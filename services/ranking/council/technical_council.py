"""
TalentGraph AI — Technical Council Evaluator

Evidence used EXCLUSIVELY by this council:
  - skill_coverage     : Fraction of JD-required skills present
  - domain_match       : Semantic embedding similarity vs JD
  - research_score     : Patent/publication/innovation signals
  - education_score    : Degree level and institution signals
  - certifications     : Professional technical certifications

This council does NOT look at leadership, stability, or career velocity.
Those signals belong to other councils, ensuring genuine independence.
"""
from __future__ import annotations

from datetime import datetime

from services.ranking.council.base_council import BaseCouncil
from shared.types.candidate import CandidateGenome
from shared.types.council import CouncilType, CouncilVote
from shared.types.job import JobGenome


class TechnicalCouncil(BaseCouncil):
    """
    Evaluates technical competency using skill coverage, domain alignment,
    research output, and education signals exclusively.

    This council can strongly disagree with Career/Behavior councils —
    a candidate with deep technical skills but poor career stability will
    score high here and low in CareerCouncil, creating genuine dissent.
    """

    def __init__(self) -> None:
        """Initialize technical council."""
        super().__init__(CouncilType.TECHNICAL)

    def evaluate(self, candidate: CandidateGenome, job: JobGenome) -> CouncilVote:
        """
        Evaluate technical capability from distinct technical evidence signals.

        Evidence sources (mutually exclusive from other councils):
          - features.skill_coverage: JD-specific skill overlap
          - features.domain_match: Semantic domain alignment
          - features.research_score: Research/innovation signals
          - features.education_score: Academic pedigree
          - features.certifications_score: Professional certifications
        """
        f = candidate.features

        # Technical score is a weighted composite of 5 distinct technical signals
        # These signals do NOT appear in Career or Behavior councils
        skill_cov  = f.skill_coverage
        domain_m   = f.domain_match
        research   = f.research_score
        edu        = f.education_score if hasattr(f, 'education_score') else f.education_level_score
        cert       = f.certifications_score if hasattr(f, 'certifications_score') else (f.certification_count / 5.0)

        score = (
            0.40 * skill_cov   # Primary: JD skill fit
            + 0.25 * domain_m  # Secondary: semantic domain fit
            + 0.15 * edu       # Education supports technical credibility
            + 0.12 * research  # Research/innovation bonus
            + 0.08 * cert      # Certification validation
        )
        score = float(min(1.0, max(0.0, score)))

        # Confidence depends on how much technical evidence we have
        evidence_signals = sum(1 for v in [skill_cov, domain_m, research, edu, cert] if v > 0.01)
        confidence = 0.5 + (evidence_signals / 5.0) * 0.45  # 0.5 to 0.95

        strengths = []
        concerns = []

        if skill_cov >= 0.80:
            strengths.append(
                f"Skill coverage is {skill_cov * 100:.0f}% — exceeds the JD requirements."
            )
        elif skill_cov >= 0.55:
            strengths.append(
                f"Skill coverage is {skill_cov * 100:.0f}% — meets core JD requirements."
            )
        else:
            concerns.append(
                f"Skill coverage is only {skill_cov * 100:.0f}% — below the 55% threshold."
            )

        if domain_m >= 0.75:
            strengths.append(
                f"Strong domain alignment ({domain_m * 100:.0f}%) with this role's technical area."
            )
        elif domain_m < 0.40:
            concerns.append(
                f"Domain alignment is low ({domain_m * 100:.0f}%) relative to job requirements."
            )

        if research >= 0.60:
            strengths.append(f"Research/innovation output score: {research:.2f} — above average.")

        if edu >= 0.80:
            strengths.append(f"Advanced degree pedigree (education score: {edu:.2f}).")
        elif edu < 0.35:
            concerns.append(f"Education level score ({edu:.2f}) is below typical expectations.")

        if score >= 0.78:
            rec = "Strong Hire"
            rat = (
                f"Technical profile is highly aligned: skill coverage {skill_cov * 100:.0f}%, "
                f"domain match {domain_m * 100:.0f}%."
            )
        elif score >= 0.55:
            rec = "Hire"
            rat = (
                f"Technical baseline met: coverage {skill_cov * 100:.0f}%, "
                f"domain {domain_m * 100:.0f}%."
            )
        else:
            rec = "Pass"
            rat = (
                f"Technical gaps prevent a hire recommendation: "
                f"coverage {skill_cov * 100:.0f}%, domain {domain_m * 100:.0f}%."
            )

        return CouncilVote(
            council_type=self.council_type,
            candidate_id=candidate.candidate_id,
            score=score,
            confidence=confidence,
            recommendation=rec,
            dimension_scores={
                "skill_coverage": skill_cov,
                "domain_match": domain_m,
                "research_score": research,
                "education_score": edu,
                "certifications_score": cert,
            },
            strengths=strengths,
            concerns=concerns,
            evidence=candidate.evidence.skill_evidence,
            rationale=rat,
            evaluated_at=datetime.utcnow(),
        )
