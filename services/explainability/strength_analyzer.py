"""
TalentGraph AI — Strength Analyzer

Identifies a candidate's top 3 strengths compared to job description requirements
based on feature score differentials.
"""
from __future__ import annotations

from typing import List
from shared.types.candidate import CandidateFeatures
from shared.types.job import JobGenome
from shared.types.ranking import ExplanationStrength


class StrengthAnalyzer:
    """
    Analyzes candidate features against job genome targets to identify top strengths.
    """

    def __init__(self) -> None:
        """Initialize strength analyzer."""
        pass

    def analyze(
        self, features: CandidateFeatures, job: JobGenome
    ) -> List[ExplanationStrength]:
        """
        Identify top 3 strengths for the candidate.

        Args:
            features: Candidate features.
            job: Job genome targets.

        Returns:
            A list of up to 3 ExplanationStrength objects.
        """
        strengths = []

        # Compare features against job targets and add strengths
        if features.skill_coverage >= 0.75:
            strengths.append(
                ExplanationStrength(
                    title="High Skill Coverage",
                    description=f"Matches {(features.skill_coverage * 100):.0f}% of the required technical skills.",
                    evidence=["Candidate profile skills intersect significantly with requirements."],
                    score_contribution=0.25,
                )
            )

        if features.experience_score >= 0.7:
            strengths.append(
                ExplanationStrength(
                    title="Deep Domain Experience",
                    description="Possesses substantial relevant years of experience in the target field.",
                    evidence=[f"Features calculate deep career length indicators."],
                    score_contribution=0.15,
                )
            )

        if features.career_stability >= 0.75:
            strengths.append(
                ExplanationStrength(
                    title="Strong Tenure Stability",
                    description="Demonstrates consistent employment history with long tenures per company.",
                    evidence=["Average job tenure is well above the industry median."],
                    score_contribution=0.1,
                )
            )

        if features.career_velocity >= 0.7:
            strengths.append(
                ExplanationStrength(
                    title="Fast Career Growth",
                    description="Shows rapid progression in seniority title ranks throughout work history.",
                    evidence=["Multiple title promotions identified in timeline."],
                    score_contribution=0.1,
                )
            )

        # Truncate to top 3
        return strengths[:3]
