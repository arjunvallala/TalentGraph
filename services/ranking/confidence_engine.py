"""
TalentGraph AI — Confidence Estimation Engine

Estimates the overall confidence in a hiring recommendation.

Confidence is NOT derived from the final score. It is computed independently from:
  1. Profile completeness    — How much data is available to reason from
  2. Council agreement       — How consistently the 5 councils agreed (low std = high agreement)
  3. Evidence quality        — Strength signal from evidence ledger
  4. Feature consistency     — Low variance in feature vector = more predictable candidate
  5. Missing data penalty    — Penalise sparse or zero features

Each factor contributes a genuine signal and can independently lower confidence.
"""
from __future__ import annotations

import numpy as np

from shared.types.candidate import CandidateFeatures
from shared.types.council import FinalCouncilDecision
from shared.types.ranking import ConfidenceLevel


class ConfidenceEngine:
    """
    Estimates numeric and categorical confidence scores for hiring decisions.

    Confidence is decoupled from the final hiring score — a high-scoring candidate
    with sparse data or high council disagreement will correctly receive LOW confidence.
    """

    def __init__(self) -> None:
        """Initialize confidence engine."""
        pass

    def estimate_confidence(
        self, features: CandidateFeatures, council_decision: FinalCouncilDecision
    ) -> tuple[float, ConfidenceLevel]:
        """
        Estimate numeric confidence in [0, 1] and assign a ConfidenceLevel classification.

        Five independent signals are computed and combined:
          - completeness_score (25%): Fraction of profile fields populated.
          - agreement_score    (25%): Council consensus agreement (1 - std of individual votes).
          - evidence_quality   (20%): Evidence strength from the ledger, if available.
          - feature_consistency(20%): Stability of the candidate's feature vector.
          - data_richness      (10%): Penalise candidates with many zero-valued features.

        Args:
            features: Candidate feature vector.
            council_decision: Consensus decision from Hiring Council.

        Returns:
            Tuple of (numeric confidence [0, 1], ConfidenceLevel enum).
        """
        # ── 1. Profile Completeness ───────────────────────────────────────────
        completeness_score = float(features.profile_completeness)

        # ── 2. Council Agreement Score ────────────────────────────────────────
        # Already computed in HiringCouncil as (1 - std_dev_of_individual_scores)
        # agreement_score = 1.0 when all councils perfectly agree, lower when they diverge
        agreement_score = float(max(0.0, min(1.0, council_decision.agreement_score)))

        # ── 3. Evidence Quality ───────────────────────────────────────────────
        # council_confidence is the average confidence reported by individual councils
        # reflecting their internal certainty about their evidence
        evidence_quality = float(max(0.0, min(1.0, council_decision.council_confidence)))

        # ── 4. Feature Consistency ────────────────────────────────────────────
        # A candidate with highly variable features (e.g. great skills but terrible stability)
        # is harder to predict — lower confidence. Measured as 1 - normalised_std of key features.
        key_feature_values = [
            features.experience_score,
            features.career_stability if hasattr(features, 'career_stability') else features.stability_score,
            features.leadership_score,
            features.learning_score,
            features.behavior_score,
            features.hiring_availability if hasattr(features, 'hiring_availability') else features.availability_score,
        ]
        # Only include non-zero values (zeros indicate missing data, handled separately)
        non_zero_vals = [v for v in key_feature_values if v > 0.01]
        if len(non_zero_vals) >= 2:
            arr = np.array(non_zero_vals, dtype=np.float32)
            feat_std = float(arr.std())
            # Normalise: std=0 → fully consistent (1.0), std=0.5 → inconsistent (0.0)
            feature_consistency = float(max(0.0, 1.0 - (feat_std / 0.5)))
        else:
            feature_consistency = 0.3  # Too few signals — low consistency

        # ── 5. Data Richness (missing data penalty) ───────────────────────────
        # If many features are at exactly 0.0 it indicates missing profile data
        all_features = [
            features.experience_score,
            features.leadership_score,
            features.learning_score,
            features.research_score,
            features.behavior_score,
            features.profile_completeness,
            features.career_velocity if hasattr(features, 'career_velocity') else 0.0,
            features.skill_consistency if hasattr(features, 'skill_consistency') else 0.0,
        ]
        zero_count = sum(1 for v in all_features if v < 0.01)
        zero_fraction = zero_count / max(1, len(all_features))
        data_richness = float(max(0.0, 1.0 - zero_fraction * 1.5))  # Heavy penalty for sparse features

        # ── Weighted Combination ──────────────────────────────────────────────
        confidence_score = (
            completeness_score  * 0.25
            + agreement_score   * 0.25
            + evidence_quality  * 0.20
            + feature_consistency * 0.20
            + data_richness     * 0.10
        )
        confidence_score = float(max(0.0, min(1.0, confidence_score)))

        # ── Classification ────────────────────────────────────────────────────
        if confidence_score >= 0.75:
            level = ConfidenceLevel.HIGH
        elif confidence_score >= 0.50:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW

        return confidence_score, level
