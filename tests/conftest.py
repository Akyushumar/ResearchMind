import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from researchmind.api.app import create_app
from researchmind.models import Base

# Use aiosqlite for testing (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///"


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def engine():
    """Create a test database engine with in-memory SQLite."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    """Create a session factory for tests."""
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def session(session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for tests."""
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(engine, session_factory) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client with the app configured for testing."""
    app = create_app()
    # Override the app's session factory and engine for testing
    app.state.db_engine = engine
    app.state.session_factory = session_factory
    # Create a mock vector store or skip Qdrant for unit tests
    app.state.vector_store = None  # Tests that need Qdrant should mock it
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
