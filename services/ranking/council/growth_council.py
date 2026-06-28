"""
TalentGraph AI — Growth Council Evaluator

Evidence used EXCLUSIVELY by this council:
  - learning_score     : Certifications + skill breadth + education diversity
  - research_score     : Publications, patents, open-source, innovation signals
  - education_score    : Degree level (PhD > Masters > Bachelors > etc.)
  - skill_consistency  : Skill coherence across career stages (specialisation depth)
  - certification_count: Number of professional certifications earned

Growth council represents a "future potential" evaluator — not what the candidate
has done, but how fast they learn and how much headroom they have.

A candidate with many certifications and research output will score high here
even if their total experience is short. This ensures disagreement with
CareerCouncil on early-career research candidates.
"""
from __future__ import annotations

from datetime import datetime

from services.ranking.council.base_council import BaseCouncil
from shared.types.candidate import CandidateGenome
from shared.types.council import CouncilType, CouncilVote
from shared.types.job import JobGenome


class GrowthCouncil(BaseCouncil):
    """
    Evaluates learning trajectory and future growth potential.
    Uses certification velocity, research output, and skill evolution signals.
    """

    def __init__(self) -> None:
        """Initialize growth council."""
        super().__init__(CouncilType.GROWTH)

    def evaluate(self, candidate: CandidateGenome, job: JobGenome) -> CouncilVote:
        """
        Evaluate learning agility and future potential from growth evidence.

        Evidence sources (distinct from Technical and Career councils):
          - features.learning_score: Composite learning agility signal
          - features.research_score: Research and innovation output
          - features.education_score: Degree level signals
          - features.skill_consistency: Cross-career skill coherence
          - features.certification_count: Number of professional certs
        """
        f = candidate.features

        learning    = f.learning_score
        research    = f.research_score
        edu         = f.education_score if hasattr(f, 'education_score') else f.education_level_score
        skill_cons  = f.skill_consistency if hasattr(f, 'skill_consistency') else 0.5
        cert_count  = f.certification_count if hasattr(f, 'certification_count') else 0
        cert_norm   = min(1.0, cert_count / 5.0)  # 5+ certs = 1.0

        # Growth score: future-potential focused
        score = (
            0.35 * learning    # Primary: breadth of learning signals
            + 0.25 * research  # Research shows deep intellectual curiosity
            + 0.20 * edu       # Academic foundation
            + 0.12 * cert_norm # Certification pursuit = active learning
            + 0.08 * skill_cons  # Consistent skill application = mastery
        )
        score = float(min(1.0, max(0.0, score)))

        # Confidence: lower if most growth signals are absent
        evidence_signals = sum(1 for v in [learning, research, edu, cert_norm] if v > 0.01)
        confidence = 0.50 + (evidence_signals / 4.0) * 0.40

        strengths = []
        concerns = []

        if learning >= 0.70:
            strengths.append(
                f"Strong learning agility signals: certifications, skill breadth, "
                f"and education score composite of {learning:.2f}."
            )
        elif learning < 0.30:
            concerns.append(
                f"Limited learning signals (learning score: {learning:.2f}) — "
                f"few certifications or narrow skill set detected."
            )

        if research >= 0.50:
            strengths.append(
                f"Research/innovation signal of {research:.2f} — "
                f"publications, patents, or open-source contributions detected."
            )

        if edu >= 0.85:
            strengths.append(
                f"Advanced academic pedigree (education score: {edu:.2f}) — "
                f"Masters or PhD level."
            )
        elif edu >= 0.65:
            strengths.append(f"Bachelor's or equivalent education base (score: {edu:.2f}).")
        elif edu < 0.35:
            concerns.append(f"Education signal is weak ({edu:.2f}) — may indicate limited formal training.")

        if cert_count >= 3:
            strengths.append(f"{cert_count} professional certification(s) confirmed — active learner.")
        elif cert_count == 0:
            concerns.append("No professional certifications found in profile.")

        if skill_cons >= 0.70:
            strengths.append(
                f"High skill coherence across career stages ({skill_cons:.2f}) — "
                f"indicates domain specialisation depth."
            )

        if score >= 0.75:
            rec = "Strong Hire"
            rat = (
                f"High growth potential: learning {learning:.2f}, "
                f"research {research:.2f}, {cert_count} certs."
            )
        elif score >= 0.50:
            rec = "Hire"
            rat = f"Adequate growth signals: learning {learning:.2f}, education {edu:.2f}."
        else:
            rec = "Consider"
            rat = (
                f"Growth signals are limited: learning {learning:.2f}, "
                f"research {research:.2f}. Further evaluation advised."
            )

        return CouncilVote(
            council_type=self.council_type,
            candidate_id=candidate.candidate_id,
            score=score,
            confidence=confidence,
            recommendation=rec,
            dimension_scores={
                "learning_score": learning,
                "research_score": research,
                "education_score": edu,
                "skill_consistency": skill_cons,
                "certification_count": float(cert_count),
            },
            strengths=strengths,
            concerns=concerns,
            evidence=candidate.evidence.learning_evidence,
            rationale=rat,
            evaluated_at=datetime.utcnow(),
        )
