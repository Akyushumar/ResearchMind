from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from researchmind.models.base import Base


def create_engine(database_url: str, echo: bool = False) -> AsyncEngine:
    """Create async SQLAlchemy engine."""
    return create_async_engine(
        database_url,
        echo=echo,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
    )


async def create_tables(engine: AsyncEngine) -> None:
    """Create all tables in the database. Useful for testing."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
