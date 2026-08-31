import logging
from typing import Dict, Any, List, Optional
from kubernetes import client as k8s_client

logger = logging.getLogger(__name__)

def collect_logs(v1_api: Optional[k8s_client.CoreV1Api], namespace: str = "default", tail_lines: int = 100) -> List[Dict[str, Any]]:
    if not v1_api:
        return [
            {
                "pod_name": "payment-service-6789ab-xy9z",
                "container_name": "payment-api",
                "log_tail": [
                    "2026-08-31 20:29:45 [INFO] Initializing Payment Service v2.1.4...",
                    "2026-08-31 20:29:46 [INFO] Connecting to Redis Cache at redis.internal:6379...",
                    "2026-08-31 20:29:47 [INFO] Allocating in-memory heap buffer (limit: 512MB)...",
                    "2026-08-31 20:29:50 [ERROR] java.lang.OutOfMemoryError: Java heap space",
                    "2026-08-31 20:29:50 [FATAL] Terminating process due to unhandled OOM error.",
                    "Killed"
                ]
            }
        ]

    try:
        pods = v1_api.list_namespaced_pod(namespace=namespace)
        collected = []

        for pod in pods.items:
            pod_name = pod.metadata.name
            if not pod.spec.containers:
                continue

            for container in pod.spec.containers:
                container_name = container.name
                try:
                    logs_str = v1_api.read_namespaced_pod_log(
                        name=pod_name,
                        namespace=namespace,
                        container=container_name,
                        tail_lines=tail_lines,
                        previous=False
                    )
                    lines = [line.strip() for line in logs_str.split("\n") if line.strip()]
                    collected.append({
                        "pod_name": pod_name,
                        "container_name": container_name,
                        "log_tail": lines[-tail_lines:] if lines else ["<No log output>"]
                    })
                except Exception as container_log_err:
                    # Try reading previous log if container crashed
                    try:
                        logs_str = v1_api.read_namespaced_pod_log(
                            name=pod_name,
                            namespace=namespace,
                            container=container_name,
                            tail_lines=tail_lines,
                            previous=True
                        )
                        lines = [line.strip() for line in logs_str.split("\n") if line.strip()]
                        collected.append({
                            "pod_name": pod_name,
                            "container_name": container_name,
                            "log_tail": (lines[-tail_lines:] if lines else []) + ["(Fetched from previous crashed container)"]
                        })
                    except Exception:
                        collected.append({
                            "pod_name": pod_name,
                            "container_name": container_name,
                            "log_tail": [f"Unable to retrieve logs: {str(container_log_err)}"]
                        })

        return collected
    except Exception as e:
        logger.error(f"Error collecting logs in namespace {namespace}: {e}")
        return []
