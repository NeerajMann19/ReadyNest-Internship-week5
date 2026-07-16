"""
Report repository operations.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    """
    ReportRepository handling reports table queries.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(Report, session)

    async def get_by_version_id(self, version_id: UUID) -> List[Report]:
        """
        Retrieves generated reports matching specific dataset version.
        """
        result = await self.session.execute(
            select(Report).filter_by(dataset_version_id=version_id)
        )
        return list(result.scalars().all())
