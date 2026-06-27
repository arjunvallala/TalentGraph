"""
TalentGraph AI — BM25 Retrieval Engine

Performs Stage 1 lexical keyword search using BM25 to retrieve candidates
who match exact job description terms, skills, or job titles.
"""
from __future__ import annotations

from typing import List, Dict, Any, Tuple

from shared.config import settings
from shared.logging_setup import get_logger
from services.preprocessing.bm25_builder import BM25IndexBuilder
from services.preprocessing.feature_store import FeatureStore

logger = get_logger(__name__)


class BM25RetrievalEngine:
    """
    Retrieves candidate IDs using BM25 lexical keyword matching.
    """

    def __init__(self, db: FeatureStore) -> None:
        """Initialize the BM25 retrieval engine."""
        self.db = db
        self.index_builder = BM25IndexBuilder()
        self.index = None
        logger.info("BM25RetrievalEngine initialised")

    def load_index(self) -> None:
        """Load the BM25 index pickle file."""
        if self.index is None:
            self.index = self.index_builder.load_index(settings.bm25_index_path)

    def retrieve(self, query_tokens: List[str], top_k: int = 1500) -> List[str]:
        """
        Retrieve candidate IDs matching the tokenized query terms.

        Args:
            query_tokens: List of tokenized terms from the job description.
            top_k: Number of candidate profiles to retrieve.

        Returns:
            A list of candidate_ids ordered by descending BM25 score.
        """
        self.load_index()
        if self.index is None:
            logger.error("BM25 index not loaded. BM25 retrieval failed.")
            return []

        # Perform BM25 search
        results = self.index_builder.search(self.index, query_tokens, top_k)
        if not results:
            return []

        # Map document indices back to candidate_ids using database
        doc_indices = [res[0] for res in results]
        conn = self.db.connect()

        # Retrieve candidate IDs by embedding_id (which corresponds to doc_index)
        indices_str = ",".join(map(str, doc_indices))
        rows = conn.execute(
            f"SELECT candidate_id, embedding_id FROM candidates WHERE embedding_id IN ({indices_str})"
        ).fetchall()

        mapping = {row[1]: row[0] for row in rows}

        ordered_ids = [mapping[idx] for idx in doc_indices if idx in mapping]
        logger.info(f"Retrieved {len(ordered_ids)} candidate IDs via BM25 search")
        return ordered_ids
