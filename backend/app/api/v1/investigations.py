import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
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

@router.post("", response_model=InvestigationOut, status_code=201)
async def create_investigation(
    inv_in: InvestigationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Enforce rate limiting
    rate_limiter.check_rate_limit(str(current_user.id))

    # 2. Check cluster authorization
    await verify_cluster_access(current_user.id, inv_in.cluster_id, db, required_role="viewer")

    # 3. Create initial Investigation record
    investigation = Investigation(
        user_id=current_user.id,
        cluster_id=inv_in.cluster_id,
        namespace=inv_in.namespace or "default",
        status="running"
    )
    db.add(investigation)
    await db.commit()
    await db.refresh(investigation)

    inv_id = investigation.id

    try:
        # Step 1: checking_pods & collecting cluster telemetry
        await _log_step(db, inv_id, "checking_pods", "started")
        stmt = select(Cluster).where(Cluster.id == inv_in.cluster_id)
        c_res = await db.execute(stmt)
        cluster_obj = c_res.scalars().first()
        cluster_name = cluster_obj.name if cluster_obj else "Kubernetes Cluster"

        raw_config = keyvault_manager.get_secret(cluster_obj.kubeconfig_secret_ref) if cluster_obj else None
        v1_api, apps_api = K8sClientManager.get_api_clients(raw_config)
        await _log_step(db, inv_id, "checking_pods", "completed")

        # Step 2: reading_logs
        await _log_step(db, inv_id, "reading_logs", "started")
        await _log_step(db, inv_id, "reading_logs", "completed")

        # Step 3: analyzing_events & aggregating evidence
        await _log_step(db, inv_id, "analyzing_events", "started")
        evidence = aggregate_cluster_evidence(v1_api, apps_api, namespace=inv_in.namespace or "default")
        await _log_step(db, inv_id, "analyzing_events", "completed")

        # Step 4: ai_reasoning via Groq
        await _log_step(db, inv_id, "ai_reasoning", "started")
        ai_result = await analyze_evidence_with_groq(evidence)
        await _log_step(db, inv_id, "ai_reasoning", "completed")

        # Step 5: completed
        await _log_step(db, inv_id, "completed", "completed")

        # Update Investigation record
        investigation.root_cause = ai_result.get("root_cause")
        investigation.suggested_fix = ai_result.get("suggested_fix")
        investigation.suggested_command = ai_result.get("suggested_command")
        investigation.confidence_score = ai_result.get("confidence_score")
        investigation.raw_evidence = evidence
        investigation.llm_response = ai_result
        investigation.status = "completed"

        await db.commit()
        await db.refresh(investigation)

        # Re-fetch with progress steps
        stmt = select(Investigation).options(selectinload(Investigation.progress_steps)).where(Investigation.id == inv_id)
        res = await db.execute(stmt)
        updated_inv = res.scalars().first()

        out = InvestigationOut.model_validate(updated_inv)
        out.cluster_name = cluster_name
        return out

    except Exception as e:
        investigation.status = "failed"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Investigation execution failed: {str(e)}")

@router.get("", response_model=List[InvestigationOut])
async def list_investigations(
    cluster_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[str] = Query(None),
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
