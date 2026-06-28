"""
TalentGraph AI — Career Engine

Evaluates career progression trajectories, promotion histories, work stability,
and candidate tenure growth patterns.
"""
from __future__ import annotations

from typing import Any

from shared.logging_setup import get_logger
from shared.types.candidate import CandidateProfile

logger = get_logger(__name__)


class CareerEngine:
    """
    Evaluates career progression growth, promotion velocity, and job stability.
    """

    def __init__(self) -> None:
        """Initialize the career engine."""
        logger.info("CareerEngine initialised")

    def analyze_trajectory(self, profile: CandidateProfile) -> dict[str, Any]:
        """
        Analyze candidate career trajectory, tenure patterns, and progression.

        Args:
            profile: Candidate profile with work experience.

        Returns:
            A dictionary containing analyzed metrics like promotion_count,
            tenure_trend (increasing/stable/decreasing), and average_tenure_months.
        """
        experience = profile.work_experience or []
        if not experience:
            return {
                "promotion_count": 0,
                "average_tenure_months": 0.0,
                "tenure_trend": "stable",
                "trajectory_class": "unknown",
                "growth_percentage": 0.0,
            }

        # Calculate average tenure
        tenures = [exp.duration_months for exp in experience if exp.duration_months is not None]
        avg_tenure = sum(tenures) / len(tenures) if tenures else 0.0

        # Look at title changes to count promotions (or seniority growth)
        promotions = 0
        seniority_levels = []

        # Simple keywords for seniority rank
        def get_rank(title: str) -> int:
            t = title.lower()
            if "intern" in t or "trainee" in t:
                return 0
            if "senior" in t or "sr" in t or "lead" in t:
                return 3
            if "staff" in t or "principal" in t:
                return 4
            if "manager" in t or "director" in t or "cto" in t or "head" in t:
                return 5
            return 2  # standard/mid

        for exp in reversed(experience):
            if exp.title:
                seniority_levels.append(get_rank(exp.title))

        # Count increases in seniority levels
        for i in range(1, len(seniority_levels)):
            if seniority_levels[i] > seniority_levels[i - 1]:
                promotions += 1

        # Determine trajectory classification
        trajectory_class = "stable"
        if promotions >= 2:
            trajectory_class = "fast_growth"
        elif promotions == 1:
            trajectory_class = "steady_growth"
        elif avg_tenure < 18.0 and len(experience) >= 3:
            trajectory_class = "job_hopper"

        return {
            "promotion_count": promotions,
            "average_tenure_months": avg_tenure,
            "tenure_trend": "increasing" if promotions > 0 else "stable",
            "trajectory_class": trajectory_class,
            "growth_percentage": min(100.0, promotions * 35.0),
        }
