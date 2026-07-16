"""
DatasetVersion repository operations.
"""
from typing import Optional
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset_version import DatasetVersion
from app.repositories.base import BaseRepository


class DatasetVersionRepository(BaseRepository[DatasetVersion]):
    """
    DatasetVersionRepository handling dataset_versions queries.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(DatasetVersion, session)

    async def get_current_version(self, dataset_id: UUID) -> Optional[DatasetVersion]:
        """
        Retrieves the active/current version of a specific dataset.
        """
        result = await self.session.execute(
            select(DatasetVersion)
            .filter_by(dataset_id=dataset_id, is_current=True)
        )
        return result.scalar_one_or_none()
