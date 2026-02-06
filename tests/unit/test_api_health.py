"""
Unit tests for health check endpoints.
"""

from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health check endpoints."""

    async def test_basic_health(self, client: AsyncClient):
        """Test basic health endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    async def test_liveness_check(self, client: AsyncClient):
        """Test liveness endpoint."""
        response = await client.get("/health/live")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    async def test_startup_check(self, client: AsyncClient):
        """Test startup endpoint."""
        response = await client.get("/health/startup")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
