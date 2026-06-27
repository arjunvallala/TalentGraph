"""
TalentGraph AI — Semantic Retrieval Engine

Performs Stage 1 dense vector search using FAISS to retrieve candidates
whose profiles are semantically similar to the job description.
"""
from __future__ import annotations

from typing import List, Dict, Any, Tuple
import numpy as np

from shared.config import settings
from shared.logging_setup import get_logger
from services.preprocessing.faiss_builder import FAISSIndexBuilder
from services.preprocessing.feature_store import FeatureStore

logger = get_logger(__name__)


class SemanticRetrievalEngine:
    """
    Retrieves candidate IDs using FAISS dense vector similarity.
    """

    def __init__(self, db: FeatureStore) -> None:
        """Initialize semantic retrieval engine."""
        self.db = db
        self.index_builder = FAISSIndexBuilder()
        self.index = None
        logger.info("SemanticRetrievalEngine initialised")

    def load_index(self) -> None:
        """Load the FAISS index from disk."""
        if self.index is None:
            self.index = self.index_builder.load_index(settings.faiss_index_path)

    def retrieve(self, query_embedding: List[float], top_k: int = 1500) -> List[str]:
        """
        Retrieve candidate IDs matching the query embedding.

        Args:
            query_embedding: Dense float vector representing the job description.
            top_k: Number of candidate profiles to retrieve.

        Returns:
            A list of candidate_ids ordered by descending similarity score.
        """
        self.load_index()
        if self.index is None:
            logger.error("FAISS index not loaded. Semantic retrieval failed.")
            return []

        query_vec = np.array(query_embedding, dtype=np.float32)
        distances, indices = self.index_builder.search(self.index, query_vec, top_k)

        # Map FAISS row indices back to candidate_ids using database
        idx_list = indices[0].tolist()
        # Filter out negative index padding (if any)
        idx_list = [int(i) for i in idx_list if i >= 0]
        if not idx_list:
            return []

        # DuckDB query to map embedding_id to candidate_id
        conn = self.db.connect()
        # Ensure we maintain FAISS rank order
        ids_in_str = ",".join(map(str, idx_list))
        rows = conn.execute(
            f"SELECT candidate_id, embedding_id FROM candidates WHERE embedding_id IN ({ids_in_str})"
        ).fetchall()

        # Map embedding_id -> candidate_id
        mapping = {row[1]: row[0] for row in rows}

        # Return ordered candidate_ids matching the index order
        ordered_ids = [mapping[idx] for idx in idx_list if idx in mapping]
        logger.info(f"Retrieved {len(ordered_ids)} candidate IDs via semantic search")
        return ordered_ids
