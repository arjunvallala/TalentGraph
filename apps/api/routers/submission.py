"""
TalentGraph AI — Submission API Router

Endpoints for generating and validating the submission.csv file.
"""
from __future__ import annotations

from fastapi import APIRouter, Query, HTTPException, status
from fastapi.responses import FileResponse, ORJSONResponse

from shared.config import settings
from shared.logging_setup import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/submission/generate",
    summary="Generate Submission CSV",
    description=(
        "Generates the submission.csv file from the current ranking results. "
        "File format: candidate_id, rank, overall_score, confidence_level, hiring_recommendation."
    ),
    response_model=None,
)
async def generate_submission(
    job_id: str = Query(..., description="Job ID to generate submission for"),
) -> ORJSONResponse:
    """
    Generate the submission.csv file for INDIA RUNS challenge submission.

    Args:
        job_id: The job to generate submission for.

    Returns:
        Path to generated file and row count.

    Raises:
        404: If no rankings exist for this job.
    """
    try:
        from services.preprocessing.feature_store import FeatureStore
        from services.analytics.submission_generator import SubmissionGenerator

        store = FeatureStore(settings.duckdb_path)
        results = store.get_ranking_results(job_id)

        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No rankings found for job '{job_id}'. Run ranking first.",
            )

        generator = SubmissionGenerator()
        output_path = generator.generate(results, settings.submission_output_path)

        return ORJSONResponse(
            content={
                "success": True,
                "output_path": output_path,
                "row_count": len(results),
                "job_id": job_id,
                "message": f"submission.csv generated with {len(results)} candidates.",
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Submission generation failed for {job_id}", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get(
    "/submission/validate",
    summary="Validate Submission CSV",
    description="Validates the generated submission.csv for format correctness.",
    response_model=None,
)
async def validate_submission(
    job_id: str = Query(default="", description="Job ID (for context)"),
) -> ORJSONResponse:
    """
    Validate the submission CSV format.

    Checks:
    - Required columns present
    - No duplicate candidate_ids
    - Ranks are sequential and 1-indexed
    - No null values
    - Overall scores are in [0, 1]

    Returns:
        Validation result with any errors found.
    """
    try:
        from services.analytics.submission_generator import SubmissionGenerator
        generator = SubmissionGenerator()
        valid, errors = generator.validate(settings.submission_output_path)

        return ORJSONResponse(
            content={
                "valid": valid,
                "errors": errors,
                "file_path": settings.submission_output_path,
                "message": "Submission is valid ✓" if valid else f"Found {len(errors)} validation error(s)",
            }
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="submission.csv not found. Generate it first.",
        )
    except Exception as exc:
        logger.exception("Submission validation failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get(
    "/submission/download",
    summary="Download Submission CSV",
    description="Download the submission.csv file directly.",
)
async def download_submission() -> FileResponse:
    """
    Download the generated submission.csv file.

    Returns:
        CSV file as a downloadable response.
    """
    import os
    if not os.path.exists(settings.submission_output_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="submission.csv not found. Generate it first.",
        )
    return FileResponse(
        path=settings.submission_output_path,
        media_type="text/csv",
        filename="submission.csv",
    )


@router.get(
    "/submission/download-xlsx",
    summary="Download Submission XLSX",
    description="Download the submission.xlsx file directly (Excel format for hackathon).",
)
async def download_submission_xlsx() -> FileResponse:
    """
    Download the generated submission.xlsx file.

    Returns:
        XLSX file as a downloadable response.
    """
    import os
    from pathlib import Path

    xlsx_path = str(Path(settings.submission_output_path).with_suffix(".xlsx"))
    if not os.path.exists(xlsx_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="submission.xlsx not found. Generate the submission first.",
        )
    return FileResponse(
        path=xlsx_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="submission.xlsx",
    )
