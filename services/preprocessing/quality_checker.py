"""
TalentGraph AI — Data Quality Checker

Performs range checks, missing data analysis, and schema validation
on processed candidate features, generating a structured QA report.
"""
from __future__ import annotations

from typing import Any

import polars as pl

from shared.logging_setup import get_logger

logger = get_logger(__name__)


class QualityChecker:
    """
    Validates features and profile coverage, returning detailed metrics
    and warnings for dataset quality.
    """

    def __init__(self) -> None:
        """Initialize the quality checker."""
        logger.info("QualityChecker initialized")

    def run_checks(self, df: pl.DataFrame) -> dict[str, Any]:
        """
        Run completeness, range, and consistency checks on features dataframe.

        Args:
            df: Polars DataFrame of candidate features.

        Returns:
            A dictionary containing audit stats, passed status, and warning lists.
        """
        if df.is_empty():
            return {
                "passed": False,
                "total_records": 0,
                "errors": ["Dataframe is empty"],
                "warnings": [],
                "metrics": {},
            }

        total_records = len(df)
        warnings = []
        errors = []
        metrics = {}

        # 1. Null Checks
        null_counts = df.null_count()
        null_dict = {col: null_counts[col][0] for col in df.columns}
        metrics["null_counts"] = null_dict

        # Crucial field: candidate_id must have no nulls
        if null_dict.get("candidate_id", 0) > 0:
            errors.append(f"Found {null_dict['candidate_id']} null candidate IDs.")

        # 2. Bound Checks [0.0, 1.0] for features
        feature_cols = [
            c for c in df.columns if c != "candidate_id"
        ]

        out_of_bounds = {}
        for col in feature_cols:
            # Check min and max
            min_val = df[col].min()
            max_val = df[col].max()
            metrics[f"{col}_min"] = min_val
            metrics[f"{col}_max"] = max_val

            if min_val is not None and (min_val < 0.0 or min_val > 1.0001):
                out_of_bounds[col] = out_of_bounds.get(col, []) + [f"min={min_val}"]
            if max_val is not None and (max_val < -0.0001 or max_val > 1.0001):
                out_of_bounds[col] = out_of_bounds.get(col, []) + [f"max={max_val}"]

        if out_of_bounds:
            for col, issues in out_of_bounds.items():
                warnings.append(
                    f"Feature '{col}' has values outside [0.0, 1.0] bounds: {', '.join(issues)}"
                )

        # 3. Variance / Completeness Warnings
        # e.g., if a feature has zero variance across the dataset, warn
        for col in feature_cols:
            std_val = df[col].std()
            if std_val is not None and std_val < 1e-4:
                warnings.append(
                    f"Feature '{col}' has near-zero standard deviation ({std_val:.6f}). Check extractor logic."
                )

        passed = len(errors) == 0

        logger.info(
            f"Quality checks complete. Passed: {passed}. Total records: {total_records}. "
            f"Errors: {len(errors)}, Warnings: {len(warnings)}"
        )

        return {
            "passed": passed,
            "total_records": total_records,
            "errors": errors,
            "warnings": warnings,
            "metrics": metrics,
        }
