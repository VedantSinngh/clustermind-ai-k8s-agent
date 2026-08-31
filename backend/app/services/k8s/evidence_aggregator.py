import logging
from typing import Dict, Any, Optional
from kubernetes import client as k8s_client
from app.services.k8s.pod_inspector import inspect_pods
from app.services.k8s.logs_collector import collect_logs
from app.services.k8s.event_analyzer import analyze_events
from app.services.k8s.deployment_inspector import inspect_deployments
from app.services.k8s.network_inspector import inspect_network

logger = logging.getLogger(__name__)

def aggregate_cluster_evidence(
    v1_api: Optional[k8s_client.CoreV1Api],
    apps_api: Optional[k8s_client.AppsV1Api],
    namespace: str = "default"
) -> Dict[str, Any]:
    """
    Aggregates telemetry from all sub-inspectors into a unified diagnostic evidence payload.
    """
    pods = inspect_pods(v1_api, namespace)
    logs = collect_logs(v1_api, namespace)
    events = analyze_events(v1_api, namespace)
    deployments = inspect_deployments(apps_api, namespace)
    network = inspect_network(v1_api, namespace)

    # Compute summary flags
    failing_pods = [
        p for p in pods 
        if p.get("phase") != "Running" or any(not c.get("ready") or c.get("restart_count", 0) > 0 for c in p.get("containers", []))
    ]

    summary = {
        "namespace": namespace,
        "total_pods": len(pods),
        "failing_pods_count": len(failing_pods),
        "total_deployments": len(deployments),
        "warning_events_count": len(events),
        "has_network_issues": any(not s.get("has_endpoints") for s in network)
    }

    return {
        "summary": summary,
        "pods": pods,
        "logs": logs,
        "events": events,
        "deployments": deployments,
        "network": network
    }
