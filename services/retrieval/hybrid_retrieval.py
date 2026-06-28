"""
TalentGraph AI — Hybrid Retrieval Engine

Performs Stage 1 hybrid retrieval, running both semantic (FAISS) and lexical (BM25)
searches and merging them using Reciprocal Rank Fusion (RRF) to output top-N candidates.
"""

from __future__ import annotations

from services.preprocessing.feature_store import FeatureStore
from services.retrieval.bm25_retrieval import BM25RetrievalEngine
from services.retrieval.semantic_retrieval import SemanticRetrievalEngine
from shared.constants import RRF_K, STAGE1_TOP_K
from shared.logging_setup import get_logger
from shared.utils.math_utils import reciprocal_rank_fusion

logger = get_logger(__name__)


class HybridRetrievalEngine:
    """
    Fuses semantic and keyword candidate lists into a single ranked list.
    """

    def __init__(self, db: FeatureStore) -> None:
        """Initialize the hybrid retrieval engine."""
        self.db = db
        self.semantic_engine = SemanticRetrievalEngine(db)
        self.bm25_engine = BM25RetrievalEngine(db)
        logger.info("HybridRetrievalEngine initialised")

    def retrieve(
        self,
        query_embedding: list[float],
        query_tokens: list[str],
        top_k: int = STAGE1_TOP_K,
    ) -> list[str]:
        """
        Run semantic and lexical retrievals, fuse lists with RRF, and truncate to top_k.

        Args:
            query_embedding: Dense float vector of the job description.
            query_tokens: Tokenized terms of the job description.
            top_k: Number of candidate IDs to return in fused list.

        Returns:
            A fused list of candidate_ids.
        """
        # Retrieve candidate IDs from semantic and lexical engines
        semantic_ids = self.semantic_engine.retrieve(query_embedding, top_k=STAGE1_TOP_K * 2)
        bm25_ids = self.bm25_engine.retrieve(query_tokens, top_k=STAGE1_TOP_K * 2)

        # Apply Reciprocal Rank Fusion
        fused_ids = reciprocal_rank_fusion([semantic_ids, bm25_ids], k=RRF_K)

        truncated = fused_ids[:top_k]
        logger.info(
            f"Hybrid retrieval finished: fused {len(fused_ids)} down to {len(truncated)} candidates"
        )
        return truncated
