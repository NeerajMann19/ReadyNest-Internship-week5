import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.eda import EdaService
from app.exceptions.base import NotFoundException

@pytest.mark.asyncio
async def test_get_eda_dataset_not_found():
    # Arrange
    session = AsyncMock()
    service = EdaService(session)
    
    service.dataset_repo = MagicMock()
    service.dataset_repo.get = AsyncMock(return_value=None)
    service.dataset_repo.get_with_versions = AsyncMock(return_value=None)
    
    # Act & Assert
    with pytest.raises(NotFoundException) as exc_info:
        await service.get_eda(dataset_id="invalid-id", user_id="user-123")
        
    assert "Dataset workspace not found" in str(exc_info.value.message)
