import logging
from typing import List, Dict, Any, Optional
from kubernetes import client as k8s_client

logger = logging.getLogger(__name__)

def inspect_deployments(apps_api: Optional[k8s_client.AppsV1Api], namespace: str = "default") -> List[Dict[str, Any]]:
    if not apps_api:
        return [
            {
                "name": "payment-service",
                "namespace": namespace,
                "replicas_desired": 3,
                "replicas_ready": 2,
                "replicas_available": 2,
                "replicas_unavailable": 1,
                "strategy": "RollingUpdate",
                "conditions": [
                    {
                        "type": "Progressing",
                        "status": "True",
                        "reason": "ReplicaSetUpdated",
                        "message": "ReplicaSet \"payment-service-6789ab\" is progressing."
                    },
                    {
                        "type": "Available",
                        "status": "False",
                        "reason": "MinimumReplicasUnavailable",
                        "message": "Deployment does not have minimum availability."
                    }
                ]
            },
            {
                "name": "frontend-web",
                "namespace": namespace,
                "replicas_desired": 2,
                "replicas_ready": 2,
                "replicas_available": 2,
                "replicas_unavailable": 0,
                "strategy": "RollingUpdate",
                "conditions": [
                    {
                        "type": "Available",
                        "status": "True",
                        "reason": "MinimumReplicasAvailable",
                        "message": "Deployment has minimum availability."
                    }
                ]
            }
        ]

    try:
        deployments = apps_api.list_namespaced_deployment(namespace=namespace)
        structured_deployments = []

        for dep in deployments.items:
            conds = []
            if dep.status.conditions:
                for c in dep.status.conditions:
                    conds.append({
                        "type": c.type,
                        "status": c.status,
                        "reason": c.reason,
                        "message": c.message
                    })

            structured_deployments.append({
                "name": dep.metadata.name,
                "namespace": dep.metadata.namespace,
                "replicas_desired": dep.spec.replicas or 0,
                "replicas_ready": dep.status.ready_replicas or 0,
                "replicas_available": dep.status.available_replicas or 0,
                "replicas_unavailable": dep.status.unavailable_replicas or 0,
                "strategy": dep.spec.strategy.type if dep.spec.strategy else "Unknown",
                "conditions": conds
            })

        return structured_deployments
    except Exception as e:
        logger.error(f"Error inspecting deployments in namespace {namespace}: {e}")
        return []
