import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.auth import AuthService
from app.exceptions.base import BadRequestException
from app.models.user import User
from app.schemas.auth import UserRegister

@pytest.mark.asyncio
async def test_register_user_success():
    # Arrange
    session = AsyncMock()
    service = AuthService(session)
    
    # Mock user repository methods
    service.user_repo = MagicMock()
    service.user_repo.get_by_email = AsyncMock(return_value=None)
    
    test_user = User(email="test@test.com", hashed_password="hashed_password")
    service.user_repo.create = AsyncMock(return_value=test_user)
    
    schema = UserRegister(email="test@test.com", password="password123")
    
    # Act
    result = await service.register_user(schema)
    
    # Assert
    assert result.email == "test@test.com"
    service.user_repo.get_by_email.assert_called_once_with("test@test.com")
    service.user_repo.create.assert_called_once()

@pytest.mark.asyncio
async def test_register_user_already_exists():
    # Arrange
    session = AsyncMock()
    service = AuthService(session)
    
    service.user_repo = MagicMock()
    service.user_repo.get_by_email = AsyncMock(return_value=User(email="test@test.com"))
    
    schema = UserRegister(email="test@test.com", password="password123")
    
    # Act & Assert
    with pytest.raises(BadRequestException) as exc_info:
        await service.register_user(schema)
    
    assert "Email is already registered" in str(exc_info.value.message)

@pytest.mark.asyncio
async def test_authenticate_user_success():
    # Arrange
    session = AsyncMock()
    service = AuthService(session)
    
    service.user_repo = MagicMock()
    test_user = User(id="123", email="test@test.com", is_active=True)
    # Hashed password for "password123"
    with patch("app.services.auth.verify_password", return_value=True):
        service.user_repo.get_by_email = AsyncMock(return_value=test_user)
        
        with patch.object(service, "_generate_token_data") as mock_gen:
            mock_gen.return_value = MagicMock()
            
            # Act
            await service.authenticate_user("test@test.com", "password123")
            
            # Assert
            mock_gen.assert_called_once_with("123")

@pytest.mark.asyncio
async def test_authenticate_user_incorrect_credentials():
    # Arrange
    session = AsyncMock()
    service = AuthService(session)
    
    service.user_repo = MagicMock()
    service.user_repo.get_by_email = AsyncMock(return_value=None)
    
    # Act & Assert
    with pytest.raises(BadRequestException) as exc_info:
        await service.authenticate_user("test@test.com", "wrong_password")
        
    assert "Incorrect email or password" in str(exc_info.value.message)
