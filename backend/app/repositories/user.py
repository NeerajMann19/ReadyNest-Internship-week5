"""
User repository operations.
"""
from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    UserRepository handling users table query logic.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieves a user by email.
        """
        result = await self.session.execute(select(User).filter_by(email=email))
        return result.scalar_one_or_none()
