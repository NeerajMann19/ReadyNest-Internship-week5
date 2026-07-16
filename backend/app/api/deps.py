"""
FastAPI dependency injection utilities.
"""
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_jwt_token
from app.db.session import get_db
from app.exceptions.base import PrismIQException
from app.models.user import User
from app.repositories.user import UserRepository

# OAuth2 bearer token routing helper. Maps to login endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Decodes client access token and resolves the authenticated User entity.
    """
    credentials_exception = PrismIQException(
        message="Could not validate credentials",
        status_code=401,
        errors=["Invalid authorization token"]
    )
    
    payload = decode_jwt_token(token)
    if not payload or payload.get("type") != "access":
        raise credentials_exception
        
    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception
        
    user_repo = UserRepository(db)
    user = await user_repo.get(user_id)
    if not user:
        raise credentials_exception
        
    if not user.is_active:
        raise PrismIQException(
            message="User account is inactive",
            status_code=401,
            errors=["Inactive account status"]
        )
        
    return user
