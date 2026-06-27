"""
TalentGraph AI — Confidence Estimation Engine

Estimates the overall confidence in a hiring recommendation based on
profile completeness, committee agreement, and evidence strength.
"""
from __future__ import annotations

from typing import Tuple
from shared.types.ranking import ConfidenceLevel
from shared.types.candidate import CandidateFeatures
from shared.types.council import FinalCouncilDecision


class ConfidenceEngine:
    """
    Estimates numeric and categorical confidence scores for hiring decisions.
    """

    def __init__(self) -> None:
        """Initialize confidence engine."""
        pass

    def estimate_confidence(
        self, features: CandidateFeatures, council_decision: FinalCouncilDecision
    ) -> Tuple[float, ConfidenceLevel]:
        """
        Estimate numeric confidence in [0, 1] and assign a ConfidenceLevel classification.

        Args:
            features: Candidate feature vector.
            council_decision: Consensus decision from Hiring Council.

        Returns:
            Tuple of (numeric confidence [0, 1], ConfidenceLevel enum).
        """
        # Confidence score is calculated from:
        # - Profile completeness (50% weight)
        # - Council agreement score (30% weight)
        # - Council confidence score (20% weight)
        
        completeness = features.profile_completeness
        agreement = council_decision.agreement_score
        council_conf = council_decision.council_confidence

        confidence_score = (
            completeness * 0.5 + 
            agreement * 0.3 + 
            council_conf * 0.2
        )

        # Classification
        if confidence_score >= 0.75:
            level = ConfidenceLevel.HIGH
        elif confidence_score >= 0.50:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW

        return float(confidence_score), level
