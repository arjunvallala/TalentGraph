"""
TalentGraph AI — FAISS Index Builder

Builds, saves, loads, and searches FAISS indexes for semantic retrieval.
Uses IndexFlatIP (inner product) on L2-normalised embeddings,
which is equivalent to cosine similarity search.

For large corpora (>100k candidates), switches to IVF for efficiency.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from shared.logging_setup import get_logger

logger = get_logger(__name__)

# Threshold for switching from exact to approximate search
_IVF_THRESHOLD = 50_000
_IVF_NLIST = 256  # Number of Voronoi cells
_IVF_NPROBE = 32  # Cells to search at query time


class FAISSIndexBuilder:
    """
    Builds and manages FAISS indexes for dense vector retrieval.

    Uses IndexFlatIP (cosine similarity via L2-normalized vectors) for
    small corpora, and IVF+Flat for large corpora (>50k candidates).

    Example:
        builder = FAISSIndexBuilder()
        index = builder.build_index(embeddings)
        builder.save_index(index, "data/indexes/candidates.faiss")
        distances, indices = builder.search(index, query_vec, top_k=100)
    """

    def __init__(self) -> None:
        """Initialise the FAISS index builder."""
        logger.info("FAISSIndexBuilder initialised")

    def build_index(self, embeddings: np.ndarray) -> faiss.Index:  # type: ignore
        """
        Build a FAISS index from a numpy embedding matrix.

        For small corpora (< 50k): uses exact IndexFlatIP search.
        For large corpora (≥ 50k): uses IVF+Flat approximate search.

        Args:
            embeddings: Float32 array of shape (n_candidates, embedding_dim).
                        Must be L2-normalised for cosine similarity.

        Returns:
            Built FAISS index ready for searching.

        Raises:
            RuntimeError: If faiss is not installed.
            ValueError: If embeddings array is empty or has wrong shape.
        """
        try:
            import faiss
        except ImportError as exc:
            raise RuntimeError(
                "faiss-cpu is required. Install with: pip install faiss-cpu"
            ) from exc

        if embeddings is None or len(embeddings) == 0:
            raise ValueError("Embeddings array is empty — cannot build FAISS index")

        if embeddings.ndim != 2:
            raise ValueError(f"Embeddings must be 2D array, got shape: {embeddings.shape}")

        embeddings = embeddings.astype(np.float32)
        n, dim = embeddings.shape
        logger.info("Building FAISS index: %d vectors × %d dims", n, dim)

        # Ensure L2 normalization for cosine similarity
        faiss.normalize_L2(embeddings)

        if n < _IVF_THRESHOLD:
            # Exact search — best for smaller corpora
            index = faiss.IndexFlatIP(dim)
            index.add(embeddings)
            logger.info("Built IndexFlatIP: %d vectors", index.ntotal)
        else:
            # Approximate search — faster for large corpora
            nlist = min(_IVF_NLIST, n // 39)  # FAISS recommends 39× vectors per cell
            quantizer = faiss.IndexFlatIP(dim)
            index = faiss.IndexIVFFlat(quantizer, dim, nlist, faiss.METRIC_INNER_PRODUCT)
            index.train(embeddings)
            index.add(embeddings)
            index.nprobe = _IVF_NPROBE
            logger.info(
                "Built IndexIVFFlat: %d vectors, nlist=%d, nprobe=%d",
                index.ntotal,
                nlist,
                _IVF_NPROBE,
            )

        return index

    def save_index(self, index: faiss.Index, path: str) -> None:  # type: ignore
        """
        Save a FAISS index to disk.

        Args:
            index: FAISS index to save.
            path: Destination file path.
        """
        try:
            import faiss
        except ImportError as exc:
            raise RuntimeError("faiss-cpu is required.") from exc

        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(p))
        logger.info("FAISS index saved to: %s (%d vectors)", p, index.ntotal)

    def load_index(self, path: str) -> faiss.Index:  # type: ignore
        """
        Load a FAISS index from disk.

        Args:
            path: Source file path.

        Returns:
            Loaded FAISS index.

        Raises:
            FileNotFoundError: If the index file does not exist.
        """
        try:
            import faiss
        except ImportError as exc:
            raise RuntimeError("faiss-cpu is required.") from exc

        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"FAISS index not found: {p}")

        index = faiss.read_index(str(p))
        logger.info("Loaded FAISS index from: %s (%d vectors)", p, index.ntotal)
        return index

    def search(
        self,
        index: faiss.Index,  # type: ignore
        query: np.ndarray,
        top_k: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Search the FAISS index for the most similar vectors.

        Args:
            index: Built FAISS index.
            query: Query vector of shape (embedding_dim,) or (1, embedding_dim).
            top_k: Number of nearest neighbors to retrieve.

        Returns:
            Tuple of (distances, indices):
                - distances: float32 array of shape (1, top_k) — similarity scores
                - indices: int64 array of shape (1, top_k) — vector indices
        """
        try:
            import faiss
        except ImportError as exc:
            raise RuntimeError("faiss-cpu is required.") from exc

        query = query.astype(np.float32)
        if query.ndim == 1:
            query = query.reshape(1, -1)

        # Ensure query is L2-normalized
        faiss.normalize_L2(query)

        top_k = min(top_k, index.ntotal)
        distances, indices = index.search(query, top_k)
        return distances, indices
