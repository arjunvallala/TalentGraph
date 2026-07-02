"""
TalentGraph AI — Ranking Result Data Models

Defines models for ranking outputs, hiring recommendations,
submission rows, and stage-by-stage pipeline results.

Pipeline flow:
    CandidateGenome + CouncilDecision → CandidateResult → RankedList → SubmissionRow
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from shared.types.candidate import CandidateProfile, CandidateFeatures

# ── Enums ─────────────────────────────────────────────────────────────────────


class ConfidenceLevel(str, Enum):
    """Overall confidence in a hiring recommendation."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class HiringRecommendation(str, Enum):
    """
    Hiring committee's final recommendation.

    Thresholds (from constants.py):
        Strong Hire: score ≥ 0.82
        Hire:        score ≥ 0.68
        Consider:    score ≥ 0.52
        Pass:        score ≥ 0.38
        Reject:      score < 0.38
    """

    STRONG_HIRE = "Strong Hire"
    HIRE = "Hire"
    CONSIDER = "Consider"
    PASS = "Pass"
    REJECT = "Reject"


class RiskLevel(str, Enum):
    """Overall hiring risk classification."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    MINIMAL = "Minimal"


class ScoreBand(str, Enum):
    """Score band label for UI display."""

    EXCEPTIONAL = "Exceptional Match"
    STRONG = "Strong Match"
    GOOD = "Good Match"
    FAIR = "Potential Match"
    WEAK = "Weak Match"


# ── Explanation Models ────────────────────────────────────────────────────────


class ExplanationStrength(BaseModel):
    """A single identified strength for a candidate."""

    title: str
    description: str
    evidence: list[str] = Field(default_factory=list)
    score_contribution: float = Field(default=0.0, ge=0.0, le=1.0)


class ExplanationWeakness(BaseModel):
    """A single identified gap or weakness for a candidate."""

    title: str
    description: str
    missing_requirement: str | None = None
    impact: str = ""  # How this gap affects the recommendation


class CounterfactualExplanation(BaseModel):
    """
    Explains what would change the hiring recommendation.

    For rejected candidates: what they need to improve.
    For hired candidates: what risks the committee noted.
    """

    candidate_id: str
    current_recommendation: HiringRecommendation
    next_recommendation: HiringRecommendation | None = None
    required_improvements: list[str] = Field(default_factory=list)
    score_gap: float = 0.0  # How far from the next threshold


class CandidateExplanation(BaseModel):
    """
    Complete explanation for a candidate's ranking.

    This is the core explainability output — every ranked candidate
    has one of these, ensuring recruiters understand WHY the system
    made its recommendation.

    Attributes:
        candidate_id: Reference to the candidate.
        summary: One-sentence hiring summary.
        strengths: Top 3 identified strengths.
        weaknesses: Top 3 identified gaps.
        risk_summary: Plain-language risk description.
        hiring_narrative: Multi-sentence hiring narrative (recruiter-friendly).
        confidence_reason: Why confidence is HIGH/MEDIUM/LOW.
        counterfactual: What would change the recommendation.
        evidence_count: Total pieces of evidence found.
        generated_at: When this explanation was produced.
    """

    candidate_id: str
    summary: str = ""
    strengths: list[ExplanationStrength] = Field(default_factory=list)
    weaknesses: list[ExplanationWeakness] = Field(default_factory=list)
    risk_summary: str = ""
    hiring_narrative: str = ""
    confidence_reason: str = ""
    counterfactual: CounterfactualExplanation | None = None
    evidence_count: int = 0
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ── Risk Assessment ───────────────────────────────────────────────────────────


class RiskAssessment(BaseModel):
    """
    Structured hiring risk assessment for a candidate.

    Attributes:
        candidate_id: Reference to the candidate.
        risk_level: Overall risk classification.
        overall_risk_score: Composite risk score [0, 1].
        job_hop_risk: Job-hopping risk score [0, 1].
        gap_risk: Career gap risk score [0, 1].
        skill_inconsistency_risk: Skill coherence risk [0, 1].
        profile_completeness_risk: Incomplete profile risk [0, 1].
        engagement_risk: Low platform engagement risk [0, 1].
        risk_flags: List of specific risk flags identified.
        risk_explanations: Human-readable risk explanations.
        notice_period_days: Candidate's notice period.
    """

    candidate_id: str
    risk_level: RiskLevel = RiskLevel.MINIMAL
    overall_risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    job_hop_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    gap_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    skill_inconsistency_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    profile_completeness_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    engagement_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    risk_flags: list[str] = Field(default_factory=list)
    risk_explanations: list[str] = Field(default_factory=list)
    notice_period_days: int | None = None


# ── Stage Results ─────────────────────────────────────────────────────────────


class RankingStageResult(BaseModel):
    """
    Result from a single stage of the ranking pipeline.

    Attributes:
        stage: Stage number (1, 2, or 3).
        stage_name: Human-readable stage name.
        input_count: Number of candidates entering this stage.
        output_count: Number of candidates passing this stage.
        duration_seconds: Processing time.
        candidate_ids: IDs of candidates that passed this stage.
        scores: Map of candidate_id → stage score.
    """

    stage: int
    stage_name: str
    input_count: int
    output_count: int
    duration_seconds: float = 0.0
    candidate_ids: list[str] = Field(default_factory=list)
    scores: dict[str, float] = Field(default_factory=dict)


# ── Core Result Model ─────────────────────────────────────────────────────────


class CandidateResult(BaseModel):
    """
    Complete ranked result for a single candidate.

    This is the final output of the TalentGraph AI ranking pipeline.
    Contains everything a recruiter needs to make a hiring decision.

    Attributes:
        candidate_id: Unique candidate identifier.
        rank: Final rank position (1 = best match).
        overall_score: Composite hiring score [0, 1].
        score_band: Human-readable score label.
        confidence_level: Recommendation confidence level.
        hiring_recommendation: Committee's final recommendation.
        risk_assessment: Full risk breakdown.
        explanation: Complete explainability output.
        genome: Full candidate genome (for radar chart).
        stage1_score: Hybrid retrieval score.
        stage2_score: Feature ranking score.
        stage3_score: Hiring Council score.
        council_scores: Individual council evaluator scores.
        feature_scores: Individual feature scores against this JD.
        ranked_at: Timestamp of final ranking.
    """

    candidate_id: str
    rank: int = Field(default=0, ge=0)
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    score_band: ScoreBand = ScoreBand.WEAK
    confidence_level: ConfidenceLevel = ConfidenceLevel.LOW
    hiring_recommendation: HiringRecommendation = HiringRecommendation.PASS
    risk_assessment: RiskAssessment | None = None
    explanation: CandidateExplanation | None = None
    profile: CandidateProfile | None = None
    features: CandidateFeatures | None = None

    # Stage-by-stage scores
    stage1_score: float = Field(default=0.0, ge=0.0, le=1.0)
    stage2_score: float = Field(default=0.0, ge=0.0, le=1.0)
    stage3_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # Detailed breakdowns
    council_scores: dict[str, float] = Field(default_factory=dict)
    feature_scores: dict[str, float] = Field(default_factory=dict)

    ranked_at: datetime = Field(default_factory=datetime.utcnow)


class RankedList(BaseModel):
    """
    The full ranked output for a single job description.

    Attributes:
        job_id: Reference to the ranked job.
        candidates: Ordered list of candidate results (rank 1 first).
        total_processed: Total candidates in the corpus.
        stage_results: Per-stage pipeline statistics.
        ranking_duration_seconds: End-to-end pipeline time.
        ranked_at: When ranking completed.
    """

    job_id: str
    candidates: list[CandidateResult] = Field(default_factory=list)
    total_processed: int = 0
    stage_results: list[RankingStageResult] = Field(default_factory=list)
    ranking_duration_seconds: float = 0.0
    ranked_at: datetime = Field(default_factory=datetime.utcnow)


class SubmissionRow(BaseModel):
    """
    A single row in the submission.csv output.

    Attributes:
        candidate_id: Candidate unique identifier.
        rank: Final rank position (1-indexed).
        overall_score: Composite score [0, 1].
        confidence_level: Confidence classification string.
        hiring_recommendation: Final recommendation string.
    """

    candidate_id: str
    rank: int
    overall_score: float
    confidence_level: str
    hiring_recommendation: str
