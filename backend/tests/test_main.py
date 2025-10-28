"""
Basic tests for FastAPI app initialization.

AICODE-NOTE: These tests verify the setup is correct and basic endpoints work.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


# AICODE-NOTE: TestClient allows synchronous testing of async FastAPI endpoints
client = TestClient(app)


def test_root_endpoint() -> None:
    """Test root endpoint returns expected response."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert "service" in data
    assert data["service"] == "TextScript API"
    assert data["status"] == "running"


def test_health_endpoint() -> None:
    """Test health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] == "healthy"


def test_cors_headers() -> None:
    """
    Test CORS headers are configured correctly.

    AICODE-NOTE: Ensures frontend at localhost:3000 can make requests.
    """
    response = client.options(
        "/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        }
    )

    # AICODE-NOTE: CORS preflight should return 200
    assert response.status_code == 200

    # AICODE-NOTE: Verify CORS headers are present
    assert "access-control-allow-origin" in response.headers
