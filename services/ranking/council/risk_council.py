"""
TalentGraph AI — Risk Council Evaluator

Evaluates hiring risks (gap risk, job-hopping, responsiveness) and assigns risk classifications.
"""

from __future__ import annotations

from datetime import datetime

from services.ranking.council.base_council import BaseCouncil
from shared.types.candidate import CandidateGenome
from shared.types.council import CouncilType, CouncilVote
from shared.types.job import JobGenome


class RiskCouncil(BaseCouncil):
    """
    Evaluates profile inconsistencies, tenure gaps, and contract compliance risks.
    """

    def __init__(self) -> None:
        """Initialize risk council."""
        super().__init__(CouncilType.RISK)

    def evaluate(self, candidate: CandidateGenome, job: JobGenome) -> CouncilVote:
        """Evaluate hiring risk."""
        # Risk score is a penalty (higher is worse)
        # We invert it for the vote score (higher = less risk / safer)
        risk_penalty = candidate.features.job_hop_risk * 0.5 + candidate.features.gap_risk * 0.5
        score = 1.0 - risk_penalty
        confidence = 0.9

        strengths = []
        concerns = []

        if score >= 0.75:
            strengths.append("Very low risk profile: stable tenures and no career gaps.")
            rec = "Strong Hire"  # Safe to hire
            rat = "No significant risk factors identified."
        elif score >= 0.45:
            concerns.append("Moderate risk flags: minor gaps or tenure warnings.")
            rec = "Consider"
            rat = "Presents standard candidate transition profiles."
        else:
            concerns.append(
                "Elevated risk profile: significant job-hopping or long unexplained gaps."
            )
            rec = "Reject"
            rat = "High career instability flags present."

        return CouncilVote(
            council_type=self.council_type,
            candidate_id=candidate.candidate_id,
            score=score,
            confidence=confidence,
            recommendation=rec,
            dimension_scores={
                "job_hop_risk": candidate.features.job_hop_risk,
                "gap_risk": candidate.features.gap_risk,
            },
            strengths=strengths,
            concerns=concerns,
            evidence=candidate.evidence.risk_evidence,
            rationale=rat,
            evaluated_at=datetime.utcnow(),
        )
