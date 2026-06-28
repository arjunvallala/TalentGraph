"""
TalentGraph AI — Feature Importance Analyzer

Analyzes feature score distribution across candidates to compute
feature importance and variance metrics.
"""
from __future__ import annotations

import numpy as np

from shared.types.analytics import FeatureImportance
from shared.types.ranking import CandidateResult


class FeatureImportanceAnalyzer:
    """
    Computes feature contribution and variance stats across shortlisted candidates.
    """

    def __init__(self) -> None:
        """Initialize the analyzer."""
        pass

    def compute(self, results: list[CandidateResult]) -> list[FeatureImportance]:
        """
        Calculate relative feature importance scores from candidate results.

        Args:
            results: List of candidate results.

        Returns:
            A list of FeatureImportance items.
        """
        if not results:
            return []

        features_to_analyze = [
            "experience_score",
            "skill_coverage",
            "domain_match",
            "career_velocity",
        ]

        importance_list = []

        # Simple simulation: relative importance is proportional to variance in the shortlist
        # and its weight in the job genome.
        # In a real environment, we'd run correlation with overall_score.
        for name in features_to_analyze:
            scores = []
            for r in results:
                # Safely get feature score
                scores.append(getattr(r.features, name, 0.5))

            arr = np.array(scores, dtype=np.float32)
            variance = float(arr.var())

            # Simple importance proxy (correlation or variance-driven)
            importance_score = float(arr.mean() * 0.8 + 0.2)

            importance_list.append(
                FeatureImportance(
                    feature_name=name.replace("_", " ").title(),
                    importance_score=importance_score,
                    variance=variance,
                )
            )

        # Sort descending by importance_score
        importance_list.sort(key=lambda x: x.importance_score, reverse=True)
        return importance_list
