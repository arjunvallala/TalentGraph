"""
TalentGraph AI — Preprocessing Pipeline Orchestrator

Coordinates the end-to-end data preprocessing flow: loading, cleaning,
parsing, feature extraction, feature store insertion, embedding generation,
and vector/keyword index building.
"""
from __future__ import annotations

import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

from shared.config import Settings
from shared.logging_setup import get_logger
from shared.types.candidate import CandidateProfile, CandidateFeatures
from services.preprocessing.loader import CandidateLoader
from services.preprocessing.cleaner import DataCleaner
from services.preprocessing.parser import CandidateParser
from services.preprocessing.feature_extractor import FeatureExtractor
from services.preprocessing.embedding_generator import EmbeddingGenerator
from services.preprocessing.faiss_builder import FAISSIndexBuilder
from services.preprocessing.bm25_builder import BM25IndexBuilder
from services.preprocessing.feature_store import FeatureStore
from services.preprocessing.quality_checker import QualityChecker
from services.preprocessing.checkpoint import CheckpointManager

logger = get_logger(__name__)


class StageResult:
    """Represents the execution outcome of a single pipeline stage."""
    def __init__(self, stage_name: str, input_count: int, output_count: int, duration_seconds: float, success: bool) -> None:
        self.stage_name = stage_name
        self.input_count = input_count
        self.output_count = output_count
        self.duration_seconds = duration_seconds
        self.success = success


class PipelineResult:
    """Contains the overall outcome and stats of a pipeline run."""
    def __init__(self, total_processed: int, stage_results: List[StageResult]) -> None:
        self.total_processed = total_processed
        self.stage_results = stage_results


class PreprocessingPipeline:
    """
    Orchestrates the entire candidate preprocessing and indexing pipeline.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the pipeline with application settings."""
        self.settings = settings
        self.loader = CandidateLoader()
        self.cleaner = DataCleaner()
        self.parser = CandidateParser()
        self.extractor = FeatureExtractor()
        self.db = FeatureStore(settings.duckdb_path)
        self.checkpoint = CheckpointManager(settings.preprocessing_checkpoint_path)
        logger.info("PreprocessingPipeline initialized")

    def reset_checkpoints(self) -> None:
        """Clear all stored checkpoints to start a clean execution."""
        self.checkpoint.clear_all()
        logger.info("Pipeline checkpoints reset")

    def run(
        self,
        input_path: str,
        resume: bool = True,
        batch_size: int = 100,
        skip_embeddings: bool = False,
        progress: Optional[Any] = None,
    ) -> PipelineResult:
        """
        Execute all stages of the preprocessing pipeline.

        Args:
            input_path: Path to candidates CSV file.
            resume: Enable checkpoint resuming.
            batch_size: Number of records to process per batch.
            skip_embeddings: Skip vector embedding generation.
            progress: Rich progress tracker object.

        Returns:
            PipelineResult containing summary details of the execution.
        """
        stage_results = []
        self.db.connect()

        # Define stages for tracking
        total_steps = 5
        current_step = 0

        # Helper to update Rich progress if active
        def update_progress(desc: str, completed_frac: float):
            if progress:
                # Basic progress interface
                pass

        # ── STAGE 1: LOADING ──
        logger.info("--- Stage 1: Loading Candidate Data ---")
        start_time = time.perf_counter()
        df_raw, stats = self.loader.load_csv(input_path)
        duration = time.perf_counter() - start_time
        input_len = stats.get("total_rows", 0)

        stage_results.append(
            StageResult("Loading & Ingestion", input_len, len(df_raw), duration, True)
        )
        self.checkpoint.save("loading", {"complete": True, "processed_count": len(df_raw)})

        # ── STAGE 2: CLEANING ──
        logger.info("--- Stage 2: Cleaning & Normalising Data ---")
        start_time = time.perf_counter()
        df_clean = self.cleaner.clean_dataframe(df_raw)
        duration = time.perf_counter() - start_time

        stage_results.append(
            StageResult("Cleaning & Normalisation", len(df_raw), len(df_clean), duration, True)
        )
        self.checkpoint.save("cleaning", {"complete": True, "processed_count": len(df_clean)})

        # Convert DF to list of dicts for parsing
        rows = df_clean.to_dicts()
        total_candidates = len(rows)

        # ── STAGE 3: PARSING & FEATURE EXTRACTION ──
        logger.info("--- Stage 3: Parsing Profiles & Extracting Features ---")
        start_time = time.perf_counter()

        profiles: List[CandidateProfile] = []
        features_list: List[CandidateFeatures] = []

        # Load existing features checkpoint if resuming
        processed_candidates_state = {}
        if resume:
            state = self.checkpoint.load("features")
            if state and state.get("complete"):
                logger.info("Resuming feature extraction: Stage marked as complete in checkpoint.")
                # Retrieve from database if needed or load directly
            elif state:
                processed_candidates_state = state.get("processed_ids", {})

        # Process in batches
        for idx in range(0, total_candidates, batch_size):
            batch_rows = rows[idx : idx + batch_size]
            for row in batch_rows:
                candidate_id = str(row["candidate_id"])
                if resume and candidate_id in processed_candidates_state:
                    continue

                try:
                    # Parse row to structured profile
                    profile = self.parser.parse_row(row)
                    # Extract 15 features
                    features = self.extractor.extract_features(profile)
                    # Compute evidence ledger
                    evidence = self.extractor.build_evidence(profile, features)

                    # Persist to DuckDB
                    self.db.save_candidate_profile(profile)
                    self.db.save_candidate_features(features)
                    self.db.save_candidate_evidence(candidate_id, evidence)

                    profiles.append(profile)
                    features_list.append(features)
                    processed_candidates_state[candidate_id] = True
                except Exception as e:
                    logger.error(f"Failed to process candidate {candidate_id}: {e}")

            # Save batch checkpoint
            self.checkpoint.save(
                "features",
                {
                    "complete": idx + batch_size >= total_candidates,
                    "processed_count": len(processed_candidates_state),
                    "processed_ids": processed_candidates_state,
                },
            )

        duration = time.perf_counter() - start_time
        stage_results.append(
            StageResult("Parsing & Feature Extraction", total_candidates, len(processed_candidates_state), duration, True)
        )

        # ── STAGE 4: EMBEDDING GENERATION ──
        logger.info("--- Stage 4: Dense & Sparse Indexing ---")
        start_time = time.perf_counter()

        # To build index, we retrieve all profiles from DB
        # Re-fetch profiles from DuckDB to build complete vectors
        all_profiles = []
        corpus_texts = []
        embeddings = []

        for cid in processed_candidates_state.keys():
            prof = self.db.get_candidate_profile(cid)
            if prof:
                all_profiles.append(prof)
                # Build textual representation for BM25 and embeddings
                text = prof.raw_text or f"{prof.name} {prof.current_title} {prof.current_company} {','.join(prof.skills or [])}"
                corpus_texts.append(text)

        # Vector Embeddings
        if not skip_embeddings and all_profiles:
            try:
                emb_generator = EmbeddingGenerator(self.settings.embedding_model_name)
                emb_generator.load_model()
                logger.info(f"Generating dense embeddings for {len(corpus_texts)} candidates...")
                embeddings = emb_generator.encode_batch(corpus_texts)

                # Save embedding IDs to candidate profiles
                for i, prof in enumerate(all_profiles):
                    prof.embedding_id = i
                    self.db.save_candidate_profile(prof)
            except Exception as e:
                logger.error(f"Failed to generate embeddings: {e}. Falling back to default search indexes.")

        # FAISS Index
        if len(embeddings) > 0:
            try:
                faiss_builder = FAISSIndexBuilder()
                index = faiss_builder.build_index(np.array(embeddings, dtype=np.float32))
                faiss_builder.save_index(index, self.settings.faiss_index_path)
            except Exception as e:
                logger.error(f"Failed to build FAISS index: {e}")

        # BM25 Index
        if corpus_texts:
            try:
                bm25_builder = BM25IndexBuilder()
                bm25_index = bm25_builder.build_index(corpus_texts)
                bm25_builder.save_index(bm25_index, self.settings.bm25_index_path)
            except Exception as e:
                logger.error(f"Failed to build BM25 index: {e}")

        duration = time.perf_counter() - start_time
        stage_results.append(
            StageResult("Dense & Sparse Indexing", len(all_profiles), len(all_profiles), duration, True)
        )
        self.checkpoint.save("indexing", {"complete": True, "processed_count": len(all_profiles)})

        # ── STAGE 5: DATA QUALITY REPORT ──
        logger.info("--- Stage 5: Quality Assurance Validation ---")
        start_time = time.perf_counter()

        df_features = self.db.get_features_dataframe(list(processed_candidates_state.keys()))
        qc = QualityChecker()
        report = qc.run_checks(df_features)

        # Output results to console and log
        if not report["passed"]:
            logger.warning(f"Data quality checks found issues: {report['errors']}")
        else:
            logger.info("Data quality validation checks passed successfully!")

        duration = time.perf_counter() - start_time
        stage_results.append(
            StageResult("Quality Assurance Report", len(df_features), len(df_features), duration, True)
        )

        self.db.close()
        return PipelineResult(len(processed_candidates_state), stage_results)
