"""
TalentGraph AI — BM25 Index Builder

Builds, saves, loads, and searches BM25 keyword indexes for lexical retrieval.
Uses rank_bm25's BM25Okapi implementation with TF-IDF-like scoring.

BM25 retrieval complements semantic search in the hybrid retrieval stage
by capturing exact keyword matches (skill names, job titles, certifications).
"""
from __future__ import annotations

import numpy as np

from shared.logging_setup import get_logger
from shared.utils.file_utils import load_pickle, save_pickle

logger = get_logger(__name__)


class BM25IndexBuilder:
    """
    Builds and manages BM25 keyword indexes using rank_bm25.

    The BM25 index is built over tokenised candidate profile texts
    and searched with tokenised job description queries.

    Example:
        builder = BM25IndexBuilder()
        index = builder.build_index(corpus_texts)
        builder.save_index(index, "data/indexes/bm25_index.pkl")
        results = builder.search(index, query_tokens, top_k=1000)
    """

    def __init__(self) -> None:
        """Initialise the BM25 index builder."""
        logger.info("BM25IndexBuilder initialised")

    def build_index(self, corpus: list[str]) -> BM25Okapi:  # type: ignore
        """
        Build a BM25Okapi index from a list of document strings.

        Each string is tokenised before indexing.

        Args:
            corpus: List of document strings (one per candidate profile).

        Returns:
            Fitted BM25Okapi index.

        Raises:
            RuntimeError: If rank_bm25 is not installed.
            ValueError: If corpus is empty.
        """
        try:
            from rank_bm25 import BM25Okapi
        except ImportError as exc:
            raise RuntimeError(
                "rank_bm25 is required. Install with: pip install rank-bm25"
            ) from exc

        if not corpus:
            raise ValueError("Corpus is empty — cannot build BM25 index")

        logger.info("Building BM25 index for %d documents", len(corpus))

        from shared.utils.text_utils import tokenize_for_bm25
        tokenized = [tokenize_for_bm25(doc) for doc in corpus]

        # Replace empty token lists with placeholder to avoid BM25 edge cases
        tokenized = [
            tokens if tokens else ["unknown"]
            for tokens in tokenized
        ]

        index = BM25Okapi(tokenized)
        logger.info("BM25 index built successfully: %d documents", len(corpus))
        return index

    def save_index(self, index: BM25Okapi, path: str) -> None:  # type: ignore
        """
        Save the BM25 index to disk using pickle.

        Args:
            index: Fitted BM25Okapi index.
            path: Destination file path.
        """
        save_pickle(index, path)
        logger.info("BM25 index saved to: %s", path)

    def load_index(self, path: str) -> BM25Okapi:  # type: ignore
        """
        Load a BM25 index from disk.

        Args:
            path: Source file path.

        Returns:
            Loaded BM25Okapi index.

        Raises:
            FileNotFoundError: If the index file does not exist.
        """
        index = load_pickle(path)
        logger.info("BM25 index loaded from: %s", path)
        return index

    def search(
        self,
        index: BM25Okapi,  # type: ignore
        query_tokens: list[str],
        top_k: int,
    ) -> list[tuple[int, float]]:
        """
        Search the BM25 index for the most relevant documents.

        Args:
            index: Fitted BM25Okapi index.
            query_tokens: Tokenised query (list of terms).
            top_k: Number of top results to return.

        Returns:
            List of (doc_index, normalized_score) tuples, sorted descending.
            doc_index is the 0-based position in the original corpus.
        """
        if not query_tokens:
            logger.warning("Empty query tokens — returning empty BM25 results")
            return []

        try:
            raw_scores = index.get_scores(query_tokens)
        except Exception as exc:
            logger.error("BM25 search error: %s", exc)
            return []

        normalized = self.normalize_scores(raw_scores)
        top_k = min(top_k, len(normalized))

        # Get top-k indices by score
        top_indices = np.argsort(normalized)[::-1][:top_k]
        results = [
            (int(idx), float(normalized[idx]))
            for idx in top_indices
            if normalized[idx] > 0
        ]

        return results

    def normalize_scores(self, raw_scores: np.ndarray) -> np.ndarray:
        """
        Normalize BM25 scores to [0.0, 1.0] using min-max normalisation.

        Args:
            raw_scores: Raw BM25 score array.

        Returns:
            Normalised score array in [0.0, 1.0].
        """
        if len(raw_scores) == 0:
            return raw_scores

        min_score = raw_scores.min()
        max_score = raw_scores.max()

        if max_score - min_score < 1e-8:
            return np.zeros_like(raw_scores, dtype=np.float32)

        normalised = (raw_scores - min_score) / (max_score - min_score)
        return normalised.astype(np.float32)
