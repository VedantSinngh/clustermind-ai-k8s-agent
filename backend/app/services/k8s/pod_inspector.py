import logging
from typing import List, Dict, Any, Optional
from kubernetes import client as k8s_client

logger = logging.getLogger(__name__)

def inspect_pods(v1_api: Optional[k8s_client.CoreV1Api], namespace: str = "default") -> List[Dict[str, Any]]:
    if not v1_api:
        return [
            {
                "name": "payment-service-6789ab-xy9z",
                "namespace": namespace,
                "phase": "Running",
                "pod_ip": "10.244.1.42",
                "node_name": "aks-nodepool1-vmss000001",
                "containers": [
                    {
                        "name": "payment-api",
                        "image": "myregistry.azurecr.io/payment-api:v2.1.4",
                        "ready": False,
                        "restart_count": 14,
                        "state": "waiting",
                        "reason": "CrashLoopBackOff",
                        "message": "back-off 5m0s restarting failed container=payment-api pod=payment-service-6789ab-xy9z",
                        "last_state": {
                            "exit_code": 137,
                            "reason": "OOMKilled",
                            "finished_at": "2026-08-31T20:30:00Z"
                        }
                    }
                ],
                "conditions": [
                    {"type": "Ready", "status": "False", "reason": "ContainersNotReady"}
                ]
            },
            {
                "name": "frontend-web-5432cd-ab12",
                "namespace": namespace,
                "phase": "Running",
                "pod_ip": "10.244.1.43",
                "node_name": "aks-nodepool1-vmss000001",
                "containers": [
                    {
                        "name": "nginx-frontend",
                        "image": "nginx:1.25-alpine",
                        "ready": True,
                        "restart_count": 0,
                        "state": "running",
                        "reason": None,
                        "message": None,
                        "last_state": {}
                    }
                ],
                "conditions": [
                    {"type": "Ready", "status": "True", "reason": None}
                ]
            }
        ]

    try:
        pods_list = v1_api.list_namespaced_pod(namespace=namespace)
        structured_pods = []

        for item in pods_list.items:
            container_statuses = []
            if item.status.container_statuses:
                for c in item.status.container_statuses:
                    state_info = {}
                    state_name = "unknown"
                    reason = None
                    message = None

                    if c.state.running:
                        state_name = "running"
                    elif c.state.waiting:
                        state_name = "waiting"
                        reason = c.state.waiting.reason
                        message = c.state.waiting.message
                    elif c.state.terminated:
                        state_name = "terminated"
                        reason = c.state.terminated.reason
                        message = c.state.terminated.message

                    last_state_info = {}
                    if c.last_state and c.last_state.terminated:
                        last_state_info = {
                            "exit_code": c.last_state.terminated.exit_code,
                            "reason": c.last_state.terminated.reason,
                            "finished_at": str(c.last_state.terminated.finished_at) if c.last_state.terminated.finished_at else None
                        }

                    container_statuses.append({
                        "name": c.name,
                        "image": c.image,
                        "ready": c.ready,
                        "restart_count": c.restart_count,
                        "state": state_name,
                        "reason": reason,
                        "message": message,
                        "last_state": last_state_info
                    })

            conditions = []
            if item.status.conditions:
                for cond in item.status.conditions:
                    conditions.append({
                        "type": cond.type,
                        "status": cond.status,
                        "reason": cond.reason
                    })

            structured_pods.append({
                "name": item.metadata.name,
                "namespace": item.metadata.namespace,
                "phase": item.status.phase,
                "pod_ip": item.status.pod_ip,
                "node_name": item.spec.node_name,
                "containers": container_statuses,
                "conditions": conditions
            })

        return structured_pods
    except Exception as e:
        logger.error(f"Error inspecting pods in namespace {namespace}: {e}")
        return []
