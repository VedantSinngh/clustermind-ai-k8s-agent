import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.keyvault import keyvault_manager
from app.models.domain import User, Cluster, UserClusterAccess
from app.schemas.cluster import ClusterOut, ClusterCreate
from app.api.deps import get_current_user, verify_cluster_access
from app.services.k8s.client_manager import K8sClientManager
from app.services.k8s.pod_inspector import inspect_pods
from app.services.k8s.logs_collector import collect_logs
from app.services.k8s.event_analyzer import analyze_events
from app.services.k8s.deployment_inspector import inspect_deployments
from app.services.k8s.network_inspector import inspect_network
from app.services.k8s.evidence_aggregator import aggregate_cluster_evidence

router = APIRouter(prefix="/clusters", tags=["Clusters & Telemetry"])

@router.get("", response_model=List[ClusterOut])
async def list_clusters(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Cluster, UserClusterAccess.role)
        .join(UserClusterAccess, Cluster.id == UserClusterAccess.cluster_id)
        .where(UserClusterAccess.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    rows = result.all()

    # Seed default clusters if user has none yet (for seamless demo)
    if not rows:
        c1 = Cluster(name="Production AKS Cluster (East US)", kubeconfig_secret_ref="aks-prod-kubeconfig", org_id=uuid.uuid4())
        c2 = Cluster(name="Staging EKS Cluster (US West)", kubeconfig_secret_ref="eks-staging-kubeconfig", org_id=uuid.uuid4())
        db.add_all([c1, c2])
        await db.commit()
        await db.refresh(c1)
        await db.refresh(c2)

        a1 = UserClusterAccess(user_id=current_user.id, cluster_id=c1.id, role="operator")
        a2 = UserClusterAccess(user_id=current_user.id, cluster_id=c2.id, role="viewer")
        db.add_all([a1, a2])
        await db.commit()

        # Re-fetch
        result = await db.execute(stmt)
        rows = result.all()

    cluster_outs = []
    for cluster_obj, role_str in rows:
        out = ClusterOut.model_validate(cluster_obj)
        out.role = role_str
        cluster_outs.append(out)

    return cluster_outs

@router.post("", response_model=ClusterOut, status_code=201)
async def create_cluster(
    cluster_in: ClusterCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    org = cluster_in.org_id or uuid.uuid4()
    new_cluster = Cluster(
        name=cluster_in.name,
        kubeconfig_secret_ref=cluster_in.kubeconfig_secret_ref,
        org_id=org
    )
    db.add(new_cluster)
    await db.commit()
    await db.refresh(new_cluster)

    # Grant operator access to creator
    access = UserClusterAccess(user_id=current_user.id, cluster_id=new_cluster.id, role="operator")
    db.add(access)
    await db.commit()

    out = ClusterOut.model_validate(new_cluster)
    out.role = "operator"
    return out

async def _get_k8s_clients_for_cluster(cluster_id: uuid.UUID, db: AsyncSession):
    stmt = select(Cluster).where(Cluster.id == cluster_id)
    res = await db.execute(stmt)
    cluster = res.scalars().first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found.")

    raw_config = keyvault_manager.get_secret(cluster.kubeconfig_secret_ref)
    return K8sClientManager.get_api_clients(raw_config)

@router.get("/{cluster_id}/pods")
async def get_pods(
    cluster_id: uuid.UUID,
    namespace: str = Query("default"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await verify_cluster_access(current_user.id, cluster_id, db, required_role="viewer")
    v1_api, _ = await _get_k8s_clients_for_cluster(cluster_id, db)
    return inspect_pods(v1_api, namespace)

@router.get("/{cluster_id}/logs")
async def get_logs(
    cluster_id: uuid.UUID,
    namespace: str = Query("default"),
    tail_lines: int = Query(100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await verify_cluster_access(current_user.id, cluster_id, db, required_role="viewer")
    v1_api, _ = await _get_k8s_clients_for_cluster(cluster_id, db)
    return collect_logs(v1_api, namespace, tail_lines)

@router.get("/{cluster_id}/events")
async def get_events(
    cluster_id: uuid.UUID,
    namespace: str = Query("default"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await verify_cluster_access(current_user.id, cluster_id, db, required_role="viewer")
    v1_api, _ = await _get_k8s_clients_for_cluster(cluster_id, db)
    return analyze_events(v1_api, namespace)

@router.get("/{cluster_id}/deployments")
async def get_deployments(
    cluster_id: uuid.UUID,
    namespace: str = Query("default"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await verify_cluster_access(current_user.id, cluster_id, db, required_role="viewer")
    _, apps_api = await _get_k8s_clients_for_cluster(cluster_id, db)
    return inspect_deployments(apps_api, namespace)

@router.get("/{cluster_id}/network")
async def get_network(
    cluster_id: uuid.UUID,
    namespace: str = Query("default"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await verify_cluster_access(current_user.id, cluster_id, db, required_role="viewer")
    v1_api, _ = await _get_k8s_clients_for_cluster(cluster_id, db)
    return inspect_network(v1_api, namespace)

@router.get("/{cluster_id}/investigate/evidence")
async def get_aggregated_evidence(
    cluster_id: uuid.UUID,
    namespace: str = Query("default"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await verify_cluster_access(current_user.id, cluster_id, db, required_role="viewer")
    v1_api, apps_api = await _get_k8s_clients_for_cluster(cluster_id, db)
    return aggregate_cluster_evidence(v1_api, apps_api, namespace)
