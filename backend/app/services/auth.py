"""
Authentication service logic.
"""
from datetime import timedelta
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_jwt_token, decode_jwt_token
from app.exceptions.base import BadRequestException
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import UserRegister, TokenData

logger = logging.getLogger(__name__)


class AuthService:
    """
    Service orchestration for registration, login, and session refresh.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def register_user(self, schema: UserRegister) -> User:
        """
        Creates a new user account if the email is unique.
        """
        existing_user = await self.user_repo.get_by_email(schema.email)
        if existing_user:
            raise BadRequestException(message="Email is already registered")

        hashed_password = get_password_hash(schema.password)
        new_user = User(
            email=schema.email,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False
        )
        return await self.user_repo.create(new_user)

    async def authenticate_user(self, email: str, password: str) -> TokenData:
        """
        Authenticates credentials and returns a TokenData session schema.
        """
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise BadRequestException(message="Incorrect email or password")

        if not user.is_active:
            raise BadRequestException(message="User account is inactive")

        return self._generate_token_data(str(user.id))

    async def refresh_tokens(self, refresh_token: str) -> TokenData:
        """
        Decodes the refresh token and generates a new pair of access and refresh tokens.
        """
        payload = decode_jwt_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise BadRequestException(message="Invalid or expired refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise BadRequestException(message="Invalid token claims")

        user = await self.user_repo.get(user_id)
        if not user or not user.is_active:
            raise BadRequestException(message="User is inactive or does not exist")

        return self._generate_token_data(str(user.id))

    def _generate_token_data(self, user_id: str) -> TokenData:
        """
        Internal helper to generate standard TokenData response.
        """
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        access_token = create_jwt_token(
            subject=user_id,
            token_type="access",
            expires_delta=access_token_expires
        )
        refresh_token = create_jwt_token(
            subject=user_id,
            token_type="refresh",
            expires_delta=refresh_token_expires
        )

        return TokenData(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds())
        )
