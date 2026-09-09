import contextlib
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from researchmind.api.routes import clauses, documents, health, ingestion, jurisdictions, search
from researchmind.config.logging import get_logger, setup_logging
from researchmind.config.settings import get_settings
from researchmind.db.engine import create_engine
from researchmind.db.session import create_session_factory
from researchmind.db.vector_store import VectorStore

logger = get_logger(__name__)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan events."""
    settings = get_settings()
    
    # 1. Create DB engine
    engine = create_engine(settings.database_url, echo=settings.debug)
    
    # 2. Create session factory
    session_factory = create_session_factory(engine)
    
    # 3. Store in app.state
    app.state.session_factory = session_factory
    
    # 4. Create VectorStore, store in app.state
    vector_store = VectorStore(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        collection_name=settings.qdrant_collection,
    )
    # Ensure collection exists with proper dimensions
    vector_store.ensure_collection(vector_size=settings.embedding_dimension)
    
    app.state.vector_store = vector_store
    
    # 5. Ensure upload directory exists
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("researchmind_started")
    yield
    
    # Shutdown:
    # 1. Dispose engine
    await engine.dispose()
    logger.info("researchmind_stopped")


def create_app() -> FastAPI:
    """Create FastAPI application."""
    settings = get_settings()
    setup_logging(settings.log_level, settings.env)

    app = FastAPI(
        title="ResearchMind",
        description="AI-powered regulatory intelligence platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware (permissive for dev)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include all routers
    app.include_router(health.router)
    app.include_router(documents.router)
    app.include_router(jurisdictions.router)
    app.include_router(clauses.router)
    app.include_router(ingestion.router)
    app.include_router(search.router)
    app.include_router(qa.router)

    return app
