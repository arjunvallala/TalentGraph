"""
TalentGraph AI — Health Check Endpoints

Provides health, readiness, and liveness endpoints for the API.
Used by Docker health checks, load balancers, and monitoring systems.
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi.responses import ORJSONResponse

from shared.config import settings
from shared.constants import APP_NAME, APP_VERSION
from shared.logging_setup import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Track startup time
_startup_time = time.time()


@router.get(
    "/health",
    summary="Health Check",
    description="Returns the API health status. Used by load balancers and Docker.",
    response_model=None,
)
async def health_check() -> ORJSONResponse:
    """
    Basic health check endpoint.

    Returns:
        200 OK with health status, version, and uptime.
    """
    uptime_seconds = int(time.time() - _startup_time)

    return ORJSONResponse(
        content={
            "status": "healthy",
            "service": APP_NAME,
            "version": APP_VERSION,
            "environment": settings.app_env,
            "demo_mode": settings.demo_mode,
            "uptime_seconds": uptime_seconds,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    )


@router.get(
    "/health/ready",
    summary="Readiness Check",
    description="Checks if the service is ready to handle requests (data files exist).",
    response_model=None,
)
async def readiness_check() -> ORJSONResponse:
    """
    Readiness check — verifies data dependencies exist.

    Returns:
        200 if ready, 503 if dependencies are missing.
    """
    checks: dict[str, Any] = {}
    all_ready = True

    # Check DuckDB
    duckdb_exists = Path(settings.duckdb_path).exists()
    checks["duckdb"] = {
        "path": settings.duckdb_path,
        "status": "ready" if duckdb_exists or settings.demo_mode else "not_found",
    }
    if not duckdb_exists and not settings.demo_mode:
        all_ready = False

    # Check FAISS index
    faiss_exists = Path(settings.faiss_index_path).exists()
    checks["faiss_index"] = {
        "path": settings.faiss_index_path,
        "status": "ready" if faiss_exists or settings.demo_mode else "not_found",
    }
    if not faiss_exists and not settings.demo_mode:
        all_ready = False

    # Check BM25 index
    bm25_exists = Path(settings.bm25_index_path).exists()
    checks["bm25_index"] = {
        "path": settings.bm25_index_path,
        "status": "ready" if bm25_exists or settings.demo_mode else "not_found",
    }
    if not bm25_exists and not settings.demo_mode:
        all_ready = False

    # Check embedding model
    model_exists = Path(settings.embedding_model_path).exists()
    checks["embedding_model"] = {
        "model": settings.embedding_model_name,
        "status": "ready" if model_exists else "not_downloaded",
    }

    # Demo mode override
    if settings.demo_mode:
        checks["demo_mode"] = {"status": "active", "note": "Using pre-generated fixture data"}
        all_ready = True

    status_code = 200 if all_ready else 503

    return ORJSONResponse(
        status_code=status_code,
        content={
            "ready": all_ready,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@router.get(
    "/health/live",
    summary="Liveness Check",
    description="Simple liveness probe — returns 200 if process is alive.",
    response_model=None,
)
async def liveness_check() -> ORJSONResponse:
    """
    Kubernetes-style liveness probe.

    Returns:
        200 OK — if the process is running, this always succeeds.
    """
    return ORJSONResponse(content={"alive": True})
