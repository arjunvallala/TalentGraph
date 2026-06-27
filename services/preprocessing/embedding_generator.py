"""
TalentGraph AI — Embedding Generator

Generates dense vector embeddings for candidate profiles and job descriptions
using SentenceTransformers. Supports batch encoding for efficiency.

Embeddings power Stage 1 semantic retrieval via FAISS index search.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import numpy as np

from shared.config import settings
from shared.constants import EMBEDDING_BATCH_SIZE, EMBEDDING_DIMENSION
from shared.logging_setup import get_logger
from shared.types.candidate import CandidateProfile
from shared.types.job import JobRaw
from shared.utils.text_utils import build_candidate_text

logger = get_logger(__name__)


class EmbeddingGenerator:
    """
    Generates semantic embeddings using SentenceTransformers.

    Uses the all-MiniLM-L6-v2 model (384-dimensional) by default.
    Supports local model caching for offline operation.

    Example:
        generator = EmbeddingGenerator()
        generator.load_model()
        embeddings = generator.encode_batch(texts)
    """

    def __init__(self, model_name: str = settings.embedding_model_name) -> None:
        """
        Initialise the embedding generator.

        Args:
            model_name: SentenceTransformer model name or local path.
        """
        self.model_name = model_name
        self.model_path = settings.embedding_model_path
        self._model = None
        self._dimension: int = EMBEDDING_DIMENSION
        logger.info("EmbeddingGenerator initialised with model: %s", model_name)

    def load_model(self) -> None:
        """
        Load the SentenceTransformer model from local path or download.

        Tries local model path first (for offline operation), then falls
        back to downloading from HuggingFace Hub.

        Raises:
            RuntimeError: If model cannot be loaded from either source.
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is required. Install with: "
                "pip install sentence-transformers"
            ) from exc

        local_path = Path(self.model_path)
        if local_path.exists():
            logger.info("Loading embedding model from local path: %s", local_path)
            try:
                self._model = SentenceTransformer(str(local_path))
                logger.info("Local model loaded successfully")
                return
            except Exception as exc:
                logger.warning(
                    "Failed to load local model from %s: %s. Trying download.",
                    local_path, exc
                )

        # Download from HuggingFace
        logger.info("Downloading embedding model: %s", self.model_name)
        try:
            self._model = SentenceTransformer(self.model_name)
            logger.info("Model downloaded and loaded successfully")

            # Save locally for future offline use
            try:
                local_path.mkdir(parents=True, exist_ok=True)
                self._model.save(str(local_path))
                logger.info("Model saved to: %s", local_path)
            except Exception as save_exc:
                logger.warning("Could not save model locally: %s", save_exc)

        except Exception as exc:
            raise RuntimeError(
                f"Failed to load embedding model '{self.model_name}': {exc}"
            ) from exc

    def _ensure_model_loaded(self) -> None:
        """Ensure model is loaded, loading it if necessary."""
        if self._model is None:
            self.load_model()

    def encode_batch(
        self,
        texts: List[str],
        batch_size: int = EMBEDDING_BATCH_SIZE,
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        Encode a list of texts into dense embeddings.

        Args:
            texts: List of text strings to encode.
            batch_size: Number of texts per batch (memory/speed tradeoff).
            show_progress: Whether to show tqdm progress bar.

        Returns:
            Numpy array of shape (len(texts), embedding_dim), float32.
            Returns zero vectors for empty texts.
        """
        self._ensure_model_loaded()

        if not texts:
            return np.zeros((0, self._dimension), dtype=np.float32)

        # Replace empty/None texts with placeholder
        clean_texts = [
            t if t and t.strip() else "unknown candidate profile"
            for t in texts
        ]

        logger.info("Encoding %d texts in batches of %d", len(clean_texts), batch_size)

        try:
            embeddings = self._model.encode(
                clean_texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
                normalize_embeddings=True,  # L2 normalization for cosine similarity
            )
            logger.info("Encoding complete: shape=%s", embeddings.shape)
            return embeddings.astype(np.float32)
        except Exception as exc:
            logger.error("Batch encoding failed: %s", exc, exc_info=True)
            return np.zeros((len(texts), self._dimension), dtype=np.float32)

    def encode_single(self, text: str) -> np.ndarray:
        """
        Encode a single text string into a dense embedding.

        Args:
            text: Text to encode.

        Returns:
            1D numpy array of shape (embedding_dim,), float32.
        """
        result = self.encode_batch([text or "unknown"], batch_size=1)
        return result[0] if result.shape[0] > 0 else np.zeros(self._dimension, dtype=np.float32)

    def encode_candidates(self, profiles: List[CandidateProfile]) -> np.ndarray:
        """
        Encode a list of CandidateProfile instances into embeddings.

        Builds embedding text from each profile using build_candidate_text().

        Args:
            profiles: List of CandidateProfile instances.

        Returns:
            Numpy array of shape (len(profiles), embedding_dim), float32.
        """
        if not profiles:
            return np.zeros((0, self._dimension), dtype=np.float32)

        logger.info("Building embedding texts for %d candidates", len(profiles))
        texts = []
        for profile in profiles:
            try:
                text = build_candidate_text(profile)
                if not text.strip():
                    text = f"{profile.current_title or ''} {' '.join(profile.skills[:10])}"
                texts.append(text)
            except Exception as exc:
                logger.debug("Failed to build text for %s: %s", profile.candidate_id, exc)
                texts.append("unknown candidate profile")

        return self.encode_batch(texts)

    def encode_job(self, job_raw: JobRaw) -> np.ndarray:
        """
        Encode a JobRaw instance into a dense embedding.

        Uses the full raw_text (title + description).

        Args:
            job_raw: Raw job description.

        Returns:
            1D numpy array of shape (embedding_dim,), float32.
        """
        text = job_raw.raw_text or f"{job_raw.title} {job_raw.description}"
        return self.encode_single(text)

    def save_embeddings(self, embeddings: np.ndarray, path: str) -> None:
        """
        Save embeddings to disk in numpy format.

        Args:
            embeddings: Numpy array to save.
            path: Destination file path (e.g., "data/processed/embeddings.npy").
        """
        from pathlib import Path
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        np.save(str(p), embeddings)
        logger.info("Saved embeddings to %s: shape=%s", p, embeddings.shape)

    def load_embeddings(self, path: str) -> np.ndarray:
        """
        Load embeddings from disk.

        Args:
            path: Source file path.

        Returns:
            Loaded numpy array.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        from pathlib import Path
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Embeddings file not found: {p}")
        embeddings = np.load(str(p))
        logger.info("Loaded embeddings from %s: shape=%s", p, embeddings.shape)
        return embeddings
