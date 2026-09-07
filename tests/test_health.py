import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Test that the health endpoint returns expected structure."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_health_reports_postgres_status(client: AsyncClient):
    """Test that health check reports PostgreSQL status."""
    response = await client.get("/health")
    data = response.json()
    assert "postgres" in data


@pytest.mark.asyncio  
async def test_health_reports_qdrant_status(client: AsyncClient):
    """Test that health check reports Qdrant status."""
    response = await client.get("/health")
    data = response.json()
    assert "qdrant" in data
