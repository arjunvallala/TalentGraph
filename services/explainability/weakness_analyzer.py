"""
TalentGraph AI — Weakness Analyzer

Identifies a candidate's top 3 weaknesses or gaps compared to job requirements
based on feature score differentials.
"""
from __future__ import annotations

from typing import List, Optional
from shared.types.candidate import CandidateFeatures
from shared.types.job import JobGenome
from shared.types.ranking import ExplanationWeakness


class WeaknessAnalyzer:
    """
    Analyzes candidate features against job genome targets to identify top gaps.
    """

    def __init__(self) -> None:
        """Initialize weakness analyzer."""
        pass

    def analyze(
        self, features: CandidateFeatures, job: JobGenome
    ) -> List[ExplanationWeakness]:
        """
        Identify top 3 weaknesses/gaps for the candidate.

        Args:
            features: Candidate features.
            job: Job genome targets.

        Returns:
            A list of up to 3 ExplanationWeakness objects.
        """
        gaps = []

        # Compare features against job targets and add gaps
        if features.skill_coverage < 0.5:
            gaps.append(
                ExplanationWeakness(
                    title="Skill Set Gaps",
                    description=f"Only matches {(features.skill_coverage * 100):.0f}% of the required skills.",
                    missing_requirement="Core required technical skills",
                    impact="Candidate will require onboarding time to master required tech stack.",
                )
            )

        if features.experience_score < 0.4:
            gaps.append(
                ExplanationWeakness(
                    title="Limited Years of Experience",
                    description="Total professional experience is below the job's ideal seniority target.",
                    missing_requirement="Seniority expectations",
                    impact="Potential challenge in leading complex initiatives independently.",
                )
            )

        if features.job_hop_risk > 0.6:
            gaps.append(
                ExplanationWeakness(
                    title="Tenure Instability",
                    description="Frequent transitions between employers within short timeframes.",
                    missing_requirement="Minimum tenure stability",
                    impact="Risk of early attrition before full onboarding ROI is realized.",
                )
            )

        if features.gap_risk > 0.6:
            gaps.append(
                ExplanationWeakness(
                    title="Significant Employment Gap",
                    description="Extended unexplained period of unemployment between roles.",
                    missing_requirement="Continuous career progression",
                    impact="Candidate might need refresher onboarding for technical currency.",
                )
            )

        # Truncate to top 3
        return gaps[:3]
