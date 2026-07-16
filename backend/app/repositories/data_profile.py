"""
DataProfile repository operations.
"""
from typing import Optional
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_profile import DataProfile
from app.repositories.base import BaseRepository


class DataProfileRepository(BaseRepository[DataProfile]):
    """
    DataProfileRepository handling data_profiles table queries.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(DataProfile, session)

    async def get_by_dataset_id(self, dataset_id: UUID) -> Optional[DataProfile]:
        """
        Retrieves profile associated with a specific dataset.
        """
        result = await self.session.execute(
            select(DataProfile).filter_by(dataset_id=dataset_id)
        )
        return result.scalar_one_or_none()
