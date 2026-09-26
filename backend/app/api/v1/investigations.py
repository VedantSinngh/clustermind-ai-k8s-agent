import asyncio
import logging
import uuid
from typing import List, Optional

logger = logging.getLogger(__name__)
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db, AsyncSessionLocal
from app.core.rate_limiter import rate_limiter
from app.core.keyvault import keyvault_manager
from app.models.domain import User, Cluster, Investigation, InvestigationProgress
from app.schemas.investigation import InvestigationCreate, InvestigationOut
from app.api.deps import get_current_user, verify_cluster_access
from app.services.k8s.client_manager import K8sClientManager
from app.services.k8s.evidence_aggregator import aggregate_cluster_evidence
from app.services.llm.groq_reasoner import analyze_evidence_with_groq

router = APIRouter(prefix="/investigations", tags=["Investigations"])

async def _log_step(db: AsyncSession, investigation_id: uuid.UUID, step_name: str, status_str: str = "completed"):
    p = InvestigationProgress(
        investigation_id=investigation_id,
        step=step_name,
        status=status_str
    )
    db.add(p)
    await db.commit()

async def _run_investigation_task(investigation_id: uuid.UUID, cluster_id: uuid.UUID, namespace: str):
    async with AsyncSessionLocal() as db:
        try:
            # Step 1: checking_pods & collecting cluster telemetry
            await _log_step(db, investigation_id, "checking_pods", "started")
            stmt = select(Cluster).where(Cluster.id == cluster_id)
            c_res = await db.execute(stmt)
            cluster_obj = c_res.scalars().first()

            raw_config = keyvault_manager.get_secret(cluster_obj.kubeconfig_secret_ref) if cluster_obj else None
            v1_api, apps_api = K8sClientManager.get_api_clients(raw_config)
            await _log_step(db, investigation_id, "checking_pods", "completed")

            # Step 2: reading_logs
            await _log_step(db, investigation_id, "reading_logs", "started")
            await _log_step(db, investigation_id, "reading_logs", "completed")

            # Step 3: analyzing_events & aggregating evidence via asyncio.to_thread
            await _log_step(db, investigation_id, "analyzing_events", "started")
            evidence = await asyncio.to_thread(aggregate_cluster_evidence, v1_api, apps_api, namespace)
            await _log_step(db, investigation_id, "analyzing_events", "completed")

            # Step 4: ai_reasoning via Groq
            await _log_step(db, investigation_id, "ai_reasoning", "started")
            ai_result = await analyze_evidence_with_groq(evidence)
            await _log_step(db, investigation_id, "ai_reasoning", "completed")

            # Step 5: completed
            await _log_step(db, investigation_id, "completed", "completed")

            # Update Investigation record
            inv_stmt = select(Investigation).where(Investigation.id == investigation_id)
            inv_res = await db.execute(inv_stmt)
            investigation = inv_res.scalars().first()
            if investigation:
                investigation.root_cause = ai_result.get("root_cause")
                investigation.suggested_fix = ai_result.get("suggested_fix")
                investigation.suggested_command = ai_result.get("suggested_command")
                investigation.confidence_score = ai_result.get("confidence_score")
                investigation.raw_evidence = evidence
                investigation.llm_response = ai_result
                investigation.status = "completed"
                await db.commit()

        except Exception as e:
            correlation_id = uuid.uuid4().hex[:8]
            logger.error(f"[Ref:{correlation_id}] Background investigation {investigation_id} failed: {e}", exc_info=True)
            inv_stmt = select(Investigation).where(Investigation.id == investigation_id)
            inv_res = await db.execute(inv_stmt)
            investigation = inv_res.scalars().first()
            if investigation:
                investigation.status = "failed"
                investigation.root_cause = f"Investigation execution failed. Reference ID: {correlation_id}. Please contact support."
                await db.commit()

@router.post("", response_model=InvestigationOut, status_code=status.HTTP_202_ACCEPTED)
async def create_investigation(
    inv_in: InvestigationCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Enforce rate limiting
    rate_limiter.check_rate_limit(str(current_user.id))

    # 2. Check cluster authorization
    await verify_cluster_access(current_user.id, inv_in.cluster_id, db, required_role="viewer")

    # 3. Fetch cluster name for response model
    stmt = select(Cluster).where(Cluster.id == inv_in.cluster_id)
    c_res = await db.execute(stmt)
    cluster_obj = c_res.scalars().first()
    cluster_name = cluster_obj.name if cluster_obj else "Kubernetes Cluster"

    # 4. Create initial Investigation record
    investigation = Investigation(
        user_id=current_user.id,
        cluster_id=inv_in.cluster_id,
        namespace=inv_in.namespace or "default",
        status="running"
    )
    db.add(investigation)
    await db.commit()
    await db.refresh(investigation)

    # 5. Dispatch background task to unblock HTTP request cycle
    background_tasks.add_task(
        _run_investigation_task,
        investigation.id,
        inv_in.cluster_id,
        inv_in.namespace or "default"
    )

    out = InvestigationOut.model_validate(investigation)
    out.cluster_name = cluster_name
    return out

@router.get("", response_model=List[InvestigationOut])
async def list_investigations(
    cluster_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Investigation, Cluster.name.label("cluster_name"))
        .join(Cluster, Investigation.cluster_id == Cluster.id)
        .options(selectinload(Investigation.progress_steps))
        .where(Investigation.user_id == current_user.id)
        .order_by(Investigation.created_at.desc())
    )

    if cluster_id:
        stmt = stmt.where(Investigation.cluster_id == cluster_id)
    if status_filter:
        stmt = stmt.where(Investigation.status == status_filter)

    stmt = stmt.limit(limit).offset(offset)
    res = await db.execute(stmt)
    rows = res.all()

    outs = []
    for inv_obj, c_name in rows:
        out = InvestigationOut.model_validate(inv_obj)
        out.cluster_name = c_name
        outs.append(out)

    return outs

@router.get("/{investigation_id}", response_model=InvestigationOut)
async def get_investigation(
    investigation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Investigation, Cluster.name.label("cluster_name"))
        .join(Cluster, Investigation.cluster_id == Cluster.id)
        .options(selectinload(Investigation.progress_steps))
        .where(Investigation.id == investigation_id, Investigation.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    row = res.first()

    if not row:
        raise HTTPException(status_code=404, detail="Investigation not found.")

    inv_obj, c_name = row
    out = InvestigationOut.model_validate(inv_obj)
    out.cluster_name = c_name
    return out
