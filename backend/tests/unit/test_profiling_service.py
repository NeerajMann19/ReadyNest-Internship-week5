import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.profiling import ProfilingService
from app.exceptions.base import BadRequestException, NotFoundException

@pytest.mark.asyncio
async def test_profile_dataset_not_found():
    # Arrange
    session = AsyncMock()
    service = ProfilingService(session)
    
    # Mock dataset repo to return None (not found)
    service.dataset_repo = MagicMock()
    service.dataset_repo.get_with_versions = AsyncMock(return_value=None)
    
    # Act & Assert
    with pytest.raises(NotFoundException) as exc_info:
        await service.profile_dataset(dataset_id="invalid-id", user_id="user-123")
        
    assert "Dataset workspace not found" in str(exc_info.value.message)

@pytest.mark.asyncio
async def test_profile_dataset_no_active_version():
    # Arrange
    session = AsyncMock()
    service = ProfilingService(session)
    
    # Mock dataset exists
    mock_dataset = MagicMock(user_id="user-123")
    service.dataset_repo = MagicMock()
    service.dataset_repo.get_with_versions = AsyncMock(return_value=mock_dataset)
    
    # Mock version repo returns None (no active version)
    service.version_repo = MagicMock()
    service.version_repo.get_current_version = AsyncMock(return_value=None)
    
    # Act & Assert
    with pytest.raises(BadRequestException) as exc_info:
        await service.profile_dataset(dataset_id="dataset-123", user_id="user-123")
        
    assert "Dataset contains no active version" in str(exc_info.value.message)
