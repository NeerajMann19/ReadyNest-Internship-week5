import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.ai_insights import AiInsightsService
from app.exceptions.base import BadRequestException, NotFoundException

@pytest.mark.asyncio
async def test_get_insights_dataset_not_found():
    # Arrange
    session = AsyncMock()
    service = AiInsightsService(session)
    
    service.dataset_repo = MagicMock()
    service.dataset_repo.get = AsyncMock(return_value=None)
    service.dataset_repo.get_with_versions = AsyncMock(return_value=None)
    
    # Act & Assert
    with pytest.raises(NotFoundException) as exc_info:
        await service.get_insights(dataset_id="invalid-id", user_id="user-123")
        
    assert "Dataset workspace not found" in str(exc_info.value.message)

@pytest.mark.asyncio
async def test_generate_insights_no_profile():
    # Arrange
    session = AsyncMock()
    service = AiInsightsService(session)
    
    mock_version = MagicMock(is_current=True)
    mock_dataset = MagicMock(user_id="user-123", versions=[mock_version])
    service.dataset_repo = MagicMock()
    service.dataset_repo.get_with_versions = AsyncMock(return_value=mock_dataset)
    
    # Mock version repo returns version
    service.version_repo = MagicMock()
    service.version_repo.get_current_version = AsyncMock(return_value=mock_version)
    
    # Mock profile repo returns None (no data profile generated yet)
    service.profile_repo = MagicMock()
    service.profile_repo.get_by_version_id = AsyncMock(return_value=None)
    service.profile_repo.get_by_dataset_id = AsyncMock(return_value=None)
    
    # Act & Assert
    with pytest.raises(BadRequestException) as exc_info:
        await service.generate_insights(dataset_id="dataset-123", user_id="user-123")
        
    assert "Data Profile has not been generated yet for this dataset" in str(exc_info.value.message)
