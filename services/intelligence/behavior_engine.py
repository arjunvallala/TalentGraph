"""
TalentGraph AI — Behavior Engine

Analyzes Redrob platform interaction signals (response rates, declination rates,
profile activity, notice period) to assess candidate engagement and hiring readiness.
"""
from __future__ import annotations

from typing import Any

from shared.logging_setup import get_logger
from shared.types.candidate import AvailabilityStatus, CandidateProfile

logger = get_logger(__name__)


class BehaviorEngine:
    """
    Evaluates candidate platform responsiveness, declination rates, and hiring readiness.
    """

    def __init__(self) -> None:
        """Initialize the behavior engine."""
        logger.info("BehaviorEngine initialised")

    def analyze_behavior(self, profile: CandidateProfile) -> dict[str, Any]:
        """
        Analyze candidate responsiveness, decline frequency, and activity indicators.

        Args:
            profile: Candidate profile containing Redrob signals.

        Returns:
            A dictionary containing analyzed behavioral metrics and a computed
            readiness score.
        """
        signals = profile.redrob_signals

        # Calculate responsiveness
        response_rate = signals.response_rate

        # Calculate declination rate index
        decline_index = 0.0
        if signals.interview_declined_count > 0 or signals.offer_declined_count > 0:
            total_declined = signals.interview_declined_count + signals.offer_declined_count
            decline_index = min(1.0, total_declined / 5.0)

        # Engagement indicator based on last active days (lower is more active)
        active_score = 0.5
        if signals.last_active_days is not None:
            if signals.last_active_days <= 7:
                active_score = 1.0
            elif signals.last_active_days <= 30:
                active_score = 0.8
            elif signals.last_active_days <= 90:
                active_score = 0.5
            else:
                active_score = 0.2

        # Notice period score (shorter notice is better for immediate needs)
        notice_score = 0.5
        if signals.notice_period_days is not None:
            if signals.notice_period_days == 0:
                notice_score = 1.0
            elif signals.notice_period_days <= 15:
                notice_score = 0.9
            elif signals.notice_period_days <= 30:
                notice_score = 0.7
            elif signals.notice_period_days <= 60:
                notice_score = 0.4
            else:
                notice_score = 0.1

        # Availability state multiplier
        avail_mult = {
            AvailabilityStatus.IMMEDIATELY_AVAILABLE: 1.0,
            AvailabilityStatus.OPEN_TO_OPPORTUNITIES: 0.8,
            AvailabilityStatus.NOTICE_PERIOD: 0.7,
            AvailabilityStatus.NOT_LOOKING: 0.2,
            AvailabilityStatus.UNKNOWN: 0.5,
        }.get(signals.availability_status, 0.5)

        # Composite readiness score [0.0, 1.0]
        readiness_score = (
            response_rate * 0.4 +
            active_score * 0.3 +
            notice_score * 0.3
        ) * avail_mult

        return {
            "responsiveness": response_rate,
            "decline_score": decline_index,
            "activity_engagement": active_score,
            "notice_score": notice_score,
            "readiness_score": readiness_score,
        }
