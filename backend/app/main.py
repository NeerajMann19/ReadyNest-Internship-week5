"""
Main FastAPI application initialization.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.database import check_db_health
from app.exceptions.handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize system logging
    setup_logging()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan
)

# Configure CORS restrictions for Vite frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom exception handlers
register_exception_handlers(app)

# Include the API router v1 endpoints
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """
    Service health verification endpoint. Checks database readiness and environment context.
    """
    db_connected = await check_db_health()
    
    if db_connected:
        return {
            "success": True,
            "message": "Prism IQ backend is running",
            "data": {
                "status": "healthy",
                "database": "connected",
                "environment": settings.ENVIRONMENT,
                "version": settings.PROJECT_VERSION
            },
            "errors": []
        }
    else:
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "message": "Database connection unavailable",
                "data": {
                    "status": "degraded",
                    "database": "disconnected",
                    "environment": settings.ENVIRONMENT,
                    "version": settings.PROJECT_VERSION
                },
                "errors": ["Unable to establish database connection."]
            }
        )
