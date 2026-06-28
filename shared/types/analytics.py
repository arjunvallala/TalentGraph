"""
TalentGraph AI — Analytics Data Models

Defines models for dashboard analytics, hiring funnel statistics,
feature importance, candidate distributions, and risk breakdowns.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class HiringFunnelStats(BaseModel):
    """
    Statistics for the hiring funnel waterfall chart.

    Shows how many candidates passed each stage of the pipeline.

    Attributes:
        total_candidates: Total candidates in the corpus.
        stage1_output: Candidates after hybrid retrieval.
        stage2_output: Candidates after feature ranking.
        stage3_output: Candidates after Hiring Council.
        final_output: Final shortlisted candidates.
        stage1_retention_rate: Fraction retained after Stage 1.
        stage2_retention_rate: Fraction retained after Stage 2.
        stage3_retention_rate: Fraction retained after Stage 3.
    """
    total_candidates: int = 0
    stage1_output: int = 0
    stage2_output: int = 0
    stage3_output: int = 0
    final_output: int = 0
    stage1_retention_rate: float = 0.0
    stage2_retention_rate: float = 0.0
    stage3_retention_rate: float = 0.0
    processing_time_seconds: float = 0.0


class FeatureImportance(BaseModel):
    """
    Feature importance analysis for the ranked candidate set.

    Attributes:
        feature_name: Name of the feature.
        importance_score: Relative importance [0, 1].
        avg_score_top10: Average feature score for top-10 candidates.
        avg_score_all: Average feature score for all candidates.
        label: Human-readable feature label.
        description: Brief description of the feature.
    """
    feature_name: str
    importance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_score_top10: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_score_all: float = Field(default=0.0, ge=0.0, le=1.0)
    label: str = ""
    description: str = ""


class CandidateDistribution(BaseModel):
    """
    Distribution statistics for the candidate pool.

    Attributes:
        score_histogram: Bucketed score distribution (10 buckets).
        experience_distribution: Count by experience band.
        education_distribution: Count by education level.
        domain_distribution: Count by primary domain.
        location_distribution: Count by top locations.
        availability_distribution: Count by availability status.
    """
    score_histogram: dict[str, int] = Field(default_factory=dict)
    experience_distribution: dict[str, int] = Field(default_factory=dict)
    education_distribution: dict[str, int] = Field(default_factory=dict)
    domain_distribution: dict[str, int] = Field(default_factory=dict)
    location_distribution: dict[str, int] = Field(default_factory=dict)
    availability_distribution: dict[str, int] = Field(default_factory=dict)


class RiskBreakdown(BaseModel):
    """
    Aggregated risk analysis across the ranked candidate set.

    Attributes:
        risk_level_distribution: Count of candidates by risk level.
        avg_job_hop_risk: Average job-hopping risk score.
        avg_gap_risk: Average career gap risk score.
        critical_risk_candidates: Count of candidates with critical risk.
        top_risk_flags: Most common risk flags encountered.
    """
    risk_level_distribution: dict[str, int] = Field(default_factory=dict)
    avg_job_hop_risk: float = 0.0
    avg_gap_risk: float = 0.0
    critical_risk_candidates: int = 0
    high_risk_candidates: int = 0
    top_risk_flags: list[str] = Field(default_factory=list)


class ConfidenceDistribution(BaseModel):
    """Distribution of confidence levels in the ranked output."""
    high_confidence: int = 0
    medium_confidence: int = 0
    low_confidence: int = 0
    avg_confidence: float = 0.0


class AnalyticsSummary(BaseModel):
    """
    Complete analytics summary for the recruiter dashboard.

    Aggregated from the ranking pipeline output.
    Powers all charts on the Analytics page.

    Attributes:
        job_id: Reference to the analysed job.
        funnel: Hiring funnel statistics.
        feature_importance: Ranked feature importance list.
        candidate_distribution: Score and demographic distributions.
        risk_breakdown: Risk analysis across the candidate pool.
        confidence_distribution: Confidence level breakdown.
        recommendation_distribution: Count by hiring recommendation.
        top_skills: Most common skills in top-100 candidates.
        skill_gap_analysis: Skills most missing in the candidate pool.
        generated_at: When this summary was produced.
    """
    job_id: str
    funnel: HiringFunnelStats = Field(default_factory=HiringFunnelStats)
    feature_importance: list[FeatureImportance] = Field(default_factory=list)
    candidate_distribution: CandidateDistribution = Field(
        default_factory=CandidateDistribution
    )
    risk_breakdown: RiskBreakdown = Field(default_factory=RiskBreakdown)
    confidence_distribution: ConfidenceDistribution = Field(
        default_factory=ConfidenceDistribution
    )
    recommendation_distribution: dict[str, int] = Field(default_factory=dict)
    top_skills: list[str] = Field(default_factory=list)
    skill_gap_analysis: list[str] = Field(default_factory=list)
    avg_overall_score: float = 0.0
    generated_at: datetime = Field(default_factory=datetime.utcnow)
