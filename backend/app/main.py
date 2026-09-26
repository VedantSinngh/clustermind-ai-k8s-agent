import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api.v1.auth import router as auth_router
from app.api.v1.clusters import router as clusters_router
from app.api.v1.investigations import router as investigations_router
from app.api.v1.remediation import router as remediation_router
from app.api.v1.health import router as health_router

from app.core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ClusterMind Backend Service Starting...")
    yield
    logger.info("ClusterMind Backend Service Shutdown.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=f"Production-grade AI Kubernetes Troubleshooting Agent backend created by {settings.DEVELOPER}.",
    lifespan=lifespan
)

# Prometheus Metrics Setup
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app)
except Exception as e:
    logger.warning(f"Prometheus instrumentator setup skipped: {e}")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health_router)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(clusters_router, prefix=settings.API_V1_STR)
app.include_router(investigations_router, prefix=settings.API_V1_STR)
app.include_router(remediation_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "message": "ClusterMind AI Kubernetes Troubleshooting Agent API Server",
        "developer": settings.DEVELOPER,
        "docs_url": "/docs",
        "health_check": "/healthz"
    }
