"""
Machine Learning API route handlers.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, BackgroundTasks, status

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.ml import MLModelTrainRequest, MLModelResponse, PredictionRequest, PredictionResponse, PredictionLogResponse
from app.services.ml import MLService

router = APIRouter()


@router.post("/train", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def train_model(
    background_tasks: BackgroundTasks,
    req: MLModelTrainRequest,
    dataset_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Creates a new machine learning model workspace and registers an asynchronous background training job.
    """
    ml_service = MLService(db)
    model = await ml_service.create_training_job(
        user_id=current_user.id,
        dataset_id=dataset_id,
        target_column=req.target_column,
        features=req.features,
        problem_type=req.problem_type,
        candidate_algorithms=req.candidate_algorithms,
        cross_validation=req.cross_validation,
        random_state=req.random_state
    )
    
    # Queue background model fitting task
    background_tasks.add_task(MLService.train_model_task, model.id)

    return {
        "success": True,
        "message": "Model training task initiated asynchronously in the background.",
        "data": MLModelResponse.model_validate(model),
        "errors": []
    }


@router.get("", response_model=dict)
async def list_models(
    dataset_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lists all models belonging to the user, optionally filtered by dataset workspace.
    """
    ml_service = MLService(db)
    models = await ml_service.list_models(user_id=current_user.id, dataset_id=dataset_id)
    data_list = [MLModelResponse.model_validate(m) for m in models]
    return {
        "success": True,
        "message": "Models list fetched successfully.",
        "data": data_list,
        "errors": []
    }


@router.get("/{id}", response_model=dict)
async def get_model_details(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves execution logs, validation metrics, and configuration for a model.
    """
    ml_service = MLService(db)
    model = await ml_service.get_model_details(model_id=id, user_id=current_user.id)
    return {
        "success": True,
        "message": "Model details fetched successfully.",
        "data": MLModelResponse.model_validate(model),
        "errors": []
    }


@router.post("/{id}/predict", response_model=dict)
async def make_prediction(
    id: UUID,
    req: PredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Performs real-time row inference predictions using the trained champion model.
    """
    ml_service = MLService(db)
    prediction, confidence = await ml_service.make_prediction(
        model_id=id,
        user_id=current_user.id,
        input_data=req.input_data
    )
    return {
        "success": True,
        "message": "Prediction calculated successfully.",
        "data": PredictionResponse(prediction=prediction, confidence=confidence),
        "errors": []
    }


@router.get("/{id}/history", response_model=dict)
async def get_prediction_history(
    id: UUID,
    limit: int = Query(50, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves prediction auditing logs.
    """
    ml_service = MLService(db)
    history = await ml_service.get_prediction_history(model_id=id, user_id=current_user.id, limit=limit)
    data_list = [PredictionLogResponse.model_validate(h) for h in history]
    return {
        "success": True,
        "message": "Prediction history logs fetched successfully.",
        "data": data_list,
        "errors": []
    }


@router.delete("/{id}", response_model=dict)
async def delete_model(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes the model metadata record and its serialized binary artifact.
    """
    ml_service = MLService(db)
    await ml_service.delete_model(model_id=id, user_id=current_user.id)
    return {
        "success": True,
        "message": "ML Model and files removed successfully.",
        "data": None,
        "errors": []
    }
