"""
TalentGraph AI — Candidates API Router

Endpoints for retrieving ranked candidate lists and individual profiles.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import ORJSONResponse

from shared.config import settings
from shared.logging_setup import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/candidates/ranked",
    summary="Get Ranked Candidates",
    description=(
        "Returns the ranked list of candidates for a given job. "
        "Supports pagination and filtering."
    ),
    response_model=None,
)
async def get_ranked_candidates(
    job_id: str = Query(..., description="Job ID to retrieve rankings for"),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Results per page"),
    min_score: float | None = Query(default=None, ge=0.0, le=1.0),
    max_score: float | None = Query(default=None, ge=0.0, le=1.0),
    recommendation: str | None = Query(default=None),
    confidence: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
) -> ORJSONResponse:
    """
    Retrieve the ranked candidate list for a specific job.

    Supports filtering by score range, recommendation, confidence, and risk.
    Results are paginated.

    Args:
        job_id: The job to retrieve rankings for.
        page: Page number (1-indexed).
        page_size: Number of results per page.
        min_score: Filter — minimum overall score.
        max_score: Filter — maximum overall score.
        recommendation: Filter — hiring recommendation label.
        confidence: Filter — confidence level (High/Medium/Low).
        risk_level: Filter — risk level filter.

    Returns:
        Paginated list of CandidateResult objects.

    Raises:
        404: If no rankings exist for the given job_id.
    """
    try:
        from services.preprocessing.feature_store import FeatureStore

        store = FeatureStore(settings.duckdb_path)
        results = store.get_ranking_results(job_id)

        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No rankings found for job '{job_id}'. Run the ranking pipeline first.",
            )

        # Apply filters
        if min_score is not None:
            results = [r for r in results if r.overall_score >= min_score]
        if max_score is not None:
            results = [r for r in results if r.overall_score <= max_score]
        if recommendation:
            results = [r for r in results if r.hiring_recommendation.value == recommendation]
        if confidence:
            results = [r for r in results if r.confidence_level.value == confidence]
        if risk_level and results:
            results = [
                r
                for r in results
                if r.risk_assessment and r.risk_assessment.risk_level.value == risk_level
            ]

        # Paginate
        total = len(results)
        offset = (page - 1) * page_size
        page_results = results[offset : offset + page_size]

        return ORJSONResponse(
            content={
                "job_id": job_id,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "candidates": [r.model_dump() for r in page_results],
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Failed to retrieve rankings for {job_id}", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get(
    "/candidates/{candidate_id}",
    summary="Get Candidate Detail",
    description="Retrieve the full profile, genome, evidence, and council votes for a candidate.",
    response_model=None,
)
async def get_candidate_detail(
    candidate_id: str,
    job_id: str | None = Query(default=None, description="Job context for scores"),
) -> ORJSONResponse:
    """
    Retrieve complete candidate detail for the Candidate Detail page.

    Returns the full CandidateResult including:
    - Profile information
    - Feature scores
    - Candidate genome (radar chart data)
    - Evidence ledger
    - Council votes
    - Risk assessment
    - Explanation

    Args:
        candidate_id: The candidate's unique identifier.
        job_id: Optional job context for JD-dependent scores.

    Returns:
        Full CandidateResult with all nested data.

    Raises:
        404: If candidate not found.
    """
    try:
        from services.preprocessing.feature_store import FeatureStore

        store = FeatureStore(settings.duckdb_path)
        profile = store.get_candidate_profile(candidate_id)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate '{candidate_id}' not found.",
            )

        features = store.get_features(candidate_id)

        # If a job context is provided, try to get the ranked result
        if job_id:
            results = store.get_ranking_results(job_id)
            candidate_result = next((r for r in results if r.candidate_id == candidate_id), None)
            if candidate_result:
                return ORJSONResponse(content=candidate_result.model_dump())

        # Fallback: return profile + features without ranking context
        response_data = {
            "candidate_id": candidate_id,
            "profile": profile.model_dump(),
            "features": features.model_dump() if features else None,
        }
        return ORJSONResponse(content=response_data)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Failed to retrieve candidate {candidate_id}", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post(
    "/candidates/rank",
    summary="Run Full Ranking Pipeline",
    description=(
        "Triggers the complete 4-stage ranking pipeline for a job description. "
        "This is the main endpoint that orchestrates the entire AI pipeline."
    ),
    response_model=None,
)
async def run_ranking(
    job_id: str = Query(..., description="Job ID to rank candidates for"),
) -> ORJSONResponse:
    """
    Run the complete TalentGraph AI ranking pipeline.

    Stages:
    1. Load job profile from store
    2. Hybrid retrieval (FAISS + BM25) → Top 2,000
    3. Feature ranking → Top 200
    4. Hiring Council evaluation → Top 100
    5. Explainability generation
    6. Store results

    Args:
        job_id: The job to rank candidates for.

    Returns:
        RankedList with full results.

    Raises:
        404: If job not found in store.
        503: If required indexes are not ready.
    """
    import time

    start = time.perf_counter()

    try:
        from services.preprocessing.feature_store import FeatureStore
        from services.ranking.ranking_pipeline import RankingPipeline

        store = FeatureStore(settings.duckdb_path)
        job_profile = store.get_job_profile(job_id)

        if not job_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job '{job_id}' not found. Analyze it first via POST /api/v1/jobs/analyze",
            )

        pipeline = RankingPipeline(config=settings, feature_store=store)

        # Build a minimal JobRaw from stored profile
        from shared.types.job import JobRaw

        job_raw = JobRaw(
            job_id=job_id,
            title=job_profile.title,
            description=" ".join(job_profile.key_responsibilities),
        )

        ranked_list = pipeline.rank(job_raw)
        duration_ms = (time.perf_counter() - start) * 1000

        return ORJSONResponse(
            content={
                "job_id": job_id,
                "total_candidates": ranked_list.total_processed,
                "shortlisted": len(ranked_list.candidates),
                "duration_ms": round(duration_ms, 2),
                "candidates": [c.model_dump() for c in ranked_list.candidates[:10]],
                "message": f"Ranking complete. {len(ranked_list.candidates)} candidates shortlisted.",
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Ranking pipeline failed for job {job_id}", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ranking pipeline failed: {str(exc)}",
        )
