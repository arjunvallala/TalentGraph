"""
TalentGraph AI — Candidate Intelligence Engine

Maps candidate feature vectors and profiles to a multidimensional CandidateGenome,
aggregating low-level metrics into recruiter-understandable dimension scores.
"""

from __future__ import annotations

from datetime import datetime

from shared.logging_setup import get_logger
from shared.types.candidate import (
    CandidateEvidence,
    CandidateFeatures,
    CandidateGenome,
    CandidateProfile,
)
from shared.utils.math_utils import clip

logger = get_logger(__name__)


class CandidateIntelligenceEngine:
    """
    Constructs candidate genomes from feature vectors, profile details,
    and evidence ledgers.
    """

    def __init__(self) -> None:
        """Initialize the candidate intelligence engine."""
        logger.info("CandidateIntelligenceEngine initialised")

    def build_genome(
        self,
        profile: CandidateProfile,
        features: CandidateFeatures,
        evidence: CandidateEvidence,
    ) -> CandidateGenome:
        """
        Aggregate features into a multi-dimensional CandidateGenome.

        Args:
            profile: Parsed candidate profile.
            features: Normalised candidate feature vector.
            evidence: Evidence ledger.

        Returns:
            Calculated CandidateGenome object.
        """
        # Composite aggregate formulas for 8 radar chart dimensions:

        # 1. Technical Capability: skill coverage + certifications
        tech_cap = features.skill_coverage * 0.6 + features.certifications_score * 0.4

        # 2. Career Progression: velocity + overall experience score
        career_prog = features.career_velocity * 0.5 + features.experience_score * 0.5

        # 3. Domain Expertise: domain match + consistency of skills
        domain_exp = features.domain_match * 0.7 + features.skill_consistency * 0.3

        # 4. Leadership Impact: leadership score direct
        leader_impact = features.leadership_score

        # 5. Learning Agility: education + research + certifications
        learning_agil = (
            features.education_score * 0.3
            + features.research_score * 0.3
            + features.learning_score * 0.4
        )

        # 6. Work Stability: stability score penalty-subtracted by job-hopping
        stability = features.stability_score * 0.7 + (1.0 - features.job_hop_risk) * 0.3

        # 7. Behavioral Signals: platform behavioral score + email/activity completeness
        behavior = features.behavior_score * 0.8 + features.profile_completeness * 0.2

        # 8. Hiring Readiness: notice availability - gap risk
        readiness = features.availability_score * 0.8 - features.gap_risk * 0.2

        # Apply clips to ensure bounds [0.0, 1.0]
        return CandidateGenome(
            candidate_id=profile.candidate_id,
            features=features,
            evidence=evidence,
            profile=profile,
            technical_capability=clip(tech_cap, 0.0, 1.0),
            career_progression=clip(career_prog, 0.0, 1.0),
            domain_expertise=clip(domain_exp, 0.0, 1.0),
            leadership_impact=clip(leader_impact, 0.0, 1.0),
            learning_agility=clip(learning_agil, 0.0, 1.0),
            work_stability=clip(stability, 0.0, 1.0),
            behavioral_signals=clip(behavior, 0.0, 1.0),
            hiring_readiness=clip(readiness, 0.0, 1.0),
            embedding_id=profile.embedding_id,
            computed_at=datetime.utcnow(),
        )
