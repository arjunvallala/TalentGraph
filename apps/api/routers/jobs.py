"""
TalentGraph AI — Jobs API Router

Endpoints for job description analysis and ideal candidate persona generation.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel, Field

from shared.config import settings
from shared.logging_setup import get_logger

logger = get_logger(__name__)
router = APIRouter()


# ── Request / Response Schemas ────────────────────────────────────────────────

class AnalyzeJobRequest(BaseModel):
    """Request body for job description analysis."""
    job_id: str = Field(default="job_001", description="Unique job identifier")
    title: str = Field(..., min_length=2, max_length=200, description="Job title")
    description: str = Field(..., min_length=50, description="Full job description text")
    company: str | None = Field(default=None, description="Hiring company name")
    location: str | None = Field(default=None, description="Job location")


class AnalyzeJobResponse(BaseModel):
    """Response containing full job intelligence analysis."""
    job_id: str
    job_profile: dict[str, Any]
    ideal_persona: dict[str, Any]
    job_genome: dict[str, Any]
    analysis_duration_ms: float


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/jobs/analyze",
    summary="Analyze Job Description",
    description=(
        "Analyzes a job description to extract structured requirements, "
        "build an Ideal Candidate Persona, and generate the Job Genome "
        "used for candidate ranking."
    ),
    response_model=None,
    status_code=status.HTTP_200_OK,
)
async def analyze_job(request: AnalyzeJobRequest) -> ORJSONResponse:
    """
    Analyze a job description and return structured job intelligence.

    This endpoint:
    1. Parses the JD to extract skills, experience requirements, and domain
    2. Builds the Ideal Candidate Persona (what the perfect hire looks like)
    3. Generates the Job Genome (feature weight vector for ranking)
    4. Generates embeddings for semantic search

    Args:
        request: Job description and metadata.

    Returns:
        AnalyzeJobResponse with full job intelligence.

    Raises:
        422: If the job description is too short or invalid.
        503: If the embedding model is not loaded.
    """
    import time
    start = time.perf_counter()

    logger.info(f"Analyzing job: {request.job_id} — '{request.title}'")

    try:
        # Import here to avoid circular imports and enable lazy loading
        from services.intelligence.job_intelligence import JobIntelligenceEngine
        from services.preprocessing.embedding_generator import EmbeddingGenerator
        from shared.types.job import JobRaw, JobType

        job_raw = JobRaw(
            job_id=request.job_id,
            title=request.title,
            description=request.description,
            company=request.company,
            location=request.location,
            job_type=JobType.FULL_TIME,
        )

        embedding_gen = EmbeddingGenerator(settings.embedding_model_name)
        embedding_gen.load_model()

        engine = JobIntelligenceEngine(embedding_gen)
        job_profile, ideal_persona, job_genome = engine.analyze(job_raw)

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"Job analysis complete: {request.job_id}",
            duration_ms=round(duration_ms, 2),
            skills_found=len(job_profile.required_skills),
        )

        return ORJSONResponse(
            content={
                "job_id": request.job_id,
                "job_profile": job_profile.model_dump(),
                "ideal_persona": ideal_persona.model_dump(),
                "job_genome": job_genome.model_dump(exclude={"embedding"}),
                "analysis_duration_ms": round(duration_ms, 2),
            }
        )

    except Exception as exc:
        logger.exception(f"Job analysis failed: {request.job_id}", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job analysis failed: {str(exc)}",
        )


@router.get(
    "/jobs/{job_id}",
    summary="Get Job Details",
    description="Retrieve a previously analyzed job profile.",
    response_model=None,
)
async def get_job(job_id: str) -> ORJSONResponse:
    """
    Retrieve a stored job profile by ID.

    Args:
        job_id: The job identifier.

    Returns:
        Stored job profile data.

    Raises:
        404: If the job is not found.
    """
    try:
        from services.preprocessing.feature_store import FeatureStore
        store = FeatureStore(settings.duckdb_path)
        job_profile = store.get_job_profile(job_id)
        if not job_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job '{job_id}' not found. Run analysis first.",
            )
        return ORJSONResponse(content=job_profile.model_dump())
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Failed to retrieve job {job_id}", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get(
    "/jobs",
    summary="List Jobs",
    description="List all analyzed job descriptions.",
    response_model=None,
)
async def list_jobs() -> ORJSONResponse:
    """
    List all stored job profiles.

    Returns:
        List of job summaries with job_id and title.
    """
    try:
        from services.preprocessing.feature_store import FeatureStore
        store = FeatureStore(settings.duckdb_path)
        jobs = store.list_jobs()
        return ORJSONResponse(content={"jobs": jobs, "count": len(jobs)})
    except Exception as exc:
        logger.exception("Failed to list jobs", error=str(exc))
        # Return empty list on error (not fatal)
        return ORJSONResponse(content={"jobs": [], "count": 0})
