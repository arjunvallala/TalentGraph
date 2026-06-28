"""
TalentGraph AI — Shared Types Package

Exports all Pydantic models used across the platform.
"""

from shared.types.analytics import (
    AnalyticsSummary,
    CandidateDistribution,
    FeatureImportance,
    HiringFunnelStats,
    RiskBreakdown,
)
from shared.types.candidate import (
    AvailabilityStatus,
    CandidateEvidence,
    CandidateFeatures,
    CandidateGenome,
    CandidateProfile,
    EducationEntry,
    EducationLevel,
    RedrobSignals,
    WorkExperience,
)
from shared.types.council import (
    CouncilEvaluationResult,
    CouncilType,
    CouncilVote,
    FinalCouncilDecision,
)
from shared.types.job import (
    ExperienceLevel,
    IdealCandidatePersona,
    JobGenome,
    JobProfile,
    JobRaw,
    JobType,
    SkillRequirement,
)
from shared.types.ranking import (
    CandidateResult,
    HiringRecommendation,
    RankedList,
    RankingStageResult,
    SubmissionRow,
)

__all__ = [
    # Candidate
    "AvailabilityStatus",
    "CandidateEvidence",
    "CandidateFeatures",
    "CandidateGenome",
    "CandidateProfile",
    "EducationEntry",
    "EducationLevel",
    "RedrobSignals",
    "WorkExperience",
    # Job
    "ExperienceLevel",
    "IdealCandidatePersona",
    "JobGenome",
    "JobProfile",
    "JobRaw",
    "JobType",
    "SkillRequirement",
    # Ranking
    "CandidateResult",
    "HiringRecommendation",
    "RankedList",
    "RankingStageResult",
    "SubmissionRow",
    # Council
    "CouncilEvaluationResult",
    "CouncilType",
    "CouncilVote",
    "FinalCouncilDecision",
    # Analytics
    "AnalyticsSummary",
    "CandidateDistribution",
    "FeatureImportance",
    "HiringFunnelStats",
    "RiskBreakdown",
]
