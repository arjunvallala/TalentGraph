"""
TalentGraph AI — Hiring Council Data Models

Defines models for individual council evaluator outputs, votes,
and the final consensus decision.

Each council evaluator independently assesses one aspect of a candidate
and produces a CouncilVote. The HiringCouncil combines all votes
into a FinalCouncilDecision.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CouncilType(str, Enum):
    """Identifies which council member produced an evaluation."""

    TECHNICAL = "technical_council"
    CAREER = "career_council"
    BEHAVIOR = "behavior_council"
    GROWTH = "growth_council"
    RISK = "risk_council"


class CouncilVote(BaseModel):
    """
    A single council evaluator's vote on a candidate.

    Produced independently by each of the 5 council evaluators.
    All votes are then combined by the Final Council into a consensus.

    Attributes:
        council_type: Which evaluator produced this vote.
        candidate_id: Candidate being evaluated.
        score: Overall score from this evaluator [0, 1].
        confidence: Evaluator's confidence in its own score [0, 1].
        recommendation: This evaluator's hiring recommendation.
        dimension_scores: Breakdown by evaluation dimension.
        strengths: Top findings that support hiring.
        concerns: Top concerns that argue against hiring.
        evidence: Specific evidence references from the profile.
        rationale: One-sentence evaluation rationale.
        evaluated_at: Timestamp of evaluation.
    """

    council_type: CouncilType
    candidate_id: str
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    recommendation: str = ""
    dimension_scores: dict[str, float] = Field(default_factory=dict)
    strengths: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    rationale: str = ""
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


class CouncilEvaluationResult(BaseModel):
    """
    All council votes for a single candidate.

    Produced by running all 5 evaluators (potentially in parallel)
    and collecting their votes before consensus.

    Attributes:
        candidate_id: Candidate being evaluated.
        votes: Map of council_type → CouncilVote.
        evaluation_duration_seconds: Total parallel evaluation time.
        all_voted: True if all 5 evaluators produced a vote.
        failed_councils: List of council types that failed/timed out.
    """

    candidate_id: str
    votes: dict[str, CouncilVote] = Field(default_factory=dict)
    evaluation_duration_seconds: float = 0.0
    all_voted: bool = False
    failed_councils: list[str] = Field(default_factory=list)

    def get_vote(self, council_type: CouncilType) -> CouncilVote | None:
        """Retrieve a specific council's vote by type."""
        return self.votes.get(council_type.value)

    @property
    def vote_count(self) -> int:
        """Number of votes cast."""
        return len(self.votes)


class FinalCouncilDecision(BaseModel):
    """
    The Hiring Council's final consensus decision on a candidate.

    Produced by combining all individual CouncilVotes using
    a weighted average approach. This is the last step before
    the Explainability Engine generates narratives.

    Attributes:
        candidate_id: Candidate evaluated.
        council_score: Weighted consensus score [0, 1].
        council_confidence: Confidence in the consensus [0, 1].
        agreement_score: How much council members agreed [0, 1].
        individual_scores: Map of council_type → score.
        individual_confidences: Map of council_type → confidence.
        all_strengths: Merged strengths from all councils.
        all_concerns: Merged concerns from all councils.
        decisive_factors: Top factors that most influenced the decision.
        dissenting_opinion: If one evaluator strongly disagreed.
        risk_penalty_applied: Risk penalty subtracted from consensus.
        final_score: council_score - risk_penalty_applied.
        decided_at: Timestamp of consensus.
    """

    candidate_id: str
    council_score: float = Field(default=0.0, ge=0.0, le=1.0)
    council_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    agreement_score: float = Field(default=0.0, ge=0.0, le=1.0)
    individual_scores: dict[str, float] = Field(default_factory=dict)
    individual_confidences: dict[str, float] = Field(default_factory=dict)
    all_strengths: list[str] = Field(default_factory=list)
    all_concerns: list[str] = Field(default_factory=list)
    decisive_factors: list[str] = Field(default_factory=list)
    dissenting_opinion: str | None = None
    risk_penalty_applied: float = Field(default=0.0, ge=0.0, le=1.0)
    final_score: float = Field(default=0.0, ge=0.0, le=1.0)
    decided_at: datetime = Field(default_factory=datetime.utcnow)
