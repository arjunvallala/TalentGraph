"""
TalentGraph AI — System API Router

System status, configuration, and pipeline management endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import ORJSONResponse

from shared.config import settings
from shared.constants import APP_NAME, APP_VERSION
from shared.logging_setup import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/system/status",
    summary="System Status",
    description="Returns detailed system status including pipeline readiness and config.",
    response_model=None,
)
async def get_system_status() -> ORJSONResponse:
    """
    Return detailed system status for the Settings and Status pages.

    Returns:
        System configuration, pipeline status, and data availability.
    """
    from pathlib import Path

    indexes_ready = (
        Path(settings.faiss_index_path).exists() and Path(settings.bm25_index_path).exists()
    )
    db_ready = Path(settings.duckdb_path).exists()
    model_ready = Path(settings.embedding_model_path).exists()

    pipeline_status = "ready" if (indexes_ready and db_ready) else "not_initialized"
    if settings.demo_mode:
        pipeline_status = "demo_mode"

    return ORJSONResponse(
        content={
            "app_name": APP_NAME,
            "version": APP_VERSION,
            "environment": settings.app_env,
            "demo_mode": settings.demo_mode,
            "pipeline_status": pipeline_status,
            "components": {
                "duckdb": {"ready": db_ready, "path": settings.duckdb_path},
                "faiss_index": {"ready": indexes_ready, "path": settings.faiss_index_path},
                "bm25_index": {"ready": indexes_ready, "path": settings.bm25_index_path},
                "embedding_model": {
                    "ready": model_ready,
                    "name": settings.embedding_model_name,
                    "path": settings.embedding_model_path,
                },
            },
            "config": {
                "stage1_top_k": settings.ranking_stage1_top_k,
                "stage2_top_k": settings.ranking_stage2_top_k,
                "stage3_top_k": settings.ranking_stage3_top_k,
                "hybrid_alpha": settings.hybrid_alpha,
                "confidence_high": settings.confidence_high_threshold,
                "confidence_low": settings.confidence_low_threshold,
                "embedding_dimension": settings.embedding_dimension,
            },
        }
    )


@router.get(
    "/system/config",
    summary="Get System Configuration",
    description="Returns the current feature weights and ranking configuration.",
    response_model=None,
)
async def get_config() -> ORJSONResponse:
    """
    Return the current YAML configuration for the Settings page.

    Returns:
        Parsed YAML configs (features, ranking, council).
    """
    try:
        features_config = settings.get_config_file("features")
        ranking_config = settings.get_config_file("ranking")
        council_config = settings.get_config_file("council")

        return ORJSONResponse(
            content={
                "features": features_config,
                "ranking": ranking_config,
                "council": council_config,
            }
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
