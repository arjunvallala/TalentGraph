"""
TalentGraph AI — Candidate CSV Loader

Responsible for loading raw candidate data from CSV files using Polars,
validating schema, and providing basic dataset statistics.

Handles missing optional columns gracefully — only candidate_id is required.
"""
from __future__ import annotations

import polars as pl

from shared.logging_setup import get_logger

logger = get_logger(__name__)

# Required columns that MUST be present in the CSV
REQUIRED_COLUMNS: list[str] = ["candidate_id"]

# Optional columns — loaded if present, defaults used if absent
OPTIONAL_COLUMNS: list[str] = [
    "name", "email", "phone", "current_title", "current_company",
    "years_of_experience", "skills", "education", "work_history",
    "certifications", "languages", "summary", "location",
    "profile_views", "application_count", "response_rate",
    "last_active_days", "notice_period_days", "availability_status",
    "expected_salary", "open_to_remote",
]

# Column default values for graceful filling
COLUMN_DEFAULTS: dict[str, object] = {
    "name": "",
    "email": "",
    "phone": "",
    "current_title": "",
    "current_company": "",
    "years_of_experience": 0.0,
    "skills": "",
    "education": "",
    "work_history": "",
    "certifications": "",
    "languages": "",
    "summary": "",
    "location": "",
    "profile_views": 0,
    "application_count": 0,
    "response_rate": 0.0,
    "last_active_days": None,
    "notice_period_days": None,
    "availability_status": "unknown",
    "expected_salary": None,
    "open_to_remote": False,
}


class CandidateLoader:
    """
    Loads and validates raw candidate CSV files into Polars DataFrames.

    Handles schema validation, missing column injection, and basic
    statistics reporting. Does NOT do any data cleaning — that is
    the responsibility of DataCleaner.

    Example:
        loader = CandidateLoader()
        df = loader.load_from_csv("data/raw/candidates.csv")
        valid, issues = loader.validate_schema(df)
        stats = loader.get_statistics(df)
    """

    def __init__(self) -> None:
        """Initialise the loader."""
        logger.info("CandidateLoader initialised")

    def load_from_csv(self, path: str) -> pl.DataFrame:
        """
        Load a raw candidate CSV file into a Polars DataFrame.

        Reads the CSV file, injects missing optional columns with defaults,
        and ensures candidate_id is cast to string.

        Args:
            path: Absolute or relative path to the CSV file.

        Returns:
            Polars DataFrame with all expected columns present.

        Raises:
            FileNotFoundError: If the CSV file does not exist.
            ValueError: If the CSV is empty or malformed.
        """
        import os
        if not os.path.exists(path):
            raise FileNotFoundError(f"CSV file not found: {path}")

        logger.info("Loading CSV from: %s", path)

        try:
            df = pl.read_csv(
                path,
                infer_schema_length=1000,
                null_values=["", "NULL", "null", "NA", "N/A", "nan", "NaN"],
                try_parse_dates=False,
                ignore_errors=True,
            )
        except Exception as exc:
            logger.error("Failed to read CSV %s: %s", path, exc)
            raise ValueError(f"Failed to read CSV file: {exc}") from exc

        if df.is_empty():
            raise ValueError(f"CSV file is empty: {path}")

        logger.info("Loaded %d rows × %d columns", df.height, df.width)

        # Inject missing optional columns with defaults
        existing_cols = set(df.columns)
        for col in OPTIONAL_COLUMNS:
            if col not in existing_cols:
                default_val = COLUMN_DEFAULTS.get(col)
                logger.debug("Injecting missing column '%s' with default %r", col, default_val)
                df = df.with_columns(pl.lit(default_val).alias(col))

        # Ensure candidate_id is string type
        if "candidate_id" in df.columns:
            df = df.with_columns(
                pl.col("candidate_id").cast(pl.Utf8).fill_null("UNKNOWN")
            )

        # Cast numeric columns safely
        numeric_float_cols = ["years_of_experience", "response_rate", "expected_salary"]
        numeric_int_cols = ["profile_views", "application_count", "last_active_days", "notice_period_days"]

        for col in numeric_float_cols:
            if col in df.columns:
                try:
                    df = df.with_columns(
                        pl.col(col).cast(pl.Float64, strict=False).fill_null(0.0)
                    )
                except Exception:
                    df = df.with_columns(pl.lit(0.0).alias(col))

        for col in numeric_int_cols:
            if col in df.columns:
                try:
                    df = df.with_columns(
                        pl.col(col).cast(pl.Int64, strict=False)
                    )
                except Exception:
                    df = df.with_columns(pl.lit(None).cast(pl.Int64).alias(col))

        logger.info("CSV loaded successfully: %d candidates", df.height)
        return df

    def load_csv(self, path: str) -> tuple[pl.DataFrame, dict[str, object]]:
        """
        Load candidate CSV and compute statistics.

        Args:
            path: Path to CSV file.

        Returns:
            Tuple of (DataFrame, stats_dict).
        """
        df = self.load_from_csv(path)
        stats = self.get_statistics(df)
        # Ensure 'total_rows' is present in stats dictionary as expected by pipeline
        stats["total_rows"] = stats.get("row_count", len(df))
        return df, stats

    def validate_schema(self, df: pl.DataFrame) -> tuple[bool, list[str]]:
        """
        Validate that the DataFrame has all required columns.

        Args:
            df: Polars DataFrame to validate.

        Returns:
            Tuple of (is_valid, issues_list).
            is_valid is True if all required columns are present.
            issues_list contains human-readable descriptions of problems found.
        """
        issues: list[str] = []
        existing_cols = set(df.columns)

        for col in REQUIRED_COLUMNS:
            if col not in existing_cols:
                issues.append(f"Missing required column: '{col}'")

        if df.is_empty():
            issues.append("DataFrame is empty — no candidates to process")

        # Check for duplicate candidate IDs
        if "candidate_id" in existing_cols:
            total = df.height
            unique = df["candidate_id"].n_unique()
            if unique < total:
                dupes = total - unique
                issues.append(f"Found {dupes} duplicate candidate_id values")

        is_valid = len(issues) == 0
        if is_valid:
            logger.info("Schema validation passed")
        else:
            logger.warning("Schema validation issues: %s", issues)

        return is_valid, issues

    def get_statistics(self, df: pl.DataFrame) -> dict[str, object]:
        """
        Compute basic statistics about the loaded dataset.

        Args:
            df: Loaded Polars DataFrame.

        Returns:
            Dictionary with row_count, column_count, missing_rates,
            and numeric summaries for key columns.
        """
        stats: dict[str, object] = {
            "row_count": df.height,
            "column_count": df.width,
            "columns": df.columns,
        }

        # Missing value rates per column
        missing_rates: dict[str, float] = {}
        for col in df.columns:
            null_count = df[col].null_count()
            missing_rates[col] = round(null_count / max(df.height, 1), 4)
        stats["missing_rates"] = missing_rates

        # Experience stats
        if "years_of_experience" in df.columns:
            exp_col = df["years_of_experience"].drop_nulls().cast(pl.Float64, strict=False)
            if exp_col.len() > 0:
                stats["experience_stats"] = {
                    "mean": round(float(exp_col.mean() or 0.0), 2),
                    "median": round(float(exp_col.median() or 0.0), 2),
                    "min": float(exp_col.min() or 0.0),
                    "max": float(exp_col.max() or 0.0),
                }

        # Availability status distribution
        if "availability_status" in df.columns:
            try:
                status_dist = (
                    df.group_by("availability_status")
                    .agg(pl.len().alias("count"))
                    .sort("count", descending=True)
                )
                stats["availability_distribution"] = {
                    row["availability_status"]: row["count"]
                    for row in status_dist.to_dicts()
                }
            except Exception:
                pass

        logger.debug("Dataset statistics: %s", stats)
        return stats
