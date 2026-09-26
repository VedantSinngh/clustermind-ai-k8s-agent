from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

from app.core.config import settings
from app.core.database import get_db
from app.core.keyvault import keyvault_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])

@router.get("/healthz")
async def healthz():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "developer": settings.DEVELOPER
    }

@router.get("/livez")
async def livez():
    return {"status": "alive"}

@router.get("/healthz/ready")
async def healthz_ready(response: Response, db: AsyncSession = Depends(get_db)):
    db_ok = False
    keyvault_ok = True

    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error(f"Readiness probe DB ping failed: {e}")
        db_ok = False

    if settings.AZURE_KEY_VAULT_URL and keyvault_manager.client is None:
        keyvault_ok = False

    if not db_ok or not keyvault_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unhealthy",
            "database": "ok" if db_ok else "unreachable",
            "keyvault": "ok" if keyvault_ok else "unreachable"
        }

    return {
        "status": "ready",
        "database": "ok",
        "keyvault": "ok" if settings.AZURE_KEY_VAULT_URL else "not_configured"
    }

