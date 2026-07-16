"""
Generic base repository mapping.
"""
from typing import TypeVar, Type, Generic, List, Optional, Any
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Unified generic repository class implementing basic CRUD operations.
    """
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: UUID) -> Optional[ModelType]:
        """
        Retrieves a single record by its UUID primary key.
        """
        result = await self.session.execute(select(self.model).filter_by(id=id))
        return result.scalar_one_or_none()

    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Retrieves multiple records with optional pagination offsets.
        """
        result = await self.session.execute(select(self.model).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, obj_in: ModelType) -> ModelType:
        """
        Adds a new record to the session context.
        """
        self.session.add(obj_in)
        await self.session.flush()
        return obj_in

    async def update(self, db_obj: ModelType, obj_in: dict[str, Any]) -> ModelType:
        """
        Updates an existing model instance attributes.
        """
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        self.session.add(db_obj)
        await self.session.flush()
        return db_obj

    async def delete(self, id: UUID) -> Optional[ModelType]:
        """
        Deletes a record from the database.
        """
        obj = await self.get(id)
        if obj:
            await self.session.delete(obj)
            await self.session.flush()
        return obj
