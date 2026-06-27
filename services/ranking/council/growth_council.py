"""
TalentGraph AI — Growth Council Evaluator

Evaluates candidate learning agility, educational qualifications, and research/patent output.
"""
from __future__ import annotations

from datetime import datetime
from shared.types.candidate import CandidateGenome
from shared.types.job import JobGenome
from shared.types.council import CouncilVote, CouncilType
from services.ranking.council.base_council import BaseCouncil


class GrowthCouncil(BaseCouncil):
    """
    Evaluates learning agility and academic pedigree.
    """

    def __init__(self) -> None:
        """Initialize growth council."""
        super().__init__(CouncilType.GROWTH)

    def evaluate(self, candidate: CandidateGenome, job: JobGenome) -> CouncilVote:
        """Evaluate learning agility."""
        score = candidate.learning_agility
        confidence = 0.85

        strengths = []
        concerns = []

        if score >= 0.8:
            strengths.append("High educational pedigree (Masters/PhD) or strong publication index.")
            rec = "Strong Hire"
            rat = "Shows outstanding learning agility and research capability."
        elif score >= 0.5:
            strengths.append("Completed appropriate higher education or multiple technical certifications.")
            rec = "Hire"
            rat = "Possesses healthy skill growth and certification velocity."
        else:
            concerns.append("Fewer skill expansion signals or certifications.")
            rec = "Consider"
            rat = "Shows standard learning signals but limited recent certifications."

        return CouncilVote(
            council_type=self.council_type,
            candidate_id=candidate.candidate_id,
            score=score,
            confidence=confidence,
            recommendation=rec,
            dimension_scores={"learning_score": candidate.features.learning_score},
            strengths=strengths,
            concerns=concerns,
            evidence=candidate.evidence.learning_evidence,
            rationale=rat,
            evaluated_at=datetime.utcnow(),
        )
