import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.keyvault import keyvault_manager
from app.models.domain import User, Investigation, Cluster, RemediationAction
from app.schemas.investigation import RemediationRequest, RemediationOut
from app.api.deps import get_current_user, verify_cluster_access
from app.services.k8s.client_manager import K8sClientManager
from app.services.k8s.remediation_executor import execute_safe_remediation

router = APIRouter(prefix="/remediations", tags=["Remediation & Human-in-the-Loop"])

@router.post("", response_model=RemediationOut, status_code=status.HTTP_201_CREATED)
async def execute_remediation(
    rem_in: RemediationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not rem_in.confirm:
        raise HTTPException(
            status_code=400,
            detail="Remediation execution requires explicit human confirmation ('confirm': true)."
        )

    # 1. Fetch investigation record
    stmt = select(Investigation).where(Investigation.id == rem_in.investigation_id)
    res = await db.execute(stmt)
    inv = res.scalars().first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation reference not found.")

    # 2. Enforce OPERATOR role permission check
    await verify_cluster_access(current_user.id, inv.cluster_id, db, required_role="operator")

    # 3. Fetch cluster & credentials
    c_stmt = select(Cluster).where(Cluster.id == inv.cluster_id)
    c_res = await db.execute(c_stmt)
    cluster = c_res.scalars().first()

    raw_config = keyvault_manager.get_secret(cluster.kubeconfig_secret_ref) if cluster else None
    v1_api, apps_api = K8sClientManager.get_api_clients(raw_config)

    # 4. Execute safe remediation action
    result_data = execute_safe_remediation(
        v1_api=v1_api,
        apps_api=apps_api,
        command=rem_in.command,
        namespace=inv.namespace or "default"
    )

    result_str = f"[{result_data.get('execution_mode')}] {result_data.get('message')}"

    # 5. Audit Log Record in remediation_actions table
    audit_action = RemediationAction(
        investigation_id=inv.id,
        approved_by=current_user.id,
        command_executed=rem_in.command,
        result=result_str
    )
    db.add(audit_action)
    await db.commit()
    await db.refresh(audit_action)

    return audit_action
