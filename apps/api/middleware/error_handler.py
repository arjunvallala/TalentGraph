"""
TalentGraph AI — API Error Handlers

Registers global exception handlers that convert TalentGraph exceptions
and FastAPI validation errors into consistent JSON error responses.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse

from shared.exceptions import (
    APIError,
    CandidateNotFoundError,
    JobNotFoundError,
    TalentGraphError,
)
from shared.logging_setup import get_logger

logger = get_logger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers on the FastAPI application.

    Args:
        app: The FastAPI application instance.
    """

    @app.exception_handler(TalentGraphError)
    async def talentgraph_error_handler(request: Request, exc: TalentGraphError) -> ORJSONResponse:
        """Handle all TalentGraph domain errors."""
        # Determine status code
        if isinstance(exc, APIError):
            status_code = exc.status_code
        elif isinstance(exc, CandidateNotFoundError | JobNotFoundError):
            status_code = status.HTTP_404_NOT_FOUND
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        logger.error(
            f"TalentGraph error: {exc.message}",
            error_code=exc.code,
            details=exc.details,
            path=str(request.url.path),
        )

        return ORJSONResponse(
            status_code=status_code,
            content=exc.to_dict(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> ORJSONResponse:
        """Handle Pydantic request validation errors."""
        logger.warning(
            "Request validation failed",
            path=str(request.url.path),
            errors=str(exc.errors()),
        )
        return ORJSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": exc.errors()},
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> ORJSONResponse:
        """Catch-all handler for unexpected exceptions."""
        logger.exception(
            "Unexpected error",
            path=str(request.url.path),
            error_type=type(exc).__name__,
        )
        return ORJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {},
            },
        )
