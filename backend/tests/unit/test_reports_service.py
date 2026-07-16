import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.reports import ReportsService
from app.exceptions.base import BadRequestException, NotFoundException

@pytest.mark.asyncio
async def test_generate_report_dataset_not_found():
    # Arrange
    session = AsyncMock()
    service = ReportsService(session)
    
    service.dataset_repo = MagicMock()
    service.dataset_repo.get_with_versions = AsyncMock(return_value=None)
    
    # Act & Assert
    with pytest.raises(NotFoundException) as exc_info:
        await service.generate_report(dataset_id="invalid-id", report_type="PDF", user_id="user-123")
        
    assert "Dataset workspace not found" in str(exc_info.value.message)

@pytest.mark.asyncio
async def test_generate_report_invalid_format():
    # Arrange
    session = AsyncMock()
    service = ReportsService(session)
    
    mock_dataset = MagicMock(user_id="user-123")
    service.dataset_repo = MagicMock()
    service.dataset_repo.get_with_versions = AsyncMock(return_value=mock_dataset)
    
    # Act & Assert
    with pytest.raises(BadRequestException) as exc_info:
        await service.generate_report(dataset_id="dataset-123", report_type="PNG", user_id="user-123")
        
    assert "Invalid report type requested" in str(exc_info.value.message)
