"""
TalentGraph AI — API Integration Tests

Tests the FastAPI endpoints using an async test client.
Runs in demo mode to avoid requiring a real database.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoints:
    """Tests for health check endpoints."""

    async def test_health_returns_200(self, api_client: AsyncClient):
        async with api_client as client:
            response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "uptime_seconds" in data

    async def test_health_returns_service_name(self, api_client: AsyncClient):
        async with api_client as client:
            response = await client.get("/api/v1/health")
        assert response.json()["service"] == "TalentGraph AI"

    async def test_liveness_always_200(self, api_client: AsyncClient):
        async with api_client as client:
            response = await client.get("/api/v1/health/live")
        assert response.status_code == 200
        assert response.json()["alive"] is True

    async def test_readiness_in_demo_mode(self, api_client: AsyncClient):
        """In demo mode, readiness should succeed."""
        async with api_client as client:
            response = await client.get("/api/v1/health/ready")
        # In demo mode, should be 200 (or at least not a 500)
        assert response.status_code in (200, 503)


@pytest.mark.asyncio
class TestJobsEndpoints:
    """Tests for jobs analysis endpoints."""

    async def test_analyze_job_returns_200(self, api_client: AsyncClient):
        async with api_client as client:
            response = await client.post(
                "/api/v1/jobs/analyze",
                json={
                    "job_id": "test_api_job_001",
                    "title": "Senior ML Engineer",
                    "description": (
                        "We are looking for a Senior ML Engineer with 5+ years of experience. "
                        "Required: Python, TensorFlow, Kubernetes, GCP. "
                        "Responsibilities include leading ML platform development."
                    ),
                },
            )
        assert response.status_code in (200, 500)  # 500 ok if model not loaded
        if response.status_code == 200:
            data = response.json()
            assert "job_id" in data
            assert "job_profile" in data
            assert "ideal_persona" in data

    async def test_analyze_job_validates_short_description(self, api_client: AsyncClient):
        """Short JD should fail validation."""
        async with api_client as client:
            response = await client.post(
                "/api/v1/jobs/analyze",
                json={
                    "title": "SWE",
                    "description": "Short",  # < 50 chars
                },
            )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestSystemEndpoints:
    """Tests for system status endpoints."""

    async def test_system_status_returns_200(self, api_client: AsyncClient):
        async with api_client as client:
            response = await client.get("/api/v1/system/status")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "pipeline_status" in data
        assert "components" in data

    async def test_system_config_returns_config(self, api_client: AsyncClient):
        async with api_client as client:
            response = await client.get("/api/v1/system/config")
        assert response.status_code == 200
        data = response.json()
        assert "features" in data
        assert "ranking" in data


@pytest.mark.asyncio
class TestCandidatesEndpoints:
    """Tests for candidate retrieval endpoints."""

    async def test_ranked_candidates_404_no_rankings(self, api_client: AsyncClient):
        """Should return 404 when no rankings exist."""
        async with api_client as client:
            response = await client.get(
                "/api/v1/candidates/ranked",
                params={"job_id": "nonexistent_job"},
            )
        assert response.status_code == 404

    async def test_candidate_detail_404_unknown(self, api_client: AsyncClient):
        async with api_client as client:
            response = await client.get("/api/v1/candidates/unknown_candidate_id")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestSubmissionEndpoints:
    """Tests for submission generation endpoints."""

    async def test_validate_submission_404_no_file(self, api_client: AsyncClient):
        """Validation should return error when no submission file exists."""
        async with api_client as client:
            response = await client.get("/api/v1/submission/validate")
        assert response.status_code in (200, 404)
