"""
TalentGraph AI — Evidence-Grounded Explanation Generator

Generates recruiter-grade, deterministic explanations for candidate rankings.

DESIGN PRINCIPLE: Every sentence must be traceable to actual candidate data.
No template phrases like "exceptional skills" or "deep domain expertise" are
emitted unless the underlying feature value actually supports the claim.

Validation rule: before including a claim, the evidence gate is checked.
If the gate fails (feature below threshold), the claim is NOT included.
"""
from __future__ import annotations

from datetime import datetime
from typing import List

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


# ── Evidence Thresholds ─────────────────────────────────────────────────────
# A claim is only made when the supporting feature exceeds this threshold.
_THRESHOLDS = {
    "exceptional_technical":  0.80,  # skill_coverage + domain_match
    "solid_technical":        0.60,
    "strong_career":          0.75,  # career_velocity + promotion
    "strong_leadership":      0.70,
    "strong_learning":        0.70,
    "high_availability":      0.70,
    "low_risk":               0.75,  # 1 - max(job_hop_risk, gap_risk)
    "rich_profile":           0.70,  # profile_completeness
    "unanimous_council":      0.85,  # agreement_score
}


class ExplanationGenerator:
    """
    Orchestrates evidence-grounded explanations for each candidate recommendation.

    Every statement generated here is guarded by a feature threshold check.
    If the evidence does not exist in the candidate data, the statement is omitted.
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
        Synthesize a validated explanation for the candidate.

        Each claim is gated on a feature value threshold. Unsupported claims
        are silently dropped rather than hallucinated.

        Args:
            candidate_id: Candidate identifier.
            features: Candidate features (all values in [0, 1]).
            job_genome: Job genome targets.
            council_decision: Hiring council consensus details.
            recommendation: Overall recommendation tier.
            confidence_label: Text confidence level ("High", "Medium", "Low").

        Returns:
            CandidateExplanation with validated and evidence-backed content.
        """
        strengths = self.strength_analyzer.analyze(features, job_genome)
        weaknesses = self.weakness_analyzer.analyze(features, job_genome)

        counterfactual = self.counterfactual_engine.generate(
            candidate_id, recommendation, council_decision.final_score, features
        )

        score_pct = council_decision.final_score * 100

        # ── Safety accessors with fallbacks ──────────────────────────────────
        skill_cov = features.skill_coverage
        domain_m = features.domain_match
        career_vel = features.career_velocity if hasattr(features, 'career_velocity') else 0.0
        leadership = features.leadership_score
        availability = (
            features.hiring_availability
            if hasattr(features, 'hiring_availability')
            else features.availability_score
        )
        job_hop = features.job_hop_risk
        gap_r = features.gap_risk
        completeness = features.profile_completeness
        agreement = council_decision.agreement_score

        # ── Evidence Gates ────────────────────────────────────────────────────
        tech_score = (skill_cov + domain_m) / 2.0
        risk_safety = 1.0 - max(job_hop, gap_r)

        is_exceptional_technical = tech_score >= _THRESHOLDS["exceptional_technical"]
        is_solid_technical       = tech_score >= _THRESHOLDS["solid_technical"]
        is_strong_career         = career_vel >= _THRESHOLDS["strong_career"]
        is_strong_leadership     = leadership >= _THRESHOLDS["strong_leadership"]
        is_available             = availability >= _THRESHOLDS["high_availability"]
        is_low_risk              = risk_safety >= _THRESHOLDS["low_risk"]
        is_rich_profile          = completeness >= _THRESHOLDS["rich_profile"]
        is_council_unanimous     = agreement >= _THRESHOLDS["unanimous_council"]

        # ── Build Evidence-Backed Summary ─────────────────────────────────────
        summary_parts: List[str] = []
        if is_exceptional_technical:
            summary_parts.append(
                f"exceptional skill-to-JD alignment ({tech_score * 100:.0f}% coverage)"
            )
        elif is_solid_technical:
            summary_parts.append(
                f"solid technical alignment ({tech_score * 100:.0f}% coverage)"
            )
        if is_strong_career:
            summary_parts.append(f"strong career velocity ({career_vel:.2f})")
        if is_strong_leadership:
            summary_parts.append(f"demonstrated leadership signals ({leadership:.2f})")
        if not summary_parts:
            summary_parts.append("standard qualifications across the evaluated dimensions")

        summary = (
            f"Ranked at {score_pct:.1f}% based on: "
            + "; ".join(summary_parts) + "."
        )

        # ── Build Risk Summary (evidence-gated) ───────────────────────────────
        risk_parts: List[str] = []
        if job_hop > 0.4:
            risk_parts.append(f"job-hopping risk flag (score {job_hop:.2f})")
        if gap_r > 0.3:
            risk_parts.append(f"career gap flag (score {gap_r:.2f})")
        if not risk_parts:
            risk_summary = "No significant risk factors detected in career history."
        else:
            risk_summary = "Risk flags noted: " + "; ".join(risk_parts) + "."

        # ── Build Hiring Narrative (evidence-gated) ───────────────────────────
        narrative_parts: List[str] = [
            f"Composite pipeline score: {score_pct:.1f}%."
        ]

        if is_exceptional_technical:
            narrative_parts.append(
                f"Technical evaluation shows {skill_cov * 100:.0f}% skill coverage "
                f"and {domain_m * 100:.0f}% domain alignment against the job requirements."
            )
        elif is_solid_technical:
            narrative_parts.append(
                f"Skill coverage: {skill_cov * 100:.0f}%. Domain match: {domain_m * 100:.0f}%."
            )
        else:
            narrative_parts.append(
                f"Skill coverage ({skill_cov * 100:.0f}%) is below the target threshold."
            )

        if is_strong_career:
            narrative_parts.append(
                f"Career velocity score of {career_vel:.2f} reflects faster-than-average "
                f"advancement to their current seniority level."
            )
        if is_strong_leadership:
            narrative_parts.append(
                f"Leadership signals present at {leadership:.2f} — consistent with a "
                f"senior or managerial track."
            )
        if is_available:
            narrative_parts.append(
                f"Candidate is available promptly (availability score: {availability:.2f})."
            )
        if is_council_unanimous:
            narrative_parts.append(
                f"All 5 hiring council members reached consensus "
                f"(agreement score: {agreement:.2f})."
            )
        elif agreement < 0.5:
            narrative_parts.append(
                f"Note: Council agreement was low ({agreement:.2f}), indicating differing "
                f"expert views — manual review recommended."
            )

        if risk_parts:
            narrative_parts.append(risk_summary)

        hiring_narrative = " ".join(narrative_parts)

        # ── Build Confidence Reason (evidence-gated) ──────────────────────────
        conf_reasons: List[str] = []
        if is_rich_profile:
            conf_reasons.append(f"complete profile data ({completeness * 100:.0f}% populated)")
        else:
            conf_reasons.append(
                f"limited profile data ({completeness * 100:.0f}% populated) — confidence reduced"
            )
        if is_council_unanimous:
            conf_reasons.append(f"high council agreement ({agreement:.2f})")
        elif agreement < 0.6:
            conf_reasons.append(f"low council agreement ({agreement:.2f})")
        confidence_reason = (
            f"Confidence is {confidence_label.lower()}. "
            + "Based on: " + "; ".join(conf_reasons) + "."
        )

        # ── Evidence Count ─────────────────────────────────────────────────────
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
