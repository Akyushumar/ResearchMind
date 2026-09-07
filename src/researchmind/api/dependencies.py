from typing import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from researchmind.config.settings import Settings, get_settings
from researchmind.db.vector_store import VectorStore


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get async database session."""
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_vector_store(request: Request) -> VectorStore:
    """Dependency to get vector store."""
    return request.app.state.vector_store


def get_settings_dep() -> Settings:
    """Dependency to get application settings."""
    return get_settings()
