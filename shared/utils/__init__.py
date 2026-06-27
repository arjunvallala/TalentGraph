"""
TalentGraph AI — Shared Utilities Package

Provides text processing, mathematical operations, and file I/O
utilities used across the entire service layer.
"""
from shared.utils.text_utils import (
    normalize_text,
    extract_skills_from_text,
    extract_years_of_experience,
    tokenize_for_bm25,
    build_candidate_text,
    detect_seniority_from_title,
)
from shared.utils.math_utils import (
    safe_divide,
    normalize_minmax,
    normalize_log,
    clip,
    weighted_average,
    reciprocal_rank_fusion,
    cosine_similarity,
    softmax,
)
from shared.utils.file_utils import (
    ensure_dir,
    save_pickle,
    load_pickle,
    save_json,
    load_json,
)

__all__ = [
    "normalize_text",
    "extract_skills_from_text",
    "extract_years_of_experience",
    "tokenize_for_bm25",
    "build_candidate_text",
    "detect_seniority_from_title",
    "safe_divide",
    "normalize_minmax",
    "normalize_log",
    "clip",
    "weighted_average",
    "reciprocal_rank_fusion",
    "cosine_similarity",
    "softmax",
    "ensure_dir",
    "save_pickle",
    "load_pickle",
    "save_json",
    "load_json",
]
