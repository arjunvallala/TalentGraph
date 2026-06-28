"""
TalentGraph AI — Behavior Council Evaluator

Evidence used EXCLUSIVELY by this council:
  - behavior_score         : Redrob platform engagement composite
  - hiring_availability    : Notice period + availability status
  - response_rate          : Fraction of recruiter messages responded to
  - last_active_days       : Days since last platform activity
  - interview_declined_count: Reliability signals

This council represents the **Recruiter Operations** perspective:
  "Is this candidate reachable, responsive, and hireable today?"

A technically excellent candidate who has been inactive for 180 days,
declined 3 interviews, and has a 90-day notice period will score LOW here —
creating authentic disagreement with TechnicalCouncil.

This council does NOT consider skills, career trajectory, or research output.
"""
from __future__ import annotations

from datetime import datetime

from services.ranking.council.base_council import BaseCouncil
from shared.types.candidate import CandidateGenome
from shared.types.council import CouncilType, CouncilVote
from shared.types.job import JobGenome


class BehaviorCouncil(BaseCouncil):
    """
    Evaluates recruiter-facing engagement signals and hiring readiness.
    Uses only platform behavioral data — no technical or career signals.
    """

    def __init__(self) -> None:
        """Initialize behavior council."""
        super().__init__(CouncilType.BEHAVIOR)

    def evaluate(self, candidate: CandidateGenome, job: JobGenome) -> CouncilVote:
        """
        Evaluate platform behavior and hiring readiness.

        Evidence sources (mutually exclusive from other councils):
          - features.behavior_score: Platform engagement composite
          - features.hiring_availability: Notice period + availability status
          - profile.redrob_signals (via genome): Raw platform signals
        """
        f = candidate.features

        behavior     = f.behavior_score
        availability = (
            f.hiring_availability
            if hasattr(f, 'hiring_availability')
            else f.availability_score
        )

        # Attempt to extract raw Redrob signals for finer-grained evidence
        redrob = None
        if candidate.profile and hasattr(candidate.profile, 'redrob_signals'):
            redrob = candidate.profile.redrob_signals

        response_rate = redrob.response_rate if redrob else 0.5
        last_active   = redrob.last_active_days if (redrob and redrob.last_active_days is not None) else 45
        declined_int  = redrob.interview_declined_count if redrob else 0
        declined_off  = redrob.offer_declined_count if redrob else 0

        # Activity score: raw computation (mirrors feature extractor logic)
        if last_active <= 7:
            activity = 1.0
        elif last_active <= 30:
            activity = 0.8
        elif last_active <= 90:
            activity = 0.5
        elif last_active <= 180:
            activity = 0.3
        else:
            activity = 0.1

        # Reliability: penalise for declined interviews/offers
        total_declined = declined_int + declined_off
        reliability = max(0.0, 1.0 - total_declined * 0.15)

        # Behavior council score — purely operational/recruiter signals
        score = (
            0.35 * behavior       # Overall platform engagement composite
            + 0.30 * availability # Can they join quickly?
            + 0.20 * response_rate  # Will they reply to recruiters?
            + 0.15 * reliability  # Have they honoured past commitments?
        )
        score = float(min(1.0, max(0.0, score)))

        # Confidence is high when we have actual Redrob platform data
        confidence = 0.85 if redrob else 0.55  # Lower if we're working from defaults

        strengths = []
        concerns = []

        if response_rate >= 0.80:
            strengths.append(
                f"Response rate of {response_rate * 100:.0f}% — highly responsive to recruiters."
            )
        elif response_rate < 0.40:
            concerns.append(
                f"Low recruiter response rate ({response_rate * 100:.0f}%) — outreach may be difficult."
            )

        if last_active <= 7:
            strengths.append("Active on platform within the last 7 days — immediately reachable.")
        elif last_active <= 30:
            strengths.append(f"Active {last_active} days ago — recently engaged.")
        elif last_active > 90:
            concerns.append(
                f"Last active {last_active} days ago — engagement may have lapsed."
            )

        if availability >= 0.80:
            strengths.append(
                f"High availability score ({availability:.2f}) — can join with minimal notice."
            )
        elif availability < 0.40:
            concerns.append(
                f"Low availability ({availability:.2f}) — long notice period or not currently looking."
            )

        if total_declined > 0:
            concerns.append(
                f"{total_declined} past interview/offer decline(s) detected — reliability flag."
            )
        else:
            strengths.append("No declined interviews or offers on record — reliable candidate.")

        if score >= 0.75:
            rec = "Strong Hire"
            rat = (
                f"Excellent hiring readiness: behavior {behavior:.2f}, "
                f"availability {availability:.2f}, response {response_rate * 100:.0f}%."
            )
        elif score >= 0.45:
            rec = "Hire"
            rat = (
                f"Adequate platform engagement: behavior {behavior:.2f}, "
                f"availability {availability:.2f}."
            )
        else:
            rec = "Pass"
            rat = (
                f"Poor recruiter engagement signals: behavior {behavior:.2f}, "
                f"last active {last_active} days ago."
            )

        return CouncilVote(
            council_type=self.council_type,
            candidate_id=candidate.candidate_id,
            score=score,
            confidence=confidence,
            recommendation=rec,
            dimension_scores={
                "behavior_score": behavior,
                "hiring_availability": availability,
                "response_rate": response_rate,
                "activity_recency": activity,
                "reliability": reliability,
            },
            strengths=strengths,
            concerns=concerns,
            evidence=candidate.evidence.behavior_evidence,
            rationale=rat,
            evaluated_at=datetime.utcnow(),
        )
