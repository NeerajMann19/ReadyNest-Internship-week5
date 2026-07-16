"""
Dataset repository operations.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.repositories.base import BaseRepository


class DatasetRepository(BaseRepository[Dataset]):
    """
    DatasetRepository handling datasets table query logic.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(Dataset, session)

    async def get_multi_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Dataset]:
        """
        Retrieves datasets owned by a specific user with pagination offsets.
        """
        result = await self.session.execute(
            select(Dataset)
            .filter_by(user_id=user_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_with_versions(self, id: UUID) -> Optional[Dataset]:
        """
        Retrieves a dataset by ID and eagerly loads its versions and profile list.
        """
        result = await self.session.execute(
            select(Dataset)
            .filter_by(id=id)
            .options(
                selectinload(Dataset.versions),
                selectinload(Dataset.profile),
                selectinload(Dataset.cleaning_jobs)
            )
        )
        return result.scalar_one_or_none()

