"""
MLModel repository operations.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ml_model import MLModel
from app.repositories.base import BaseRepository


class MLModelRepository(BaseRepository[MLModel]):
    """
    MLModelRepository handling database operations for trained models.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(MLModel, session)

    async def get_with_logs(self, model_id: UUID) -> Optional[MLModel]:
        """
        Retrieves a model by ID and eagerly loads its prediction logs list.
        """
        result = await self.session.execute(
            select(MLModel)
            .filter_by(id=model_id)
            .options(
                selectinload(MLModel.prediction_logs)
            )
        )
        return result.scalar_one_or_none()

    async def get_multi_by_dataset(self, dataset_id: UUID) -> List[MLModel]:
        """
        Retrieves all MLModels associated with a specific dataset.
        """
        result = await self.session.execute(
            select(MLModel)
            .filter_by(dataset_id=dataset_id)
            .order_by(MLModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_next_version_number(self, dataset_version_id: UUID) -> int:
        """
        Calculates the next model version number for a given dataset version.
        """
        result = await self.session.execute(
            select(MLModel)
            .filter_by(dataset_version_id=dataset_version_id)
        )
        models = result.scalars().all()
        if not models:
            return 1
        return max(m.model_version for m in models) + 1
