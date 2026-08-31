import logging
import os
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class KeyVaultManager:
    def __init__(self):
        self.client = None
        if settings.AZURE_KEY_VAULT_URL:
            try:
                from azure.identity import DefaultAzureCredential
                from azure.keyvault.secrets import SecretClient
                credential = DefaultAzureCredential()
                self.client = SecretClient(vault_url=settings.AZURE_KEY_VAULT_URL, credential=credential)
                logger.info(f"Connected to Azure Key Vault at {settings.AZURE_KEY_VAULT_URL}")
            except Exception as e:
                logger.warning(f"Could not connect to Azure Key Vault: {e}")

    def get_secret(self, secret_name: str) -> Optional[str]:
        if self.client:
            try:
                retrieved_secret = self.client.get_secret(secret_name)
                return retrieved_secret.value
            except Exception as e:
                logger.error(f"Failed to fetch secret '{secret_name}' from Azure Key Vault: {e}")
                return None
        # In local dev mode without Key Vault, check environment or return None
        return os.getenv(f"KEYVAULT_SECRET_{secret_name.upper().replace('-', '_')}", None)

keyvault_manager = KeyVaultManager()
