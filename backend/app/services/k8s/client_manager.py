import logging
import os
import yaml
from typing import Tuple, Optional
from kubernetes import client as k8s_client, config as k8s_config
from app.core.config import settings

logger = logging.getLogger(__name__)

class K8sClientManager:
    """
    Manages connections to K8s API servers dynamically using official python client.
    Loads raw kubeconfig strings entirely in-memory without temporary files.
    """
    
    @staticmethod
    def get_api_clients(kubeconfig_raw: Optional[str] = None) -> Tuple[Optional[k8s_client.CoreV1Api], Optional[k8s_client.AppsV1Api]]:
        """
        Returns (CoreV1Api, AppsV1Api).
        Loads kubeconfig YAML in-memory via new_client_from_config_dict without writing to disk.
        """
        try:
            if kubeconfig_raw:
                config_dict = yaml.safe_load(kubeconfig_raw)
                client_instance = k8s_config.new_client_from_config_dict(config_dict)
                return k8s_client.CoreV1Api(api_client=client_instance), k8s_client.AppsV1Api(api_client=client_instance)
            elif settings.KUBECONFIG_PATH and os.path.exists(settings.KUBECONFIG_PATH):
                k8s_config.load_kube_config(config_file=settings.KUBECONFIG_PATH)
            else:
                try:
                    k8s_config.load_incluster_config()
                except Exception:
                    try:
                        k8s_config.load_kube_config()
                    except Exception:
                        logger.warning("No valid K8s cluster configuration found. Inspector using synthetic telemetry.")
                        return None, None
            
            return k8s_client.CoreV1Api(), k8s_client.AppsV1Api()
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            return None, None
