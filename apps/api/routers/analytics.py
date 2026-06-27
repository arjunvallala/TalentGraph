"""
TalentGraph AI — Analytics API Router

Endpoints for dashboard analytics: hiring funnel, feature importance,
candidate distributions, and risk breakdowns.
"""
from __future__ import annotations

from fastapi import APIRouter, Query, HTTPException, status
from fastapi.responses import ORJSONResponse

from shared.config import settings
from shared.logging_setup import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/analytics/summary",
    summary="Get Analytics Summary",
    description="Returns the complete analytics summary for a job, powering all dashboard charts.",
    response_model=None,
)
async def get_analytics_summary(
    job_id: str = Query(..., description="Job ID to get analytics for"),
) -> ORJSONResponse:
    """
    Retrieve full analytics summary for a ranked job.

    Includes: funnel stats, feature importance, candidate distribution,
    risk breakdown, confidence distribution, recommendation distribution.

    Args:
        job_id: The job to analyse.

    Returns:
        AnalyticsSummary model serialized as JSON.

    Raises:
        404: If no rankings exist for this job.
    """
    try:
        from services.preprocessing.feature_store import FeatureStore
        from services.analytics.funnel_analytics import FunnelAnalytics
        from services.analytics.feature_importance import FeatureImportanceAnalyzer

        store = FeatureStore(settings.duckdb_path)
        results = store.get_ranking_results(job_id)

        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No rankings found for job '{job_id}'.",
            )

        # Build analytics
        funnel = FunnelAnalytics()
        fi_analyzer = FeatureImportanceAnalyzer()

        funnel_stats = funnel.compute_from_results(results)
        feature_importance = fi_analyzer.compute(results)

        # Candidate distribution
        score_buckets = {f"{i/10:.1f}-{(i+1)/10:.1f}": 0 for i in range(10)}
        recommendation_dist: dict = {}
        confidence_dist = {"High": 0, "Medium": 0, "Low": 0}
        risk_dist: dict = {}

        for r in results:
            # Score histogram
            bucket_idx = min(int(r.overall_score * 10), 9)
            key = f"{bucket_idx/10:.1f}-{(bucket_idx+1)/10:.1f}"
            score_buckets[key] = score_buckets.get(key, 0) + 1

            # Recommendation distribution
            rec = r.hiring_recommendation.value
            recommendation_dist[rec] = recommendation_dist.get(rec, 0) + 1

            # Confidence distribution
            conf = r.confidence_level.value
            confidence_dist[conf] = confidence_dist.get(conf, 0) + 1

            # Risk distribution
            if r.risk_assessment:
                risk = r.risk_assessment.risk_level.value
                risk_dist[risk] = risk_dist.get(risk, 0) + 1

        avg_score = sum(r.overall_score for r in results) / len(results) if results else 0.0

        return ORJSONResponse(
            content={
                "job_id": job_id,
                "total_candidates": len(results),
                "avg_overall_score": round(avg_score, 4),
                "funnel": funnel_stats.model_dump(),
                "feature_importance": [f.model_dump() for f in feature_importance],
                "score_distribution": score_buckets,
                "recommendation_distribution": recommendation_dist,
                "confidence_distribution": confidence_dist,
                "risk_distribution": risk_dist,
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Analytics failed for job {job_id}", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get(
    "/analytics/features",
    summary="Get Feature Importance",
    description="Returns ranked feature importance for the current job's candidate pool.",
    response_model=None,
)
async def get_feature_importance(
    job_id: str = Query(..., description="Job ID"),
) -> ORJSONResponse:
    """
    Retrieve feature importance scores for a ranked job.

    Args:
        job_id: The job to analyse.

    Returns:
        List of FeatureImportance objects sorted by importance descending.
    """
    try:
        from services.preprocessing.feature_store import FeatureStore
        from services.analytics.feature_importance import FeatureImportanceAnalyzer

        store = FeatureStore(settings.duckdb_path)
        results = store.get_ranking_results(job_id)

        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No rankings for job '{job_id}'.",
            )

        analyzer = FeatureImportanceAnalyzer()
        importance = analyzer.compute(results)

        return ORJSONResponse(
            content={
                "job_id": job_id,
                "features": [f.model_dump() for f in importance],
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Feature importance failed for job {job_id}", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
