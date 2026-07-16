"""
EdaResult repository operations.
"""
from typing import Optional
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.eda_result import EdaResult
from app.repositories.base import BaseRepository


class EdaResultRepository(BaseRepository[EdaResult]):
    """
    EdaResultRepository handling eda_results table queries.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(EdaResult, session)

    async def get_by_version_id(self, version_id: UUID) -> Optional[EdaResult]:
        """
        Retrieves exploratory analysis results matching specific dataset version.
        """
        result = await self.session.execute(
            select(EdaResult).filter_by(dataset_version_id=version_id)
        )
        return result.scalar_one_or_none()
