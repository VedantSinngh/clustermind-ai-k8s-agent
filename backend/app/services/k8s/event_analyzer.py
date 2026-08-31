import logging
from typing import List, Dict, Any, Optional
from kubernetes import client as k8s_client

logger = logging.getLogger(__name__)

def analyze_events(v1_api: Optional[k8s_client.CoreV1Api], namespace: str = "default") -> List[Dict[str, Any]]:
    if not v1_api:
        return [
            {
                "type": "Warning",
                "reason": "BackOff",
                "object": "Pod/payment-service-6789ab-xy9z",
                "message": "Back-off restarting failed container",
                "count": 14,
                "first_timestamp": "2026-08-31T20:15:00Z",
                "last_timestamp": "2026-08-31T20:30:05Z"
            },
            {
                "type": "Warning",
                "reason": "OOMKilled",
                "object": "Pod/payment-service-6789ab-xy9z",
                "message": "Memory cgroup out of memory: Killed process 14210 (java)",
                "count": 4,
                "first_timestamp": "2026-08-31T20:10:00Z",
                "last_timestamp": "2026-08-31T20:29:50Z"
            }
        ]

    try:
        events = v1_api.list_namespaced_event(namespace=namespace)
        structured_events = []

        for item in events.items:
            # Focus primarily on Warning/Error events or recent events
            if item.type in ["Warning", "Error"] or item.reason in ["Failed", "BackOff", "Unhealthy", "OOMKilled", "FailedScheduling"]:
                obj_ref = f"{item.involved_object.kind}/{item.involved_object.name}" if item.involved_object else "Unknown"
                structured_events.append({
                    "type": item.type,
                    "reason": item.reason,
                    "object": obj_ref,
                    "message": item.message,
                    "count": item.count or 1,
                    "first_timestamp": str(item.first_timestamp) if item.first_timestamp else None,
                    "last_timestamp": str(item.last_timestamp) if item.last_timestamp else None,
                })

        # Sort by count/relevance
        structured_events.sort(key=lambda x: x.get("count", 1), reverse=True)
        return structured_events
    except Exception as e:
        logger.error(f"Error fetching K8s events in namespace {namespace}: {e}")
        return []
