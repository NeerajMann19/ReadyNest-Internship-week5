"""
AiInsight repository operations.
"""
from typing import Optional
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_insight import AiInsight
from app.repositories.base import BaseRepository


class AiInsightRepository(BaseRepository[AiInsight]):
    """
    AiInsightRepository handling ai_insights table queries.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(AiInsight, session)

    async def get_by_version_id(self, version_id: UUID) -> Optional[AiInsight]:
        """
        Retrieves generated insights matching specific dataset version.
        """
        result = await self.session.execute(
            select(AiInsight).filter_by(dataset_version_id=version_id)
        )
        return result.scalar_one_or_none()
