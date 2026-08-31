from fastapi import APIRouter
from app.core.config import settings

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
