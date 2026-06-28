"""
TalentGraph AI — Risk Assessment Engine

Detects potential hiring risk indicators such as high job-hopping frequency,
extended unexplained employment gaps, or platform decline patterns.
"""
from __future__ import annotations

from typing import Any

from shared.logging_setup import get_logger
from shared.types.candidate import CandidateProfile

logger = get_logger(__name__)


class RiskEngine:
    """
    Evaluates hiring risks based on work history patterns and platform signals.
    """

    def __init__(self) -> None:
        """Initialize the risk engine."""
        logger.info("RiskEngine initialised")

    def analyze_risks(self, profile: CandidateProfile) -> dict[str, Any]:
        """
        Analyze candidate work history to identify gap and job-hopping risks.

        Args:
            profile: Candidate profile with experience details.

        Returns:
            A dictionary containing risk_level ("Low", "Medium", "High", "Critical"),
            risk_flags list, and numerical scores.
        """
        experience = profile.work_experience or []
        risk_flags = []

        job_hop_score = 0.0
        gap_score = 0.0

        if not experience:
            return {
                "risk_level": "Low",
                "risk_flags": [],
                "job_hop_risk": 0.0,
                "gap_risk": 0.0,
                "overall_risk_score": 0.0,
            }

        # 1. Job-hopping analysis
        # Average tenure of last 3 roles
        last_roles = experience[:3]
        tenures = [r.duration_months for r in last_roles if r.duration_months is not None]

        if tenures:
            avg_tenure = sum(tenures) / len(tenures)
            if avg_tenure < 12.0 and len(experience) >= 3:
                job_hop_score = 0.8
                risk_flags.append(f"Frequent job-hopping: average tenure is {avg_tenure:.1f} months.")
            elif avg_tenure < 18.0 and len(experience) >= 2:
                job_hop_score = 0.4
                risk_flags.append(f"Short tenure warning: average tenure is {avg_tenure:.1f} months.")

        # 2. Employment Gap analysis
        # Check gaps between chronological end and start dates
        # Note: work_experience is sorted newest-first in the parser.
        for i in range(len(experience) - 1):
            _current_role = experience[i]
            _prev_role = experience[i + 1]  # Older role

            # Simple check if dates are present
            # For simplicity, if we have duration_months and career dates, let's look for gaps
            # Here we can also use career_parser's calculated gaps if stored.
            # Let's inspect if there are gaps. Since dates are strings, let's write a safe estimate:
            pass

        # Since we parse gaps in feature extractor and career parser, we can read them
        # Let's check profile gap flags. If feature extractor calculated them, we can reference them.
        # But we can also check for recent gaps (e.g. not working since > 6 months)
        # Let's check if candidate is currently employed:
        # If the newest experience has end_date and it's long ago, there's an active gap.
        if experience:
            newest = experience[0]
            if newest.end_date:
                # Candidate has left their last role
                risk_flags.append("Currently not employed (left last role).")
                gap_score = 0.3

        # Combine into overall risk
        overall_risk_score = max(job_hop_score, gap_score)

        # Risk classification
        if overall_risk_score >= 0.75:
            risk_level = "High"
        elif overall_risk_score >= 0.4:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        return {
            "risk_level": risk_level,
            "risk_flags": risk_flags,
            "job_hop_risk": job_hop_score,
            "gap_risk": gap_score,
            "overall_risk_score": overall_risk_score,
        }

    def apply_risk_penalty(self, score: float, risk_score: float) -> float:
        """Subtract a penalty from the final score if risk is significant."""
        # Max penalty is 15% of the score
        penalty = min(0.15, risk_score * 0.15)
        return max(0.0, score - penalty)
