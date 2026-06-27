"""
TalentGraph AI — Explanation Generator

Generates complete, recruiter-grade deterministic explanations for candidate rankings.
Combines strengths, weaknesses, risk summaries, and counterfactuals.
"""
from __future__ import annotations

from datetime import datetime
from shared.types.candidate import CandidateFeatures
from shared.types.ranking import (
    CandidateExplanation,
    HiringRecommendation,
)
from services.explainability.strength_analyzer import StrengthAnalyzer
from services.explainability.weakness_analyzer import WeaknessAnalyzer
from services.explainability.counterfactual import CounterfactualEngine
from shared.types.job import JobGenome
from shared.types.council import FinalCouncilDecision


class ExplanationGenerator:
    """
    Orchestrates the creation of detailed explanations for each candidate recommendation.
    """

    def __init__(self) -> None:
        """Initialize explanation generator."""
        self.strength_analyzer = StrengthAnalyzer()
        self.weakness_analyzer = WeaknessAnalyzer()
        self.counterfactual_engine = CounterfactualEngine()

    def generate_explanation(
        self,
        candidate_id: str,
        features: CandidateFeatures,
        job_genome: JobGenome,
        council_decision: FinalCouncilDecision,
        recommendation: HiringRecommendation,
        confidence_label: str,
    ) -> CandidateExplanation:
        """
        Synthesize detailed explanation objects for the candidate.

        Args:
            candidate_id: Candidate identifier.
            features: Candidate features.
            job_genome: Job genome targets.
            council_decision: Hiring council consensus details.
            recommendation: Overall recommendation tier.
            confidence_label: Text confidence level ("High", "Medium", "Low").

        Returns:
            CandidateExplanation containing all parsed and compiled descriptions.
        """
        strengths = self.strength_analyzer.analyze(features, job_genome)
        weaknesses = self.weakness_analyzer.analyze(features, job_genome)
        
        counterfactual = self.counterfactual_engine.generate(
            candidate_id, recommendation, council_decision.final_score, features
        )

        # Build custom summaries and narratives based on scores
        score_pct = council_decision.final_score * 100
        
        if recommendation == HiringRecommendation.STRONG_HIRE:
            summary = "Highly recommended candidate with exceptional skills and experience alignment."
            risk_summary = "Very low risk profile. Minimal concerns regarding tenure or transition."
            hiring_narrative = (
                f"The candidate is a top-tier fit for this position, matching the ideal requirements "
                f"with a final score of {score_pct:.1f}%. Their deep domain expertise and career velocity "
                f"make them an immediate asset."
            )
            confidence_reason = "High confidence is supported by rich profile history and unanimous council consensus."
        
        elif recommendation == HiringRecommendation.HIRE:
            summary = "Recommended candidate meeting all core technical requirements."
            risk_summary = "Low risk profile. Stable professional background."
            hiring_narrative = (
                f"The candidate matches core expectations (score {score_pct:.1f}%) and is a reliable "
                f"hire. They possess the required skills but may require onboarding in secondary tech areas."
            )
            confidence_reason = "Medium to High confidence backed by verified qualifications and positive platform engagement."

        elif recommendation == HiringRecommendation.CONSIDER:
            summary = "Potential match worth considering for interview stage."
            risk_summary = "Moderate risk flags. Average tenure is stable but minor gaps exist."
            hiring_narrative = (
                f"The candidate is a consideration (score {score_pct:.1f}%). They have good experience "
                f"but lack direct match on several preferred requirements. A technical interview is advised."
            )
            confidence_reason = "Medium confidence due to minor gaps in required skills list."

        elif recommendation == HiringRecommendation.PASS:
            summary = "Backup candidate with significant technical or experience gaps."
            risk_summary = "Elevated risk warning: short average tenures or long gaps."
            hiring_narrative = (
                f"The candidate falls below active hiring thresholds (score {score_pct:.1f}%). Gaps in core "
                f"competencies suggest they are not a primary match."
            )
            confidence_reason = "Lower confidence due to sparse profile details or low skill coverage."

        else: # Reject
            summary = "Not recommended for this role."
            risk_summary = "High risk profile: frequent transitions or incomplete work records."
            hiring_narrative = (
                f"The candidate is not suited for the role (score {score_pct:.1f}%). Significant alignment gaps "
                f"exist across technical capability and stability dimensions."
            )
            confidence_reason = "Low confidence due to severe gaps in essential profile sections."

        # Count total evidence pieces
        evidence_count = 0
        for s in strengths:
            evidence_count += len(s.evidence)
        
        return CandidateExplanation(
            candidate_id=candidate_id,
            summary=summary,
            strengths=strengths,
            weaknesses=weaknesses,
            risk_summary=risk_summary,
            hiring_narrative=hiring_narrative,
            confidence_reason=confidence_reason,
            counterfactual=counterfactual,
            evidence_count=max(1, evidence_count),
            generated_at=datetime.utcnow(),
        )
