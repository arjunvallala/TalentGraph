"""
TalentGraph AI — Mathematical Utilities

Provides score normalisation, aggregation, and ranking utilities
used throughout the scoring and ranking pipeline.

All functions are deterministic, numerically stable, and produce
scores in [0.0, 1.0] unless explicitly documented otherwise.
"""
from __future__ import annotations

import math
from typing import Dict, List

import numpy as np

from shared.logging_setup import get_logger

logger = get_logger(__name__)

EPSILON: float = 1e-8


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Divide numerator by denominator, returning default if denominator is zero.

    Args:
        numerator: Dividend value.
        denominator: Divisor value.
        default: Value to return when denominator is zero or near-zero.

    Returns:
        Division result, or default if denominator ≈ 0.
    """
    if abs(denominator) < EPSILON:
        return default
    return numerator / denominator


def normalize_minmax(value: float, min_val: float, max_val: float) -> float:
    """
    Apply min-max normalisation to map value into [0.0, 1.0].

    Args:
        value: Raw value to normalise.
        min_val: Minimum of the range.
        max_val: Maximum of the range.

    Returns:
        Normalised float in [0.0, 1.0]. Returns 0.0 if range is zero.
    """
    if abs(max_val - min_val) < EPSILON:
        return 0.0
    normalised = (value - min_val) / (max_val - min_val)
    return float(clip(normalised))


def normalize_log(value: float, max_val: float = 30.0) -> float:
    """
    Apply logarithmic normalisation for diminishing-returns scaling.

    Useful for years of experience: 1 year vs 5 years matters a lot,
    but 20 years vs 25 years matters much less.

    Formula: log(1 + value) / log(1 + max_val)

    Args:
        value: Raw value (e.g., years of experience). Must be ≥ 0.
        max_val: Maximum expected value (normalisation ceiling).

    Returns:
        Log-normalised float in [0.0, 1.0].
    """
    value = max(0.0, value)
    max_val = max(max_val, 1.0)
    result = math.log1p(value) / math.log1p(max_val)
    return float(clip(result))


def clip(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """
    Clip value to [min_val, max_val].

    Args:
        value: Value to clip.
        min_val: Lower bound (default 0.0).
        max_val: Upper bound (default 1.0).

    Returns:
        Clipped float.
    """
    return float(max(min_val, min(max_val, value)))


def weighted_average(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    """
    Compute weighted average of scores using provided weights.

    Missing keys in scores use value 0.0. Missing keys in weights
    use weight 0.0 (effectively excluded). Weights need not sum to 1.0
    — they are normalised internally.

    Args:
        scores: Map of feature_name → score [0, 1].
        weights: Map of feature_name → weight (non-negative).

    Returns:
        Weighted average float in [0.0, 1.0].
    """
    total_weight = 0.0
    weighted_sum = 0.0
    for key, weight in weights.items():
        if weight < 0:
            continue
        score = scores.get(key, 0.0)
        weighted_sum += float(score) * float(weight)
        total_weight += float(weight)
    return clip(safe_divide(weighted_sum, total_weight, default=0.0))


def reciprocal_rank_fusion(rank_lists: List[List[str]], k: int = 60) -> List[str]:
    """
    Combine multiple ranked candidate lists using Reciprocal Rank Fusion.

    RRF score for each item = Σ 1 / (k + rank_i) across all lists.
    Items appearing in more lists and at higher ranks score higher.

    Args:
        rank_lists: List of candidate_id lists, each sorted best-first.
        k: RRF smoothing constant (default 60 per the original paper).

    Returns:
        Merged list of candidate_ids sorted by descending RRF score.
    """
    rrf_scores: Dict[str, float] = {}
    for ranked_list in rank_lists:
        for rank_idx, candidate_id in enumerate(ranked_list):
            rank = rank_idx + 1  # 1-indexed
            rrf_scores[candidate_id] = rrf_scores.get(candidate_id, 0.0) + 1.0 / (k + rank)
    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return [item[0] for item in sorted_items]


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute cosine similarity between two dense vectors.

    Args:
        a: First vector (1D numpy array).
        b: Second vector (1D numpy array).

    Returns:
        Cosine similarity in [-1.0, 1.0]. Returns 0.0 for zero vectors.
    """
    a = a.flatten().astype(np.float32)
    b = b.flatten().astype(np.float32)
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a < EPSILON or norm_b < EPSILON:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def softmax(values: List[float]) -> List[float]:
    """
    Apply softmax to convert a list of real-valued scores to probabilities.

    Uses numerically stable implementation (subtract max before exp).

    Args:
        values: List of floats.

    Returns:
        List of floats summing to 1.0. Returns empty list for empty input.
    """
    if not values:
        return []
    arr = np.array(values, dtype=np.float64)
    arr -= arr.max()  # numerical stability
    exp_arr = np.exp(arr)
    total = exp_arr.sum()
    if total < EPSILON:
        return [1.0 / len(values)] * len(values)
    return (exp_arr / total).tolist()
