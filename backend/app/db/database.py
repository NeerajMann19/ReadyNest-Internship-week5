"""
Database engine and connection handlers.
"""
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True
)

async def check_db_health() -> bool:
    """
    Checks the health of the database connection by executing a simple SELECT 1 query.
    Returns:
        bool: True if connection is successful, False otherwise.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("Database health check failed: %s", str(e), exc_info=True)
        return False
