"""
TalentGraph AI — Career Council Evaluator

Evaluates career progression history, promotion rate, and tenure stability.
"""
from __future__ import annotations

from datetime import datetime
from shared.types.candidate import CandidateGenome
from shared.types.job import JobGenome
from shared.types.council import CouncilVote, CouncilType
from services.ranking.council.base_council import BaseCouncil


class CareerCouncil(BaseCouncil):
    """
    Evaluates career progression and work stability.
    """

    def __init__(self) -> None:
        """Initialize career council."""
        super().__init__(CouncilType.CAREER)

    def evaluate(self, candidate: CandidateGenome, job: JobGenome) -> CouncilVote:
        """Evaluate career progression."""
        score = candidate.career_progression
        confidence = 0.85

        strengths = []
        concerns = []
        
        if score >= 0.75:
            strengths.append("Excellent career advancement and promotion frequency.")
            rec = "Strong Hire"
            rat = "Shows high upward mobility and velocity."
        elif score >= 0.5:
            strengths.append("Consistent work history with steady career progression.")
            rec = "Hire"
            rat = "Meets the expected tenure stability and title growth."
        else:
            concerns.append("Slow title progression relative to career longevity.")
            rec = "Consider"
            rat = "Limited title growth or career velocity signals."

        return CouncilVote(
            council_type=self.council_type,
            candidate_id=candidate.candidate_id,
            score=score,
            confidence=confidence,
            recommendation=rec,
            dimension_scores={"career_velocity": candidate.features.career_velocity},
            strengths=strengths,
            concerns=concerns,
            evidence=candidate.evidence.stability_evidence,
            rationale=rat,
            evaluated_at=datetime.utcnow(),
        )
