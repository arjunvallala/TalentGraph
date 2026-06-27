"""
TalentGraph AI — Technical Council Evaluator

Evaluates technical capability, skill coverage, and certifications.
"""
from __future__ import annotations

from datetime import datetime
from shared.types.candidate import CandidateGenome
from shared.types.job import JobGenome
from shared.types.council import CouncilVote, CouncilType
from services.ranking.council.base_council import BaseCouncil


class TechnicalCouncil(BaseCouncil):
    """
    Evaluates technical competency, skill coverage, and engineering pedigree.
    """

    def __init__(self) -> None:
        """Initialize technical council."""
        super().__init__(CouncilType.TECHNICAL)

    def evaluate(self, candidate: CandidateGenome, job: JobGenome) -> CouncilVote:
        """Evaluate technical capability."""
        score = candidate.technical_capability
        confidence = 0.9

        strengths = []
        concerns = []
        
        if score >= 0.8:
            strengths.append(f"Exceptional technical alignment: skill coverage score is {(score * 100):.1f}%.")
            rec = "Strong Hire"
            rat = "Technical skills and engineering pedigree exceed requirements."
        elif score >= 0.6:
            strengths.append("Demonstrates solid technical capabilities across required skills.")
            rec = "Hire"
            rat = "Meets the core technical requirements for the role."
        else:
            concerns.append("Skill coverage is below target requirements.")
            rec = "Pass"
            rat = "Technical skillset has gaps relative to the job requirements."

        return CouncilVote(
            council_type=self.council_type,
            candidate_id=candidate.candidate_id,
            score=score,
            confidence=confidence,
            recommendation=rec,
            dimension_scores={"skill_coverage": candidate.features.skill_coverage},
            strengths=strengths,
            concerns=concerns,
            evidence=candidate.evidence.experience_evidence,
            rationale=rat,
            evaluated_at=datetime.utcnow(),
        )
