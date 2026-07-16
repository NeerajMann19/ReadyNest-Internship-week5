from datetime import datetime
import os
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.report import ReportResponse, ReportRequest
from app.services.reports import ReportsService
from app.exceptions.base import NotFoundException, BadRequestException
from app.core.config import settings

router = APIRouter()


@router.get("", response_model=dict)
async def list_reports(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    format: Optional[str] = Query(None),
    dataset_id: Optional[UUID] = Query(None),
    created_before: Optional[datetime] = Query(None),
    created_after: Optional[datetime] = Query(None),
    sort: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves user owned reports with pagination and complex filters.
    """
    reports_service = ReportsService(db)
    reports = await reports_service.list_reports(
        user_id=current_user.id,
        page=page,
        limit=limit,
        search=search,
        status=status,
        format=format,
        dataset_id=dataset_id,
        created_before=created_before,
        created_after=created_after,
        sort=sort
    )
    data_list = [ReportResponse.model_validate(r) for r in reports]
    return {
        "success": True,
        "message": "Reports list fetched successfully",
        "data": data_list,
        "errors": []
    }


@router.post("/generate", response_model=dict)
async def generate_report(
    dataset_id: UUID = Query(...),
    request: ReportRequest = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Registers a PENDING report job and compiles PDF, Excel, HTML, or JSON exports.
    """
    reports_service = ReportsService(db)
    report = await reports_service.generate_report(
        dataset_id=dataset_id,
        report_type=request.report_type,
        user_id=current_user.id
    )
    return {
        "success": True,
        "message": "Report generated successfully",
        "data": ReportResponse.model_validate(report),
        "errors": []
    }


@router.get("/{id}", response_model=dict)
async def get_report_details(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves status, file size, and creation times for a report.
    """
    reports_service = ReportsService(db)
    report = await reports_service.report_repo.get(id)
    if not report:
        raise NotFoundException("Report not found")
        
    # Ownership check
    dataset = await reports_service.dataset_repo.get(report.dataset_id)
    if not dataset or dataset.user_id != current_user.id:
        raise NotFoundException("Report not found")

    return {
        "success": True,
        "message": "Report details fetched successfully",
        "data": ReportResponse.model_validate(report),
        "errors": []
    }


@router.get("/{id}/download")
async def download_report(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Streams the compiled report file from local storage.
    """
    reports_service = ReportsService(db)
    report = await reports_service.report_repo.get(id)
    if not report or report.status != "COMPLETED":
        raise NotFoundException("Report not found or not compiled yet")

    # Ownership check
    dataset = await reports_service.dataset_repo.get(report.dataset_id)
    if not dataset or dataset.user_id != current_user.id:
        raise NotFoundException("Report not found")

    local_path = report.storage_path.replace("local://", "", 1)
    full_path = os.path.join(settings.STORAGE_ROOT, local_path)
    if not os.path.exists(full_path):
        raise NotFoundException("Report file does not exist on storage")

    filename = os.path.basename(full_path)
    return FileResponse(
        path=full_path,
        filename=filename,
        media_type="application/octet-stream"
    )


@router.delete("/{id}", response_model=dict)
async def delete_report(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Purges generated report file from storage and removes database log record.
    """
    reports_service = ReportsService(db)
    report = await reports_service.report_repo.get(id)
    if not report:
        raise NotFoundException("Report not found")

    # Ownership check
    dataset = await reports_service.dataset_repo.get(report.dataset_id)
    if not dataset or dataset.user_id != current_user.id:
        raise NotFoundException("Report not found")

    local_path = report.storage_path.replace("local://", "", 1)
    full_path = os.path.join(settings.STORAGE_ROOT, local_path)
    if os.path.exists(full_path):
        os.remove(full_path)

    await reports_service.report_repo.delete(report.id)
    await db.flush()

    return {
        "success": True,
        "message": "Report deleted successfully",
        "data": None,
        "errors": []
    }
