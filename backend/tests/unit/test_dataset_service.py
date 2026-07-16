import pytest
import math
from unittest.mock import AsyncMock, MagicMock
from app.services.dataset import DatasetService
from app.exceptions.base import BadRequestException

@pytest.mark.asyncio
async def test_sanitize_floats():
    # Arrange
    session = AsyncMock()
    service = DatasetService(session)
    
    test_dict = {
        "float_val": 3.14,
        "nan_val": float('nan'),
        "inf_val": float('inf'),
        "list_val": [1.0, float('nan'), 2.5]
    }
    
    # Act
    sanitized = service._sanitize_floats(test_dict)
    
    # Assert
    assert sanitized["float_val"] == 3.14
    assert sanitized["nan_val"] is None
    assert sanitized["inf_val"] is None
    assert sanitized["list_val"] == [1.0, None, 2.5]

@pytest.mark.asyncio
async def test_import_invalid_extension():
    # Arrange
    session = AsyncMock()
    service = DatasetService(session)
    
    mock_file = MagicMock()
    mock_file.filename = "unsupported_image.png"
    
    # Act & Assert
    with pytest.raises(BadRequestException) as exc_info:
        await service.import_dataset(
            user_id="user-123",
            upload_file=mock_file,
            dataset_name="Test Invalid Dataset"
        )
        
    assert "Unsupported file extension" in str(exc_info.value.message)
