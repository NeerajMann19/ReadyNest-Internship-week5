"""
Pydantic validation schemas for authentication and user management.
"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="User password (min 8 chars)")


class UserLogin(BaseModel):
    """Schema for user login JSON payload."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user resource representation."""
    id: UUID
    email: EmailStr
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenData(BaseModel):
    """Schema representing active session token data."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefreshRequest(BaseModel):
    """Schema for refresh token request payload."""
    refresh_token: str
