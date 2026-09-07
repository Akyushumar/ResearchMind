"""Health check endpoint."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from researchmind.api.dependencies import get_db, get_vector_store
from researchmind.db.vector_store import VectorStore
from researchmind.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> HealthResponse:
    """Check API, PostgreSQL, and Qdrant connectivity.

    Returns status of each subsystem. Overall status is 'healthy' if all
    subsystems are connected, 'degraded' otherwise.
    """
    # Check PostgreSQL
    postgres_status = "disconnected"
    try:
        await db.execute(text("SELECT 1"))
        postgres_status = "connected"
    except Exception as e:
        postgres_status = f"error: {e}"

    # Check Qdrant
    qdrant_status = "disconnected"
    vector_store: VectorStore | None = getattr(request.app.state, "vector_store", None)
    if vector_store is not None:
        try:
            if vector_store.health_check():
                qdrant_status = "connected"
        except Exception as e:
            qdrant_status = f"error: {e}"
    else:
        qdrant_status = "not configured"

    overall = "healthy" if postgres_status == "connected" and qdrant_status == "connected" else "degraded"

    return HealthResponse(
        status=overall,
        postgres=postgres_status,
        qdrant=qdrant_status,
        version="0.1.0",
    )
