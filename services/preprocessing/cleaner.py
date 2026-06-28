"""
TalentGraph AI — Data Cleaner

Responsible for cleaning and normalising raw candidate DataFrames:
deduplication, skill normalisation, null filling, and candidate ID validation.

All operations are non-destructive in the sense that they return new
Polars DataFrames — the original is never modified in-place.
"""

from __future__ import annotations

import re

import polars as pl

from shared.logging_setup import get_logger

logger = get_logger(__name__)

# Skill normalisation mappings (common aliases → canonical name)
_SKILL_ALIASES: dict[str, str] = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "rl": "reinforcement learning",
    "k8s": "kubernetes",
    "tf": "tensorflow",
    "pt": "pytorch",
    "pg": "postgresql",
    "psql": "postgresql",
    "mysql": "mysql",
    "mongo": "mongodb",
    "es": "elasticsearch",
    "sk-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "xgb": "xgboost",
    "lgbm": "lightgbm",
    "hf": "hugging face",
    "gcp": "google cloud",
    "aws": "aws",
    "az": "azure",
    "ci/cd": "ci/cd",
    "dsa": "data structures",
    "oop": "object-oriented programming",
    "fp": "functional programming",
    "api": "rest api",
    "restful": "rest api",
    "rest": "rest api",
    "sql": "sql",
    "nosql": "nosql",
    "vcs": "git",
    "react.js": "react",
    "reactjs": "react",
    "vue.js": "vue",
    "vuejs": "vue",
    "node.js": "node.js",
    "nodejs": "node.js",
    "next.js": "next.js",
    "nextjs": "next.js",
    "spring boot": "spring boot",
    "springboot": "spring boot",
    "data science": "data science",
    "ds": "data science",
    "bi": "business intelligence",
    "powerbi": "power bi",
    "power bi": "power bi",
    "tableau": "tableau",
    "looker": "looker",
    "ai": "artificial intelligence",
    "gen ai": "generative ai",
    "genai": "generative ai",
    "llm": "large language model",
    "rag": "retrieval augmented generation",
}


class DataCleaner:
    """
    Cleans and normalises a raw candidate Polars DataFrame.

    Operations performed:
    - Deduplication by candidate_id (keeps first occurrence)
    - Skill string normalisation (alias expansion, lowercase, dedup)
    - Missing value filling with appropriate defaults
    - candidate_id format validation and sanitisation
    - Text field trimming and encoding fixes

    Example:
        cleaner = DataCleaner()
        df_clean = cleaner.clean_dataframe(df_raw)
    """

    def __init__(self) -> None:
        """Initialise the data cleaner."""
        logger.info("DataCleaner initialised")

    def clean_dataframe(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Apply the full cleaning pipeline to a raw DataFrame.

        Steps:
        1. Validate and sanitise candidate IDs
        2. Deduplicate by candidate_id
        3. Fill missing values
        4. Normalise string fields (trim, strip)
        5. Clamp numeric fields to valid ranges

        Args:
            df: Raw Polars DataFrame from the loader.

        Returns:
            Cleaned Polars DataFrame.
        """
        logger.info("Starting dataframe cleaning: %d rows", df.height)

        df = self.validate_candidate_ids(df)
        df = self.deduplicate(df)
        df = self.fill_missing_values(df)
        df = self._trim_string_columns(df)
        df = self._clamp_numeric_columns(df)

        logger.info("Cleaning complete: %d rows remaining", df.height)
        return df

    def deduplicate(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Remove duplicate rows by candidate_id, keeping the first occurrence.

        Args:
            df: Input DataFrame.

        Returns:
            DataFrame with unique candidate_ids.
        """
        original_count = df.height
        df = df.unique(subset=["candidate_id"], keep="first", maintain_order=True)
        removed = original_count - df.height
        if removed > 0:
            logger.warning("Removed %d duplicate candidate_id rows", removed)
        return df

    def normalize_skills(self, skills: list[str]) -> list[str]:
        """
        Normalise a list of skill strings.

        Operations:
        - Strip whitespace
        - Lowercase
        - Expand known aliases
        - Remove empty strings and duplicates

        Args:
            skills: Raw skill list.

        Returns:
            Normalised, deduplicated skill list.
        """
        normalised: list[str] = []
        seen: set[str] = set()
        for skill in skills:
            if not skill or not isinstance(skill, str):
                continue
            clean = skill.strip().lower()
            clean = re.sub(r"\s+", " ", clean)
            # Expand known aliases
            clean = _SKILL_ALIASES.get(clean, clean)
            if clean and clean not in seen and len(clean) >= 1:
                normalised.append(clean)
                seen.add(clean)
        return normalised[:100]  # cap at 100 skills

    def fill_missing_values(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Fill null/missing values with sensible defaults.

        Args:
            df: Input DataFrame.

        Returns:
            DataFrame with nulls replaced by defaults.
        """
        # String column defaults
        str_defaults: dict[str, str] = {
            "name": "",
            "email": "",
            "phone": "",
            "current_title": "",
            "current_company": "",
            "skills": "",
            "education": "",
            "work_history": "",
            "certifications": "",
            "languages": "",
            "summary": "",
            "location": "",
            "availability_status": "unknown",
        }

        # Numeric float defaults
        float_defaults: dict[str, float] = {
            "years_of_experience": 0.0,
            "response_rate": 0.0,
        }

        # Numeric int defaults
        int_defaults: dict[str, int] = {
            "profile_views": 0,
            "application_count": 0,
        }

        expressions = []
        for col, default in str_defaults.items():
            if col in df.columns:
                expressions.append(pl.col(col).cast(pl.Utf8).fill_null(default))

        for col, default in float_defaults.items():
            if col in df.columns:
                expressions.append(pl.col(col).cast(pl.Float64, strict=False).fill_null(default))

        for col, default in int_defaults.items():
            if col in df.columns:
                expressions.append(pl.col(col).cast(pl.Int64, strict=False).fill_null(default))

        if expressions:
            df = df.with_columns(expressions)

        return df

    def validate_candidate_ids(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Validate and sanitise candidate_id values.

        - Casts to string
        - Removes leading/trailing whitespace
        - Drops rows where candidate_id is null or empty
        - Reports dropped count

        Args:
            df: Input DataFrame.

        Returns:
            DataFrame with valid candidate_ids only.
        """
        if "candidate_id" not in df.columns:
            logger.error("No candidate_id column found — cannot validate IDs")
            return df

        df = df.with_columns(
            pl.col("candidate_id").cast(pl.Utf8).str.strip_chars().alias("candidate_id")
        )

        original_count = df.height
        df = df.filter(
            pl.col("candidate_id").is_not_null()
            & (pl.col("candidate_id") != "")
            & (pl.col("candidate_id") != "UNKNOWN")
        )
        dropped = original_count - df.height
        if dropped > 0:
            logger.warning("Dropped %d rows with invalid candidate_id", dropped)

        return df

    def _trim_string_columns(self, df: pl.DataFrame) -> pl.DataFrame:
        """Strip leading/trailing whitespace from all string columns."""
        str_cols = [col for col in df.columns if df[col].dtype in (pl.Utf8, pl.String)]
        if not str_cols:
            return df
        return df.with_columns([pl.col(c).str.strip_chars() for c in str_cols])

    def _clamp_numeric_columns(self, df: pl.DataFrame) -> pl.DataFrame:
        """Clamp numeric columns to valid ranges."""
        expressions = []

        if "years_of_experience" in df.columns:
            expressions.append(pl.col("years_of_experience").clip(0.0, 50.0))
        if "response_rate" in df.columns:
            expressions.append(pl.col("response_rate").clip(0.0, 1.0))
        if "profile_views" in df.columns:
            expressions.append(
                pl.col("profile_views").cast(pl.Int64, strict=False).fill_null(0).clip(0, 100_000)
            )
        if "application_count" in df.columns:
            expressions.append(
                pl.col("application_count")
                .cast(pl.Int64, strict=False)
                .fill_null(0)
                .clip(0, 10_000)
            )
        if "notice_period_days" in df.columns:
            expressions.append(
                pl.col("notice_period_days").cast(pl.Int64, strict=False).clip(0, 365)
            )

        if expressions:
            df = df.with_columns(expressions)

        return df
