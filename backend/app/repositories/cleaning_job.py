"""
CleaningJob repository operations.
"""
from typing import List
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cleaning_job import CleaningJob
from app.repositories.base import BaseRepository


class CleaningJobRepository(BaseRepository[CleaningJob]):
    """
    CleaningJobRepository handling cleaning_jobs table queries.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(CleaningJob, session)

    async def get_by_dataset_id(self, dataset_id: UUID) -> List[CleaningJob]:
        """
        Retrieves all cleaning jobs run for a specific dataset workspace.
        """
        result = await self.session.execute(
            select(CleaningJob)
            .filter_by(dataset_id=dataset_id)
            .order_by(CleaningJob.created_at.desc())
        )
        return list(result.scalars().all())
