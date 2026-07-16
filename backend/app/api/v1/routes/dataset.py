"""
Dataset API routes.
"""
import os
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.dataset import DatasetResponse, DatasetDetailResponse, DatasetVersionResponse
from app.schemas.data_profile import DataProfileResponse
from app.schemas.cleaning import CleanRequest, CleanPreviewResponse
from app.schemas.eda import EdaResultResponse
from app.schemas.ai_insights import AiInsightResponse, AiInsightSummaryResponse
from app.schemas.report import DatasetCompareResponse, BulkDeleteRequest, BulkDeleteResponse
from app.services.dataset import DatasetService
from app.services.profiling import ProfilingService
from app.services.cleaning import CleaningService
from app.services.eda import EdaService
from app.services.ai_insights import AiInsightsService
from app.services.reports import ReportsService
from app.repositories.eda_result import EdaResultRepository
from app.repositories.ai_insight import AiInsightRepository
from app.exceptions.base import BadRequestException


router = APIRouter()


@router.post("")
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_name: str = Form(...),
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ingests and validates a multipart dataset upload.
    """
    dataset_service = DatasetService(db)
    dataset, version = await dataset_service.import_dataset(
        user_id=current_user.id,
        upload_file=file,
        dataset_name=dataset_name,
        description=description
    )
    
    version_res = DatasetVersionResponse.model_validate(version)
    dataset_res = DatasetDetailResponse(
        id=dataset.id,
        user_id=dataset.user_id,
        dataset_name=dataset.dataset_name,
        original_filename=dataset.original_filename,
        description=dataset.description,
        source_type=dataset.source_type,
        created_at=dataset.created_at,
        versions=[version_res],
        profile=None
    )
    
    return {
        "success": True,
        "message": "Dataset uploaded and parsed successfully",
        "data": dataset_res,
        "errors": []
    }


@router.get("")
async def list_datasets(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    status: Optional[str] = None,
    sort: Optional[str] = None,
    created_before: Optional[datetime] = None,
    created_after: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lists all owned datasets for the authenticated user session with paginated filters.
    """
    skip = (page - 1) * page_size
    limit = page_size
    
    dataset_service = DatasetService(db)
    datasets = await dataset_service.list_datasets(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        sort=sort,
        created_before=created_before,
        created_after=created_after
    )
    
    data_list = [DatasetResponse.model_validate(d) for d in datasets]
    
    return {
        "success": True,
        "message": "Datasets list fetched successfully",
        "data": data_list,
        "errors": []
    }



@router.get("/{id}")
async def get_dataset_detail(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetches comprehensive details of a user owned dataset, including all versions.
    """
    dataset_service = DatasetService(db)
    dataset = await dataset_service.get_dataset(dataset_id=id, user_id=current_user.id)
    
    return {
        "success": True,
        "message": "Dataset details fetched successfully",
        "data": DatasetDetailResponse.model_validate(dataset),
        "errors": []
    }


@router.get("/{id}/download")
async def download_dataset(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Downloads the active version of the dataset file.
    """
    dataset_service = DatasetService(db)
    filepath = await dataset_service.get_dataset_file_path(dataset_id=id, user_id=current_user.id)
    filename = os.path.basename(filepath)
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream"
    )


@router.get("/{id}/preview")
async def get_dataset_preview(
    id: UUID,
    page: int = 1,
    page_size: int = 20,
    sort: Optional[str] = None,
    filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns paginated preview of active version including head(100), tail(100), sorting, and filtering.
    """
    dataset_service = DatasetService(db)
    preview = await dataset_service.preview_dataset_records(
        dataset_id=id,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        sort=sort,
        filter=filter
    )
    return {
        "success": True,
        "message": "Dataset preview loaded successfully",
        "data": preview,
        "errors": []
    }


@router.post("/{id}/profile")
async def trigger_profiling(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generates or overwrites data profiling metrics for the target dataset.
    """
    profiling_service = ProfilingService(db)
    profile = await profiling_service.profile_dataset(dataset_id=id, user_id=current_user.id)
    
    return {
        "success": True,
        "message": "Dataset profiled successfully",
        "data": DataProfileResponse.model_validate(profile),
        "errors": []
    }


@router.get("/{id}/profile")
async def get_dataset_profile(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the existing generated profile metrics for the target dataset.
    """
    profiling_service = ProfilingService(db)
    profile = await profiling_service.get_profile(dataset_id=id, user_id=current_user.id)
    
    return {
        "success": True,
        "message": "Dataset profile fetched successfully",
        "data": DataProfileResponse.model_validate(profile),
        "errors": []
    }


@router.post("/{id}/clean/preview")
async def trigger_clean_preview(
    id: UUID,
    request: CleanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Simulates dataset cleaning sequence in-memory and returns preview statistics comparisons.
    """
    cleaning_service = CleaningService(db)
    operations_dict = [op.model_dump() for op in request.operations]
    preview_data = await cleaning_service.preview_cleaning(
        dataset_id=id,
        user_id=current_user.id,
        operations=operations_dict
    )
    
    return {
        "success": True,
        "message": "Dataset cleaning preview generated successfully",
        "data": preview_data,
        "errors": []
    }


@router.post("/{id}/clean")
async def trigger_clean_apply(
    id: UUID,
    request: CleanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Applies cleaning rules sequence, creates version 2 on disk, logs lineage, and auto-profiles.
    """
    cleaning_service = CleaningService(db)
    operations_dict = [op.model_dump() for op in request.operations]
    dataset = await cleaning_service.apply_cleaning(
        dataset_id=id,
        user_id=current_user.id,
        operations=operations_dict
    )
    
    return {
        "success": True,
        "message": "Dataset cleaned successfully",
        "data": DatasetDetailResponse.model_validate(dataset),
        "errors": []
    }


@router.post("/{id}/eda")
async def trigger_eda(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Computes exploratory data analysis (EDA) for the dataset version.
    """
    eda_service = EdaService(db)
    eda = await eda_service.run_eda(dataset_id=id, user_id=current_user.id)
    return {
        "success": True,
        "message": "EDA computation completed successfully",
        "data": EdaResultResponse.model_validate(eda),
        "errors": []
    }


@router.get("/{id}/eda")
async def get_eda(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves stored exploratory data analysis (EDA) results for the dataset version.
    """
    eda_service = EdaService(db)
    eda = await eda_service.get_eda(dataset_id=id, user_id=current_user.id)
    return {
        "success": True,
        "message": "EDA results retrieved successfully",
        "data": EdaResultResponse.model_validate(eda),
        "errors": []
    }


@router.delete("/{id}/eda")
async def delete_eda(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes exploratory data analysis (EDA) results for the dataset version.
    """
    dataset_service = DatasetService(db)
    dataset = await dataset_service.get_dataset(dataset_id=id, user_id=current_user.id)
    version = next((v for v in dataset.versions if v.is_current), None)
    if not version:
        raise BadRequestException("Dataset contains no active version")
        
    eda_repo = EdaResultRepository(db)
    existing_eda = await eda_repo.get_by_version_id(version.id)
    if existing_eda:
        await eda_repo.delete(existing_eda.id)
        await db.flush()
        
    return {
        "success": True,
        "message": "EDA results deleted successfully",
        "data": None,
        "errors": []
    }


@router.post("/{id}/insights")
async def trigger_insights(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Triggers rule-based AI Insights engine to generate descriptive findings and cleaning recomendations.
    """
    insights_service = AiInsightsService(db)
    insight = await insights_service.generate_insights(dataset_id=id, user_id=current_user.id)
    return {
        "success": True,
        "message": "AI Insights generated successfully",
        "data": AiInsightResponse.model_validate(insight),
        "errors": []
    }


@router.get("/{id}/insights")
async def get_insights(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves complete stored AI Insights results matching the active dataset version.
    """
    insights_service = AiInsightsService(db)
    insight = await insights_service.get_insights(dataset_id=id, user_id=current_user.id)
    return {
        "success": True,
        "message": "AI Insights retrieved successfully",
        "data": AiInsightResponse.model_validate(insight),
        "errors": []
    }


@router.get("/{id}/insights/summary")
async def get_insights_summary(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves lightweight executive health summary metadata (ideal for fast dashboard loading).
    """
    insights_service = AiInsightsService(db)
    summary = await insights_service.get_insights_summary(dataset_id=id, user_id=current_user.id)
    return {
        "success": True,
        "message": "AI Insights Health Summary retrieved successfully",
        "data": summary,
        "errors": []
    }


@router.delete("/{id}/insights")
async def delete_insights(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes generated AI Insights results matching the active dataset version.
    """
    dataset_service = DatasetService(db)
    dataset = await dataset_service.get_dataset(dataset_id=id, user_id=current_user.id)
    version = next((v for v in dataset.versions if v.is_current), None)
    if not version:
        raise BadRequestException("Dataset contains no active version")
        
    insights_repo = AiInsightRepository(db)
    existing_insights = await insights_repo.get_by_version_id(version.id)
    if existing_insights:
        await insights_repo.delete(existing_insights.id)
        await db.flush()
        
    return {
        "success": True,
        "message": "AI Insights deleted successfully",
        "data": None,
        "errors": []
    }


@router.post("/bulk-delete", response_model=dict)
async def bulk_delete_datasets(
    request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes multiple dataset workspaces and their associated physical version files.
    """
    dataset_service = DatasetService(db)
    result = await dataset_service.bulk_delete_datasets(ids=request.ids, user_id=current_user.id)
    return {
        "success": True,
        "message": "Bulk deletion completed",
        "data": BulkDeleteResponse.model_validate(result),
        "errors": []
    }


@router.get("/{id}/compare", response_model=dict)
async def compare_dataset_versions(
    id: UUID,
    v1: int = Query(...),
    v2: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generates side-by-side comparison stats (shape differences, column/type changes, cleaning applied) between two version indices.
    """
    reports_service = ReportsService(db)
    comparison = await reports_service.get_comparison_summary(
        dataset_id=id,
        v1_num=v1,
        v2_num=v2,
        user_id=current_user.id
    )
    return {
        "success": True,
        "message": "Versions comparison calculated successfully",
        "data": DatasetCompareResponse.model_validate(comparison),
        "errors": []
    }

