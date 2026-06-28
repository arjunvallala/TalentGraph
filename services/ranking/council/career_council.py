"""
TalentGraph AI — Career Council Evaluator

Evidence used EXCLUSIVELY by this council:
  - career_velocity    : Advancement speed relative to career age
  - promotion_score    : Title progression rate across career
  - career_stability   : Tenure consistency (inverse coefficient of variation)
  - total_companies    : Raw number of employers
  - avg_tenure_months  : Mean tenure length

This council does NOT consider technical skills, research output, or behavioral platform signals.
Those belong to other councils. Career council represents a trajectory-focused HR reviewer.

When a technically brilliant candidate has a chaotic career history, this council
will be the primary voice of dissent — driving a genuine consensus disagreement.
"""
from __future__ import annotations

from datetime import datetime
from shared.types.candidate import CandidateGenome
from shared.types.job import JobGenome
from shared.types.council import CouncilVote, CouncilType
from services.ranking.council.base_council import BaseCouncil


class CareerCouncil(BaseCouncil):
    """
    Evaluates career trajectory using sequential career signals exclusively.

    Evidence is entirely drawn from career history metadata — no skill or
    behavior features are used. This guarantees council independence.
    """

    def __init__(self) -> None:
        """Initialize career council."""
        super().__init__(CouncilType.CAREER)

    def evaluate(self, candidate: CandidateGenome, job: JobGenome) -> CouncilVote:
        """
        Evaluate career trajectory from sequential career evidence.

        Evidence sources (mutually exclusive from TechnicalCouncil):
          - features.career_velocity: Speed of seniority advancement
          - features.promotion_score: Detected promotion events / expected promotions
          - features.career_stability: Tenure consistency across roles
          - features.total_companies: Number of distinct employers
          - features.avg_tenure_months: Average tenure per role (in months)
        """
        f = candidate.features

        career_vel  = f.career_velocity if hasattr(f, 'career_velocity') else 0.0
        promotion   = f.promotion_score
        stability   = f.career_stability if hasattr(f, 'career_stability') else f.stability_score
        total_cos   = f.total_companies
        avg_tenure  = f.avg_tenure_months  # in months

        # Normalise avg_tenure: 24 months (2 years) = 1.0, capped
        avg_tenure_norm = min(1.0, avg_tenure / 24.0) if avg_tenure > 0 else 0.0

        # Career score: weighted combination of trajectory signals
        score = (
            0.35 * career_vel        # Primary: how fast they advanced
            + 0.25 * promotion       # Confirmed title progression events
            + 0.25 * stability       # Consistency of tenure lengths
            + 0.15 * avg_tenure_norm # Average role duration
        )
        score = float(min(1.0, max(0.0, score)))

        # Confidence depends on evidence richness of career data
        evidence_signals = sum(1 for v in [career_vel, promotion, stability, avg_tenure_norm] if v > 0.01)
        # Extra confidence penalty if only 1 company (hard to assess trajectory)
        confidence = 0.55 + (evidence_signals / 4.0) * 0.35
        if total_cos <= 1:
            confidence = max(0.3, confidence - 0.15)  # Hard to judge trajectory from single employer

        strengths = []
        concerns = []

        # Career velocity evidence
        if career_vel >= 0.75:
            strengths.append(
                f"Career velocity of {career_vel:.2f} — reached current seniority significantly "
                f"faster than the cohort average."
            )
        elif career_vel >= 0.45:
            strengths.append(f"Career advancement is on a standard upward track (velocity: {career_vel:.2f}).")
        else:
            concerns.append(
                f"Career velocity is low ({career_vel:.2f}) — seniority growth appears slow "
                f"relative to years of experience."
            )

        # Promotion evidence
        if promotion >= 0.60:
            strengths.append(
                f"Promotion detection score {promotion:.2f} indicates confirmed title advancement events."
            )
        elif promotion < 0.20:
            concerns.append(
                f"No clear promotion signals detected (promotion score: {promotion:.2f})."
            )

        # Stability evidence
        if stability >= 0.70:
            strengths.append(
                f"Tenure consistency score {stability:.2f} — roles maintained for stable durations."
            )
        elif stability < 0.40:
            concerns.append(
                f"High tenure variance (stability score: {stability:.2f}) — inconsistent role durations."
            )

        # Average tenure evidence
        if avg_tenure >= 24:
            strengths.append(
                f"Average role tenure of {avg_tenure:.0f} months ({avg_tenure/12:.1f} years) "
                f"reflects commitment."
            )
        elif avg_tenure < 12 and avg_tenure > 0:
            concerns.append(
                f"Average role tenure is only {avg_tenure:.0f} months — risk of early departure."
            )

        if score >= 0.72:
            rec = "Strong Hire"
            rat = (
                f"Career trajectory is impressive: velocity {career_vel:.2f}, "
                f"stability {stability:.2f}, avg tenure {avg_tenure:.0f} months."
            )
        elif score >= 0.48:
            rec = "Hire"
            rat = (
                f"Career history is solid: standard progression rate, "
                f"tenure stability {stability:.2f}."
            )
        else:
            rec = "Consider"
            rat = (
                f"Career trajectory shows concerns: velocity {career_vel:.2f}, "
                f"stability {stability:.2f}."
            )

        return CouncilVote(
            council_type=self.council_type,
            candidate_id=candidate.candidate_id,
            score=score,
            confidence=confidence,
            recommendation=rec,
            dimension_scores={
                "career_velocity": career_vel,
                "promotion_score": promotion,
                "career_stability": stability,
                "avg_tenure_months": avg_tenure,
                "total_companies": float(total_cos),
            },
            strengths=strengths,
            concerns=concerns,
            evidence=candidate.evidence.stability_evidence,
            rationale=rat,
            evaluated_at=datetime.utcnow(),
        )
