import logging
import datetime
from typing import Dict, Any, Optional, Literal
from kubernetes import client as k8s_client

logger = logging.getLogger(__name__)

def execute_typed_remediation(
    v1_api: Optional[k8s_client.CoreV1Api],
    apps_api: Optional[k8s_client.AppsV1Api],
    action: str,
    target_resource: str,
    namespace: str = "default",
    replicas: Optional[int] = None
) -> Dict[str, Any]:
    """
    Executes explicit, typed remediation action safely via the K8s API client.
    """
    logger.info(f"Executing typed remediation action: {action} on resource: {target_resource} in namespace: {namespace}")

    if not v1_api or not apps_api:
        return {
            "success": True,
            "action": action,
            "target": target_resource,
            "message": f"Successfully simulated '{action}' on '{target_resource}' in namespace '{namespace}' (dev mode)",
            "execution_mode": "simulation"
        }

    try:
        if action == "RESTART_DEPLOYMENT":
            patch_body = {
                "spec": {
                    "template": {
                        "metadata": {
                            "annotations": {
                                "kubectl.kubernetes.io/restartedAt": datetime.datetime.utcnow().isoformat()
                            }
                        }
                    }
                }
            }
            apps_api.patch_namespaced_deployment(name=target_resource, namespace=namespace, body=patch_body)
            return {
                "success": True,
                "action": action,
                "target": target_resource,
                "message": f"Deployment '{target_resource}' in namespace '{namespace}' successfully restarted via rollout patch.",
                "execution_mode": "live_k8s_api"
            }

        elif action == "DELETE_POD":
            v1_api.delete_namespaced_pod(name=target_resource, namespace=namespace)
            return {
                "success": True,
                "action": action,
                "target": target_resource,
                "message": f"Pod '{target_resource}' in namespace '{namespace}' successfully deleted.",
                "execution_mode": "live_k8s_api"
            }

        elif action == "SCALE_DEPLOYMENT":
            rep_count = replicas if replicas is not None else 1
            patch_body = {"spec": {"replicas": rep_count}}
            apps_api.patch_namespaced_deployment(name=target_resource, namespace=namespace, body=patch_body)
            return {
                "success": True,
                "action": action,
                "target": target_resource,
                "message": f"Deployment '{target_resource}' successfully scaled to {rep_count} replicas.",
                "execution_mode": "live_k8s_api"
            }

        return {
            "success": False,
            "action": action,
            "target": target_resource,
            "message": f"Action '{action}' is not supported.",
            "execution_mode": "restricted"
        }
    except Exception as e:
        logger.error(f"Error executing remediation action '{action}' on '{target_resource}': {e}")
        return {
            "success": False,
            "action": action,
            "target": target_resource,
            "message": f"Execution failed: {str(e)}",
            "execution_mode": "error"
        }
