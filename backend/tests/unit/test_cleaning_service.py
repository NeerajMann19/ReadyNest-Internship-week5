import pytest
import math
from unittest.mock import AsyncMock, MagicMock
from app.services.cleaning import CleaningService
from app.exceptions.base import NotFoundException

@pytest.mark.asyncio
async def test_sanitize_sample():
    # Arrange
    session = AsyncMock()
    service = CleaningService(session)
    
    test_records = [
        {"col1": "A", "col2": 1.23},
        {"col1": "B", "col2": float('nan')},
        {"col1": "C", "col2": float('inf')}
    ]
    
    # Act
    sanitized = service._sanitize_sample(test_records)
    
    # Assert
    assert sanitized[0]["col2"] == 1.23
    assert sanitized[1]["col2"] is None
    assert sanitized[2]["col2"] is None

@pytest.mark.asyncio
async def test_preview_cleaning_dataset_not_found():
    # Arrange
    session = AsyncMock()
    service = CleaningService(session)
    
    service.dataset_repo = MagicMock()
    service.dataset_repo.get_with_versions = AsyncMock(return_value=None)
    
    # Act & Assert
    with pytest.raises(NotFoundException) as exc_info:
        await service.preview_cleaning(dataset_id="invalid-id", user_id="user-123", operations=[])
        
    assert "Dataset workspace not found" in str(exc_info.value.message)
