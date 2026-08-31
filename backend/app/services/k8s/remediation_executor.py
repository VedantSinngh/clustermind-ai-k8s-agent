import logging
import re
from typing import Dict, Any, Optional
from kubernetes import client as k8s_client

logger = logging.getLogger(__name__)

def execute_safe_remediation(
    v1_api: Optional[k8s_client.CoreV1Api],
    apps_api: Optional[k8s_client.AppsV1Api],
    command: str,
    namespace: str = "default"
) -> Dict[str, Any]:
    """
    Executes explicit, human-in-the-loop approved remediation commands safely via the K8s API client.
    """
    clean_cmd = command.strip()
    logger.info(f"Executing approved remediation command: {clean_cmd} in namespace: {namespace}")

    if not v1_api or not apps_api:
        # Mock execution for offline / dev demo
        return {
            "success": True,
            "command": clean_cmd,
            "message": f"Successfully simulated command execution on dev cluster: '{clean_cmd}'",
            "execution_mode": "simulation"
        }

    try:
        # 1. Restart deployment: kubectl rollout restart deployment <name>
        if "rollout restart deployment" in clean_cmd:
            match = re.search(r"deployment\s+([a-zA-Z0-9_-]+)", clean_cmd)
            if match:
                dep_name = match.group(1)
                import datetime
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
                apps_api.patch_namespaced_deployment(name=dep_name, namespace=namespace, body=patch_body)
                return {
                    "success": True,
                    "command": clean_cmd,
                    "message": f"Deployment '{dep_name}' in namespace '{namespace}' successfully restarted via rollout patch.",
                    "execution_mode": "live_k8s_api"
                }

        # 2. Delete pod: kubectl delete pod <name>
        elif "delete pod" in clean_cmd:
            match = re.search(r"pod\s+([a-zA-Z0-9_-]+)", clean_cmd)
            if match:
                pod_name = match.group(1)
                v1_api.delete_namespaced_pod(name=pod_name, namespace=namespace)
                return {
                    "success": True,
                    "command": clean_cmd,
                    "message": f"Pod '{pod_name}' in namespace '{namespace}' successfully deleted and scheduled for recreation.",
                    "execution_mode": "live_k8s_api"
                }

        # 3. Scale deployment: kubectl scale deployment <name> --replicas=<count>
        elif "scale deployment" in clean_cmd:
            dep_match = re.search(r"deployment\s+([a-zA-Z0-9_-]+)", clean_cmd)
            rep_match = re.search(r"--replicas=(\d+)", clean_cmd)
            if dep_match and rep_match:
                dep_name = dep_match.group(1)
                replicas = int(rep_match.group(1))
                patch_body = {"spec": {"replicas": replicas}}
                apps_api.patch_namespaced_deployment(name=dep_name, namespace=namespace, body=patch_body)
                return {
                    "success": True,
                    "command": clean_cmd,
                    "message": f"Deployment '{dep_name}' successfully scaled to {replicas} replicas.",
                    "execution_mode": "live_k8s_api"
                }

        return {
            "success": False,
            "command": clean_cmd,
            "message": f"Command type not recognized or restricted for security reasons. Supported commands: rollout restart deployment, delete pod, scale deployment.",
            "execution_mode": "restricted"
        }
    except Exception as e:
        logger.error(f"Error executing remediation command '{clean_cmd}': {e}")
        return {
            "success": False,
            "command": clean_cmd,
            "message": f"Execution failed: {str(e)}",
            "execution_mode": "error"
        }
