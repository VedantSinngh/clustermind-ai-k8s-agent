from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ClusterMind AI Kubernetes Troubleshooting Agent"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEVELOPER: str = "Vedant Singh"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./clustermind.db"

    # Security & Auth
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Groq LLM Settings
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_FALLBACK_MODEL: str = "llama-3.1-8b-instant"
    GROQ_TIMEOUT_SECONDS: float = 15.0

    # Azure Key Vault
    AZURE_KEY_VAULT_URL: Optional[str] = None

    # Kubernetes Default Local Dev Config
    KUBECONFIG_PATH: Optional[str] = None

    # Rate Limiting & Cache
    RATE_LIMIT_INVESTIGATIONS_PER_HOUR: int = 20
    REDIS_URL: str = "redis://redis:6379/0"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "https://*.vercel.app", "http://localhost:8000"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
