"""
Cloud Cost Calculator - FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.utils.database import init_db
from app.utils.logger import logger
from app.config import settings

# Import v1 routers
from app.api.v1 import bom as bom_v1
from app.api.v1 import scenarios as scenarios_v1

# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-cloud cost estimation with per-provider discount modelling",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — allow frontend dev server
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(bom_v1.router)
app.include_router(scenarios_v1.router)

# ---------------------------------------------------------------------------
# Startup event
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    init_db()
    logger.info("Database initialised")

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status":      "healthy",
        "app":         settings.APP_NAME,
        "version":     settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }

@app.get("/", tags=["Health"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs":    "/docs",
        "health":  "/health",
    }
