"""
PredictionLog repository operations.
"""
from typing import List
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction_log import PredictionLog
from app.repositories.base import BaseRepository


class PredictionLogRepository(BaseRepository[PredictionLog]):
    """
    PredictionLogRepository handling database operations for prediction histories.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(PredictionLog, session)

    async def get_by_model(self, model_id: UUID, limit: int = 100) -> List[PredictionLog]:
        """
        Retrieves prediction history for a model.
        """
        result = await self.session.execute(
            select(PredictionLog)
            .filter_by(model_id=model_id)
            .order_by(PredictionLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
