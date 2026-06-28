"""
TalentGraph AI — Custom Exception Hierarchy

Defines a clean, typed exception hierarchy so errors are always
predictable and catchable at the right abstraction level.

Usage:
    from shared.exceptions import CandidateNotFoundError, PipelineError
    raise CandidateNotFoundError(candidate_id="c123", message="Not in feature store")
"""
from __future__ import annotations

from typing import Any

# ── Base ──────────────────────────────────────────────────────────────────────

class TalentGraphError(Exception):
    """Base exception for all TalentGraph AI errors."""

    def __init__(
        self,
        message: str,
        code: str = "TALENTGRAPH_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Serialise exception for API error responses."""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
        }


# ── Configuration ─────────────────────────────────────────────────────────────

class ConfigurationError(TalentGraphError):
    """Raised when required configuration is missing or invalid."""

    def __init__(self, message: str, config_key: str | None = None) -> None:
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            details={"config_key": config_key} if config_key else {},
        )


# ── Data Layer ────────────────────────────────────────────────────────────────

class DataError(TalentGraphError):
    """Base class for data-related errors."""
    pass


class CandidateNotFoundError(DataError):
    """Raised when a candidate cannot be found in the store."""

    def __init__(self, candidate_id: str, message: str | None = None) -> None:
        super().__init__(
            message=message or f"Candidate '{candidate_id}' not found",
            code="CANDIDATE_NOT_FOUND",
            details={"candidate_id": candidate_id},
        )


class JobNotFoundError(DataError):
    """Raised when a job cannot be found in the store."""

    def __init__(self, job_id: str, message: str | None = None) -> None:
        super().__init__(
            message=message or f"Job '{job_id}' not found",
            code="JOB_NOT_FOUND",
            details={"job_id": job_id},
        )


class InvalidDataError(DataError):
    """Raised when input data fails schema or domain validation."""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(
            message=message,
            code="INVALID_DATA",
            details={"field": field} if field else {},
        )


class DuplicateCandidateError(DataError):
    """Raised when the same candidate_id appears multiple times."""

    def __init__(self, candidate_id: str) -> None:
        super().__init__(
            message=f"Duplicate candidate_id: '{candidate_id}'",
            code="DUPLICATE_CANDIDATE",
            details={"candidate_id": candidate_id},
        )


# ── Preprocessing ─────────────────────────────────────────────────────────────

class PreprocessingError(TalentGraphError):
    """Base class for preprocessing pipeline errors."""
    pass


class ParseError(PreprocessingError):
    """Raised when a profile cannot be parsed."""

    def __init__(self, candidate_id: str, reason: str) -> None:
        super().__init__(
            message=f"Failed to parse candidate '{candidate_id}': {reason}",
            code="PARSE_ERROR",
            details={"candidate_id": candidate_id, "reason": reason},
        )


class EmbeddingError(PreprocessingError):
    """Raised when embedding generation fails."""

    def __init__(self, message: str, batch_index: int | None = None) -> None:
        super().__init__(
            message=message,
            code="EMBEDDING_ERROR",
            details={"batch_index": batch_index} if batch_index is not None else {},
        )


class IndexBuildError(PreprocessingError):
    """Raised when FAISS or BM25 index construction fails."""

    def __init__(self, message: str, index_type: str = "unknown") -> None:
        super().__init__(
            message=message,
            code="INDEX_BUILD_ERROR",
            details={"index_type": index_type},
        )


class CheckpointError(PreprocessingError):
    """Raised when checkpoint save/load fails."""

    def __init__(self, message: str, checkpoint_path: str | None = None) -> None:
        super().__init__(
            message=message,
            code="CHECKPOINT_ERROR",
            details={"checkpoint_path": checkpoint_path} if checkpoint_path else {},
        )


# ── Intelligence ──────────────────────────────────────────────────────────────

class IntelligenceError(TalentGraphError):
    """Base class for intelligence engine errors."""
    pass


class JobIntelligenceError(IntelligenceError):
    """Raised when job description analysis fails."""

    def __init__(self, job_id: str, reason: str) -> None:
        super().__init__(
            message=f"Job intelligence failed for '{job_id}': {reason}",
            code="JOB_INTELLIGENCE_ERROR",
            details={"job_id": job_id, "reason": reason},
        )


class CandidateIntelligenceError(IntelligenceError):
    """Raised when candidate genome construction fails."""

    def __init__(self, candidate_id: str, reason: str) -> None:
        super().__init__(
            message=f"Candidate intelligence failed for '{candidate_id}': {reason}",
            code="CANDIDATE_INTELLIGENCE_ERROR",
            details={"candidate_id": candidate_id, "reason": reason},
        )


# ── Ranking ───────────────────────────────────────────────────────────────────

class RankingError(TalentGraphError):
    """Base class for ranking pipeline errors."""
    pass


class RetrievalError(RankingError):
    """Raised when hybrid retrieval fails."""

    def __init__(self, message: str, stage: str = "unknown") -> None:
        super().__init__(
            message=message,
            code="RETRIEVAL_ERROR",
            details={"stage": stage},
        )


class CouncilError(RankingError):
    """Raised when a council evaluator produces an error."""

    def __init__(self, council_name: str, candidate_id: str, reason: str) -> None:
        super().__init__(
            message=f"Council '{council_name}' failed for '{candidate_id}': {reason}",
            code="COUNCIL_ERROR",
            details={
                "council_name": council_name,
                "candidate_id": candidate_id,
                "reason": reason,
            },
        )


class PipelineError(RankingError):
    """Raised when the ranking pipeline encounters a fatal error."""

    def __init__(self, message: str, stage: int | None = None) -> None:
        super().__init__(
            message=message,
            code="PIPELINE_ERROR",
            details={"stage": stage} if stage is not None else {},
        )


# ── Feature Store ─────────────────────────────────────────────────────────────

class FeatureStoreError(TalentGraphError):
    """Raised when feature store read/write fails."""

    def __init__(self, message: str, operation: str | None = None) -> None:
        super().__init__(
            message=message,
            code="FEATURE_STORE_ERROR",
            details={"operation": operation} if operation else {},
        )


# ── Submission ────────────────────────────────────────────────────────────────

class SubmissionError(TalentGraphError):
    """Raised when submission generation or validation fails."""

    def __init__(self, message: str, row_index: int | None = None) -> None:
        super().__init__(
            message=message,
            code="SUBMISSION_ERROR",
            details={"row_index": row_index} if row_index is not None else {},
        )


# ── HTTP / API ────────────────────────────────────────────────────────────────

class APIError(TalentGraphError):
    """Base class for API-level errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        code: str = "API_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        super().__init__(message=message, code=code, details=details)


class NotFoundError(APIError):
    """404 — Resource not found."""

    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(
            message=f"{resource} '{resource_id}' not found",
            status_code=404,
            code="NOT_FOUND",
            details={"resource": resource, "id": resource_id},
        )


class ValidationError(APIError):
    """422 — Request validation failed."""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(
            message=message,
            status_code=422,
            code="VALIDATION_ERROR",
            details={"field": field} if field else {},
        )


class ServiceUnavailableError(APIError):
    """503 — Downstream service unavailable."""

    def __init__(self, service: str, reason: str) -> None:
        super().__init__(
            message=f"Service '{service}' is unavailable: {reason}",
            status_code=503,
            code="SERVICE_UNAVAILABLE",
            details={"service": service, "reason": reason},
        )
