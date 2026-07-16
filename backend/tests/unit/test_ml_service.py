"""
Unit tests for Machine Learning preprocessing detectors and service handlers.
"""
import pytest
import pandas as pd
from unittest.mock import AsyncMock, MagicMock
from app.exceptions.base import BadRequestException, NotFoundException
from app.services.ml import MLService
from app.ml.preprocessing.detector import detect_problem_type


def test_detect_problem_type():
    # 1. Classification detection
    series_cat = pd.Series(["yes", "no", "yes", "yes"])
    assert detect_problem_type(series_cat) == "classification"

    series_low_card = pd.Series([1, 0, 1, 1, 0])
    assert detect_problem_type(series_low_card) == "classification"

    # 2. Regression detection
    series_num = pd.Series([10.5, 20.3, 11.2, 45.1, 80.9, 12.0, 34.5, 56.1, 78.2, 90.0, 100.2, 120.3])
    assert detect_problem_type(series_num) == "regression"


@pytest.mark.asyncio
async def test_create_training_job_dataset_not_found():
    # Arrange
    session = AsyncMock()
    service = MLService(session)

    service.dataset_repo = MagicMock()
    service.dataset_repo.get_with_versions = AsyncMock(return_value=None)

    # Act & Assert
    with pytest.raises(NotFoundException) as exc_info:
        await service.create_training_job(
            user_id="user-123",
            dataset_id="invalid-id",
            target_column="churn"
        )
    assert "Dataset workspace not found" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_make_prediction_uncompleted_status():
    # Arrange
    session = AsyncMock()
    service = MLService(session)

    # Mock model
    mock_model = MagicMock(status="TRAINING")
    service.get_model_details = AsyncMock(return_value=mock_model)

    # Act & Assert
    with pytest.raises(BadRequestException) as exc_info:
        await service.make_prediction(
            model_id="model-123",
            user_id="user-123",
            input_data={"feature1": 1}
        )
    assert "Cannot run predictions. Model status is TRAINING" in str(exc_info.value.message)
