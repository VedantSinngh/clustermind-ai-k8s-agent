import logging
import os
import tempfile
from typing import Tuple, Optional
from kubernetes import client as k8s_client, config as k8s_config
from app.core.config import settings

logger = logging.getLogger(__name__)

class K8sClientManager:
    """
    Manages connections to K8s API servers dynamically using official python client.
    Supports in-memory decrypted kubeconfig strings from Key Vault, local file kubeconfigs,
    in-cluster pod credentials, or synthetic cluster telemetry for dev/offline mode.
    """
    
    @staticmethod
    def get_api_clients(kubeconfig_raw: Optional[str] = None) -> Tuple[Optional[k8s_client.CoreV1Api], Optional[k8s_client.AppsV1Api]]:
        """
        Returns (CoreV1Api, AppsV1Api).
        If kubeconfig_raw is provided, creates a temporary in-memory file for authentication and cleans it up.
        """
        try:
            if kubeconfig_raw:
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as tmp:
                    tmp.write(kubeconfig_raw)
                    tmp_path = tmp.name
                try:
                    k8s_config.load_kube_config(config_file=tmp_path)
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
            elif settings.KUBECONFIG_PATH and os.path.exists(settings.KUBECONFIG_PATH):
                k8s_config.load_kube_config(config_file=settings.KUBECONFIG_PATH)
            else:
                try:
                    k8s_config.load_incluster_config()
                except Exception:
                    try:
                        k8s_config.load_kube_config()
                    except Exception:
                        logger.warning("No valid K8s cluster configuration found. Inspector will use synthetic evidence engine for local demonstration.")
                        return None, None
            
            return k8s_client.CoreV1Api(), k8s_client.AppsV1Api()
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            return None, None
