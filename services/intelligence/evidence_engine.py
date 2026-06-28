"""
TalentGraph AI — Evidence Ledger Engine

Extracts explicit evidence (skills mentioned, specific companies, dates, degrees)
from a candidate's profile and links them to the computed feature scores.
"""

from __future__ import annotations

from shared.logging_setup import get_logger
from shared.types.candidate import (
    CandidateEvidence,
    CandidateFeatures,
    CandidateProfile,
)

logger = get_logger(__name__)


class EvidenceEngine:
    """
    Constructs an audit trail (Evidence Ledger) linking candidate scores to raw profile facts.
    """

    def __init__(self) -> None:
        """Initialize the evidence engine."""
        logger.info("EvidenceEngine initialised")

    def build_ledger(
        self, profile: CandidateProfile, features: CandidateFeatures
    ) -> CandidateEvidence:
        """
        Compile evidence maps and timelines for the candidate profile.

        Args:
            profile: Candidate profile containing raw data.
            features: Computed normalized features.

        Returns:
            CandidateEvidence containing the structured evidence ledger.
        """
        skill_evidence_map: dict[str, list[str]] = {}
        for s in profile.skills or []:
            skill_evidence_map[s] = [f"Found skill '{s}' mentioned in candidate profile."]

        experience_evidence = [
            f"Candidate has {profile.years_of_experience:.1f} years of total professional experience.",
            f"Current title is '{profile.current_title or 'Not specified'}' at '{profile.current_company or 'Not specified'}'.",
        ]

        edu_list = profile.education or []
        learning_evidence = []
        for e in edu_list:
            deg = e.degree or "Degree"
            inst = e.institution or "Institution"
            yr = f" ({e.end_year})" if e.end_year else ""
            learning_evidence.append(f"Completed {deg} from {inst}{yr}.")
        if not learning_evidence:
            learning_evidence.append("No formal education records listed.")
        if profile.certifications:
            learning_evidence.append(f"Certifications: {', '.join(profile.certifications)}.")

        stability_evidence = []
        if profile.work_experience:
            stability_evidence.append(
                f"Worked at {len(profile.work_experience)} distinct companies."
            )
            tenures = [
                exp.duration_months for exp in profile.work_experience if exp.duration_months
            ]
            if tenures:
                avg = sum(tenures) / len(tenures)
                stability_evidence.append(f"Average employment tenure is {avg:.1f} months.")
        else:
            stability_evidence.append("No formal work experience records found.")

        leader_evidence = []
        if features.leadership_score > 0.6:
            leader_evidence.append(
                "Strong leadership indicators: title contains 'lead', 'manager', or 'head'."
            )
        elif features.leadership_score > 0.3:
            leader_evidence.append(
                "Moderate leadership signals: profile contains mentoring or coordination keywords."
            )
        else:
            leader_evidence.append("Mainly individual contributor technical focus.")

        sig = profile.redrob_signals
        behavior_evidence = [f"Hiring status: '{sig.availability_status.value}'."]
        if sig.notice_period_days is not None:
            behavior_evidence.append(f"Notice period: {sig.notice_period_days} days.")
        behavior_evidence.append(
            f"Platform interaction: {sig.profile_views} profile views, {sig.application_count} applications."
        )

        risk_evidence = []
        if features.job_hop_risk > 0.6:
            risk_evidence.append("High job-hopping risk: average tenure is low.")
        if features.gap_risk > 0.6:
            risk_evidence.append("Significant employment gaps detected.")

        return CandidateEvidence(
            candidate_id=profile.candidate_id,
            skill_evidence=skill_evidence_map,
            experience_evidence=experience_evidence,
            leadership_evidence=leader_evidence,
            learning_evidence=learning_evidence,
            stability_evidence=stability_evidence,
            risk_evidence=risk_evidence,
            behavior_evidence=behavior_evidence,
            evidence_strength=0.9,
        )
