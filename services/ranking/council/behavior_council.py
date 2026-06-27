"""
TalentGraph AI — Behavior Council Evaluator

Evaluates platform interaction behavior, response rates, and notice period readiness.
"""
from __future__ import annotations

from datetime import datetime
from shared.types.candidate import CandidateGenome
from shared.types.job import JobGenome
from shared.types.council import CouncilVote, CouncilType
from services.ranking.council.base_council import BaseCouncil


class BehaviorCouncil(BaseCouncil):
    """
    Evaluates hiring availability and engagement responsiveness.
    """

    def __init__(self) -> None:
        """Initialize behavior council."""
        super().__init__(CouncilType.BEHAVIOR)

    def evaluate(self, candidate: CandidateGenome, job: JobGenome) -> CouncilVote:
        """Evaluate behavioral readiness."""
        score = candidate.behavioral_signals
        confidence = 0.8

        strengths = []
        concerns = []

        if score >= 0.75:
            strengths.append("High platform activity and immediate availability status.")
            rec = "Strong Hire"
            rat = "Extremely responsive and highly motivated candidate."
        elif score >= 0.45:
            strengths.append("Active profile with good response rate indicators.")
            rec = "Hire"
            rat = "Regular platform engagement with normal notice period."
        else:
            concerns.append("Low responsiveness or longer notice period warning.")
            rec = "Pass"
            rat = "Candidate response rate or availability is less than ideal."

        return CouncilVote(
            council_type=self.council_type,
            candidate_id=candidate.candidate_id,
            score=score,
            confidence=confidence,
            recommendation=rec,
            dimension_scores={"availability": candidate.features.hiring_availability},
            strengths=strengths,
            concerns=concerns,
            evidence=candidate.evidence.behavior_evidence,
            rationale=rat,
            evaluated_at=datetime.utcnow(),
        )
