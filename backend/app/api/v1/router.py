"""
FastAPI v1 routing configuration.
"""
from fastapi import APIRouter
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.dataset import router as dataset_router
from app.api.v1.routes.dashboard import router as dashboard_router
from app.api.v1.routes.report import router as report_router
from app.api.v1.routes.ml import router as ml_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(dataset_router, prefix="/datasets", tags=["datasets"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(report_router, prefix="/reports", tags=["reports"])
api_router.include_router(ml_router, prefix="/ml", tags=["ml"])

