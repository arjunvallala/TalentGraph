"""
TalentGraph AI — Application Configuration

Loads configuration from environment variables and YAML config files.
Uses pydantic-settings for typed, validated configuration.

Usage:
    from shared.config import settings
    print(settings.api_port)
    print(settings.embedding_model_name)
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application-wide settings.

    Values are loaded from (in priority order):
    1. Environment variables
    2. .env file
    3. Default values defined here
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    app_name: str = Field(default="TalentGraph AI")
    app_version: str = Field(default="0.1.0")
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # ── API ───────────────────────────────────────────────────────────────────
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_workers: int = Field(default=1)
    api_reload: bool = Field(default=True)
    api_cors_origins: str = Field(default="http://localhost:3000,http://localhost:5173")

    # ── Demo ──────────────────────────────────────────────────────────────────
    demo_mode: bool = Field(default=False)
    demo_data_path: str = Field(default="data/demo")

    # ── Data Paths ────────────────────────────────────────────────────────────
    data_raw_path: str = Field(default="data/raw")
    data_processed_path: str = Field(default="data/processed")
    data_indexes_path: str = Field(default="data/indexes")

    # ── DuckDB ────────────────────────────────────────────────────────────────
    duckdb_path: str = Field(default="data/processed/talentgraph.duckdb")

    # ── FAISS ─────────────────────────────────────────────────────────────────
    faiss_index_path: str = Field(default="data/indexes/candidates.faiss")
    faiss_metadata_path: str = Field(default="data/indexes/faiss_metadata.pkl")

    # ── BM25 ──────────────────────────────────────────────────────────────────
    bm25_index_path: str = Field(default="data/indexes/bm25_index.pkl")

    # ── Embedding ─────────────────────────────────────────────────────────────
    embedding_model_name: str = Field(default="all-MiniLM-L6-v2")
    embedding_model_path: str = Field(default="models/embeddings/all-MiniLM-L6-v2")
    embedding_batch_size: int = Field(default=64)
    embedding_dimension: int = Field(default=384)

    # ── Preprocessing ─────────────────────────────────────────────────────────
    preprocessing_checkpoint_path: str = Field(default="data/processed/.checkpoints")
    preprocessing_batch_size: int = Field(default=1000)
    preprocessing_max_workers: int = Field(default=4)

    # ── Ranking ───────────────────────────────────────────────────────────────
    ranking_stage1_top_k: int = Field(default=2000)
    ranking_stage2_top_k: int = Field(default=200)
    ranking_stage3_top_k: int = Field(default=100)
    ranking_final_top_k: int = Field(default=100)

    # ── Retrieval ─────────────────────────────────────────────────────────────
    semantic_top_k: int = Field(default=1500)
    bm25_top_k: int = Field(default=1500)
    hybrid_alpha: float = Field(default=0.6)

    # ── Confidence ────────────────────────────────────────────────────────────
    confidence_high_threshold: float = Field(default=0.75)
    confidence_low_threshold: float = Field(default=0.45)

    # ── Submission ────────────────────────────────────────────────────────────
    submission_output_path: str = Field(default="data/submission.csv")

    # ── Config ────────────────────────────────────────────────────────────────
    config_path: str = Field(default="configs")

    # ── Logging ───────────────────────────────────────────────────────────────
    log_file_path: str = Field(default="logs/talentgraph.log")
    log_rotation: str = Field(default="500 MB")
    log_retention: str = Field(default="10 days")

    @field_validator("app_env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        """Ensure environment is one of the allowed values."""
        allowed = {"development", "production", "test"}
        if v not in allowed:
            raise ValueError(f"app_env must be one of {allowed}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is valid."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return upper

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    def get_config_file(self, name: str) -> dict:
        """
        Load a YAML configuration file by name.

        Args:
            name: Config file name without extension (e.g., 'features').

        Returns:
            Parsed YAML content as a dictionary.

        Raises:
            FileNotFoundError: If the config file does not exist.
        """
        config_file = Path(self.config_path) / f"{name}.yaml"
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        with config_file.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def ensure_directories(self) -> None:
        """
        Create all required data directories if they don't exist.

        This should be called once at application startup.
        """
        directories = [
            self.data_raw_path,
            self.data_processed_path,
            self.data_indexes_path,
            self.preprocessing_checkpoint_path,
            self.demo_data_path,
            str(Path(self.log_file_path).parent),
            str(Path(self.duckdb_path).parent),
            str(Path(self.faiss_index_path).parent),
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached application settings singleton.

    Uses lru_cache to ensure settings are only loaded once per process.
    In tests, call get_settings.cache_clear() to reload settings.

    Returns:
        Validated Settings instance.
    """
    return Settings()


# Module-level singleton for convenience imports
settings = get_settings()
