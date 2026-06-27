"""
TalentGraph AI — Counterfactual Explanation Engine

Generates counterfactual explanations specifying what changes or improvements
would shift the candidate into the next higher hiring recommendation tier.
"""
from __future__ import annotations

from typing import List, Optional
from shared.types.candidate import CandidateFeatures
from shared.types.ranking import (
    HiringRecommendation,
    CounterfactualExplanation,
)


class CounterfactualEngine:
    """
    Computes score gaps and lists action items to cross recommendation thresholds.
    """

    def __init__(self) -> None:
        """Initialize counterfactual engine."""
        pass

    def generate(
        self,
        candidate_id: str,
        current_rec: HiringRecommendation,
        final_score: float,
        features: CandidateFeatures,
    ) -> CounterfactualExplanation:
        """
        Generate counterfactual logic for the candidate.

        Args:
            candidate_id: Candidate identifier.
            current_rec: Current assigned recommendation.
            final_score: Composite score.
            features: Candidate features.

        Returns:
            CounterfactualExplanation object.
        """
        next_rec = None
        score_gap = 0.0
        improvements = []

        # Reference thresholds:
        # Strong Hire: score ≥ 0.82
        # Hire:        score ≥ 0.68
        # Consider:    score ≥ 0.52
        # Pass:        score ≥ 0.38
        # Reject:      score < 0.38

        if current_rec == HiringRecommendation.REJECT:
            next_rec = HiringRecommendation.PASS
            score_gap = max(0.01, 0.38 - final_score)
            improvements.append("Increase skill coverage: acquire core required technical competencies.")
            improvements.append("Add relevant certifications to substantiate skill competency claims.")

        elif current_rec == HiringRecommendation.PASS:
            next_rec = HiringRecommendation.CONSIDER
            score_gap = max(0.01, 0.52 - final_score)
            improvements.append("Verify availability: clarify immediate availability status.")
            if features.job_hop_risk > 0.4:
                improvements.append("Establish stability: demonstrate commitment to future employer.")

        elif current_rec == HiringRecommendation.CONSIDER:
            next_rec = HiringRecommendation.HIRE
            score_gap = max(0.01, 0.68 - final_score)
            improvements.append("Upskill technical domains: gain hands-on experience with secondary domains.")
            if features.experience_score < 0.6:
                improvements.append("Obtain leadership experience: seek team mentoring opportunities.")

        elif current_rec == HiringRecommendation.HIRE:
            next_rec = HiringRecommendation.STRONG_HIRE
            score_gap = max(0.01, 0.82 - final_score)
            improvements.append("Demonstrate technical mastery or leadership credentials.")
            improvements.append("Add evidence of publications or open-source contributions.")

        else: # Strong Hire
            next_rec = None
            score_gap = 0.0
            improvements = ["Candidate is already ranked as a Strong Hire. Maintain current expertise."]

        return CounterfactualExplanation(
            candidate_id=candidate_id,
            current_recommendation=current_rec,
            next_recommendation=next_rec,
            required_improvements=improvements,
            score_gap=score_gap,
        )
