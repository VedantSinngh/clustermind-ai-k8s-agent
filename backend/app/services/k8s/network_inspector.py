import logging
from typing import List, Dict, Any, Optional
from kubernetes import client as k8s_client

logger = logging.getLogger(__name__)

def inspect_network(v1_api: Optional[k8s_client.CoreV1Api], namespace: str = "default") -> List[Dict[str, Any]]:
    if not v1_api:
        return [
            {
                "name": "payment-service",
                "namespace": namespace,
                "type": "ClusterIP",
                "cluster_ip": "10.0.120.45",
                "ports": [{"port": 8080, "target_port": 8080, "protocol": "TCP"}],
                "selector": {"app": "payment-service"},
                "has_endpoints": True
            },
            {
                "name": "frontend-web",
                "namespace": namespace,
                "type": "LoadBalancer",
                "cluster_ip": "10.0.80.12",
                "ports": [{"port": 80, "target_port": 80, "protocol": "TCP"}],
                "selector": {"app": "frontend-web"},
                "has_endpoints": True
            }
        ]

    try:
        services = v1_api.list_namespaced_service(namespace=namespace)
        structured_services = []

        for svc in services.items:
            ports = []
            if svc.spec.ports:
                for p in svc.spec.ports:
                    ports.append({
                        "port": p.port,
                        "target_port": str(p.target_port),
                        "protocol": p.protocol
                    })

            # Check if matching endpoints exist
            has_endpoints = False
            try:
                ep = v1_api.read_namespaced_endpoints(name=svc.metadata.name, namespace=namespace)
                if ep and ep.subsets:
                    for s in ep.subsets:
                        if s.addresses:
                            has_endpoints = True
                            break
            except Exception:
                has_endpoints = False

            structured_services.append({
                "name": svc.metadata.name,
                "namespace": svc.metadata.namespace,
                "type": svc.spec.type,
                "cluster_ip": svc.spec.cluster_ip,
                "ports": ports,
                "selector": svc.spec.selector or {},
                "has_endpoints": has_endpoints
            })

        return structured_services
    except Exception as e:
        logger.error(f"Error inspecting network services in namespace {namespace}: {e}")
        return []
