"""
Authentication endpoints.
"""
import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.exceptions.base import BadRequestException
from app.models.user import User
from app.schemas.auth import UserRegister, UserResponse, TokenRefreshRequest
from app.services.auth import AuthService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register")
async def register(
    schema: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Registers a new user account in the system.
    """
    auth_service = AuthService(db)
    user = await auth_service.register_user(schema)
    
    return {
        "success": True,
        "message": "User registered successfully",
        "data": UserResponse.model_validate(user),
        "errors": []
    }


@router.post("/login")
async def login(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticates a user session. Supports JSON body (email/password) and OAuth2 form urlencoded fields (username/password).
    """
    content_type = request.headers.get("content-type", "")
    email = None
    password = None

    if "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        email = form.get("username")
        password = form.get("password")
    else:
        try:
            body = await request.json()
            email = body.get("email")
            password = body.get("password")
        except Exception as e:
            logger.warning("Failed to parse JSON login body: %s", str(e))
            
    if not email or not password:
        raise BadRequestException("Missing email or password credentials")

    auth_service = AuthService(db)
    token_data = await auth_service.authenticate_user(email, password)

    return {
        "success": True,
        "message": "Login successful",
        "data": token_data,
        "errors": []
    }


@router.post("/refresh")
async def refresh_token(
    payload: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Exchanges an active refresh token for a new set of access/refresh tokens.
    """
    auth_service = AuthService(db)
    token_data = await auth_service.refresh_tokens(payload.refresh_token)

    return {
        "success": True,
        "message": "Tokens refreshed successfully",
        "data": token_data,
        "errors": []
    }


@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves profile information for the currently authenticated session.
    """
    return {
        "success": True,
        "message": "Profile fetched successfully",
        "data": UserResponse.model_validate(current_user),
        "errors": []
    }
