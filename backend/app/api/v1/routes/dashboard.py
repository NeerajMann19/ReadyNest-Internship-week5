"""
Dashboard API routes.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard import DashboardService

router = APIRouter()


@router.get("/summary", response_model=dict)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns unified, frontend-ready dashboard metrics, charts, timeline logs, and recent jobs.
    """
    dashboard_service = DashboardService(db)
    summary = await dashboard_service.get_dashboard_summary(user_id=current_user.id)
    return {
        "success": True,
        "message": "Dashboard summary metrics aggregated successfully",
        "data": summary,
        "errors": []
    }
