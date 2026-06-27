"""
TalentGraph AI — Candidate Data Models

Defines all Pydantic models related to candidate profiles,
engineered features, evidence, and the multidimensional genome.

These models flow through the entire pipeline:
    CSV Row → CandidateProfile → CandidateFeatures → CandidateGenome → CandidateResult
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ── Enums ─────────────────────────────────────────────────────────────────────

class AvailabilityStatus(str, Enum):
    """Candidate's current job-seeking status."""
    IMMEDIATELY_AVAILABLE = "immediately_available"
    NOTICE_PERIOD = "notice_period"
    NOT_LOOKING = "not_looking"
    OPEN_TO_OPPORTUNITIES = "open_to_opportunities"
    UNKNOWN = "unknown"


class EducationLevel(str, Enum):
    """Standardised education qualification levels."""
    HIGH_SCHOOL = "high_school"
    DIPLOMA = "diploma"
    BACHELORS = "bachelors"
    MASTERS = "masters"
    PHD = "phd"
    MBA = "mba"
    OTHER = "other"
    UNKNOWN = "unknown"


# ── Sub-Models ────────────────────────────────────────────────────────────────

class EducationEntry(BaseModel):
    """
    A single education record extracted from the candidate profile.

    Attributes:
        institution: Name of the educational institution.
        degree: Degree or qualification obtained.
        field_of_study: Major or specialisation.
        level: Standardised education level enum.
        start_year: Year education began.
        end_year: Year education completed (None if ongoing).
        gpa: Grade point average, if available.
        is_current: True if this is an ongoing qualification.
    """
    institution: str = ""
    degree: str = ""
    field_of_study: Optional[str] = None
    level: EducationLevel = EducationLevel.UNKNOWN
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    gpa: Optional[float] = None
    is_current: bool = False

    @field_validator("gpa")
    @classmethod
    def validate_gpa(cls, v: Optional[float]) -> Optional[float]:
        """Clamp GPA to [0.0, 10.0] to handle both 4.0 and 10.0 scales."""
        if v is not None:
            return max(0.0, min(v, 10.0))
        return v


class WorkExperience(BaseModel):
    """
    A single employment record from the candidate's career history.

    Attributes:
        company: Employer name.
        title: Job title or designation.
        start_date: Employment start (ISO string or human-readable).
        end_date: Employment end (ISO string, 'Present', or None).
        is_current: True if this is the candidate's current role.
        duration_months: Pre-computed tenure in months.
        description: Role description or responsibilities text.
        skills_used: Skills explicitly mentioned for this role.
        location: Office/work location.
        company_size: Company size descriptor (startup, mid-size, enterprise).
        industry: Industry sector.
    """
    company: str = ""
    title: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    duration_months: Optional[int] = None
    description: Optional[str] = None
    skills_used: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None

    @field_validator("duration_months")
    @classmethod
    def clamp_duration(cls, v: Optional[int]) -> Optional[int]:
        """Clamp tenure to realistic range."""
        if v is not None:
            return max(0, min(v, 600))  # 0 to 50 years
        return v


class RedrobSignals(BaseModel):
    """
    Behavioral and engagement signals from the Redrob hiring platform.

    These signals represent real-world recruiter-candidate interaction data
    and are used by the Behavior Council for hiring readiness assessment.

    Attributes:
        profile_views: Total number of times this profile has been viewed.
        application_count: Number of job applications submitted.
        response_rate: Fraction of recruiter messages responded to (0.0–1.0).
        last_active_days: Days since last platform activity (lower = more active).
        availability_status: Current job-seeking status.
        notice_period_days: Required notice period before joining.
        expected_salary: Expected salary in INR (if provided).
        preferred_locations: List of preferred work locations.
        open_to_remote: Whether the candidate is open to remote work.
        interview_declined_count: Number of scheduled interviews declined.
        offer_declined_count: Number of job offers declined.
    """
    profile_views: int = Field(default=0, ge=0)
    application_count: int = Field(default=0, ge=0)
    response_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    last_active_days: Optional[int] = Field(default=None, ge=0)
    availability_status: AvailabilityStatus = AvailabilityStatus.UNKNOWN
    notice_period_days: Optional[int] = Field(default=None, ge=0, le=365)
    expected_salary: Optional[float] = Field(default=None, ge=0)
    preferred_locations: List[str] = Field(default_factory=list)
    open_to_remote: bool = False
    interview_declined_count: int = Field(default=0, ge=0)
    offer_declined_count: int = Field(default=0, ge=0)


# ── Core Models ───────────────────────────────────────────────────────────────

class CandidateProfile(BaseModel):
    """
    Complete candidate profile with all available data.

    This is the primary data model produced by the parser and flowing
    through the entire pipeline. Every field is optional to handle
    incomplete profiles gracefully — the quality checker assigns
    a completeness score based on populated fields.

    Attributes:
        candidate_id: Unique identifier (from raw data source).
        name: Full name.
        email: Email address.
        phone: Phone number.
        location: Current location (city, state, country).
        current_title: Current or most recent job title.
        current_company: Current or most recent employer.
        years_of_experience: Total professional experience in years.
        skills: Flat list of all skills (deduplicated, normalised).
        education: Structured list of education records.
        work_experience: Structured list of employment records (newest first).
        certifications: Professional certifications.
        languages: Spoken/written languages.
        summary: Professional summary or objective.
        redrob_signals: Behavioral signals from the platform.
        raw_text: Full profile text used for embedding generation.
        raw_data: Original row as a dict (for debugging/audit).
        created_at: Timestamp when this profile was parsed.
    """
    candidate_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    embedding_id: Optional[int] = None
    location: Optional[str] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    years_of_experience: float = Field(default=0.0, ge=0.0)
    skills: List[str] = Field(default_factory=list)
    education: List[EducationEntry] = Field(default_factory=list)
    work_experience: List[WorkExperience] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    redrob_signals: RedrobSignals = Field(default_factory=RedrobSignals)
    raw_text: Optional[str] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("years_of_experience")
    @classmethod
    def clamp_experience(cls, v: float) -> float:
        """Clamp experience to [0, 50] — reject bad data."""
        return max(0.0, min(v, 50.0))

    @field_validator("skills")
    @classmethod
    def deduplicate_skills(cls, v: List[str]) -> List[str]:
        """Remove duplicate skills (case-insensitive)."""
        seen: set[str] = set()
        result: List[str] = []
        for skill in v:
            normalised = skill.strip().lower()
            if normalised and normalised not in seen:
                seen.add(normalised)
                result.append(skill.strip())
        return result[:100]  # cap at 100 skills

    @property
    def highest_education(self) -> Optional[EducationEntry]:
        """Return the highest education entry by level."""
        level_order = {
            EducationLevel.PHD: 6,
            EducationLevel.MASTERS: 5,
            EducationLevel.MBA: 4,
            EducationLevel.BACHELORS: 3,
            EducationLevel.DIPLOMA: 2,
            EducationLevel.HIGH_SCHOOL: 1,
            EducationLevel.OTHER: 0,
            EducationLevel.UNKNOWN: 0,
        }
        if not self.education:
            return None
        return max(self.education, key=lambda e: level_order.get(e.level, 0))

    @property
    def current_work(self) -> Optional[WorkExperience]:
        """Return the current/most recent work experience entry."""
        current = [w for w in self.work_experience if w.is_current]
        if current:
            return current[0]
        return self.work_experience[0] if self.work_experience else None


class CandidateFeatures(BaseModel):
    """
    Engineered feature vector for a candidate.

    These features are precomputed during the preprocessing phase
    and stored in DuckDB for fast retrieval during Stage 2 ranking.

    Each feature is normalised to [0.0, 1.0] unless noted.
    Risk features are also [0.0, 1.0] where higher = higher risk.

    Attributes:
        candidate_id: Reference to the source candidate.
        experience_score: Log-normalised relevant experience score.
        career_stability: Mean/std ratio of tenure lengths.
        promotion_score: Normalised title progression rate.
        skill_coverage: Computed at ranking time against specific JD.
        domain_match: Embedding cosine similarity vs JD (ranking time).
        leadership_score: Weighted leadership signals score.
        learning_score: Composite learning agility score.
        research_score: Research and innovation contribution score.
        behavior_score: Redrob signal composite score.
        hiring_availability: Inverse notice-period availability score.
        profile_completeness: Fraction of profile fields populated.
        career_velocity: Advancement speed relative to career age.
        skill_consistency: Skill coherence across career stages.
        job_hop_risk: Risk from frequent company changes.
        gap_risk: Risk from significant employment gaps.
        total_companies: Raw count of employers.
        avg_tenure_months: Mean tenure across all positions.
        max_tenure_months: Longest single tenure.
        career_gap_months: Largest single employment gap.
        skill_count: Total normalised skill count.
        certification_count: Total certifications.
        education_level_score: Numeric education level [0, 1].
        computed_at: Timestamp of feature computation.
    """
    candidate_id: str

    # ── Core Precomputed Features ─────────────────────────────────────────────
    experience_score: float = Field(default=0.0, ge=0.0, le=1.0)
    career_stability: float = Field(default=0.0, ge=0.0, le=1.0)
    promotion_score: float = Field(default=0.0, ge=0.0, le=1.0)
    leadership_score: float = Field(default=0.0, ge=0.0, le=1.0)
    learning_score: float = Field(default=0.0, ge=0.0, le=1.0)
    research_score: float = Field(default=0.0, ge=0.0, le=1.0)
    behavior_score: float = Field(default=0.0, ge=0.0, le=1.0)
    hiring_availability: float = Field(default=0.0, ge=0.0, le=1.0)
    profile_completeness: float = Field(default=0.0, ge=0.0, le=1.0)
    career_velocity: float = Field(default=0.0, ge=0.0, le=1.0)
    skill_consistency: float = Field(default=0.0, ge=0.0, le=1.0)

    # ── JD-Dependent Features (computed at ranking time) ──────────────────────
    skill_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    domain_match: float = Field(default=0.0, ge=0.0, le=1.0)

    # ── Risk Features (higher = more risky) ──────────────────────────────────
    job_hop_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    gap_risk: float = Field(default=0.0, ge=0.0, le=1.0)

    # ── Raw Metadata (for explainability) ─────────────────────────────────────
    total_companies: int = Field(default=0, ge=0)
    avg_tenure_months: float = Field(default=0.0, ge=0.0)
    max_tenure_months: float = Field(default=0.0, ge=0.0)
    career_gap_months: float = Field(default=0.0, ge=0.0)
    skill_count: int = Field(default=0, ge=0)
    certification_count: int = Field(default=0, ge=0)
    education_level_score: float = Field(default=0.0, ge=0.0, le=1.0)

    @property
    def stability_score(self) -> float:
        return self.career_stability

    @property
    def availability_score(self) -> float:
        return self.hiring_availability

    @property
    def education_score(self) -> float:
        return self.education_level_score

    @property
    def certifications_score(self) -> float:
        return float(max(0.0, min(1.0, self.certification_count / 5.0)))

    @property
    def semantic_similarity(self) -> float:
        return self.domain_match

    @property
    def location_match(self) -> float:
        return 0.5

    computed_at: datetime = Field(default_factory=datetime.utcnow)


class CandidateEvidence(BaseModel):
    """
    Evidence Ledger for a candidate.

    Every feature score must be backed by concrete, traceable evidence
    extracted directly from the candidate profile. This ensures
    explainability and prevents hallucination.

    Attributes:
        candidate_id: Reference to the source candidate.
        skill_evidence: Map of skill → list of evidence strings.
        experience_evidence: Evidence strings for experience score.
        leadership_evidence: Evidence strings for leadership score.
        learning_evidence: Evidence strings for learning score.
        stability_evidence: Evidence strings for stability score.
        risk_evidence: Evidence strings for identified risks.
        behavior_evidence: Evidence strings from Redrob signals.
        evidence_strength: Overall evidence quality score [0, 1].
    """
    candidate_id: str
    skill_evidence: Dict[str, List[str]] = Field(default_factory=dict)
    experience_evidence: List[str] = Field(default_factory=list)
    leadership_evidence: List[str] = Field(default_factory=list)
    learning_evidence: List[str] = Field(default_factory=list)
    stability_evidence: List[str] = Field(default_factory=list)
    risk_evidence: List[str] = Field(default_factory=list)
    behavior_evidence: List[str] = Field(default_factory=list)
    evidence_strength: float = Field(default=0.0, ge=0.0, le=1.0)

    @property
    def evidence(self) -> Dict[str, Any]:
        """Aggregate all evidence categories into a single dictionary."""
        return {
            "skill_evidence": self.skill_evidence,
            "experience_evidence": self.experience_evidence,
            "leadership_evidence": self.leadership_evidence,
            "learning_evidence": self.learning_evidence,
            "stability_evidence": self.stability_evidence,
            "risk_evidence": self.risk_evidence,
            "behavior_evidence": self.behavior_evidence,
            "evidence_strength": self.evidence_strength,
        }

    @property
    def timeline(self) -> List[Any]:
        """Return timeline events (mock or empty list if not explicitly stored)."""
        return []


class CandidateGenome(BaseModel):
    """
    Multidimensional capability profile — the candidate's professional 'DNA'.

    Combines features, evidence, and career analysis into a unified
    representation. This is what the Hiring Council receives.

    The genome_dimensions represent 8 high-level axes shown
    in the radar chart visualisation on the Candidate Detail page.

    Attributes:
        candidate_id: Unique candidate identifier.
        features: Precomputed feature vector.
        evidence: Traceable evidence for all features.
        profile: Full candidate profile.
        technical_capability: Technical skills + domain expertise composite.
        career_progression: Career growth and advancement composite.
        domain_expertise: Specialisation depth in the target domain.
        leadership_impact: Leadership and team influence composite.
        learning_agility: Learning speed and breadth composite.
        work_stability: Tenure consistency and reliability composite.
        behavioral_signals: Platform engagement and readiness composite.
        hiring_readiness: Combined availability and fit composite.
        embedding_id: FAISS vector ID for semantic retrieval.
        computed_at: Timestamp of genome construction.
    """
    candidate_id: str
    features: CandidateFeatures
    evidence: CandidateEvidence
    profile: CandidateProfile

    # ── Genome Dimensions [0, 1] — used in radar chart ────────────────────────
    technical_capability: float = Field(default=0.0, ge=0.0, le=1.0)
    career_progression: float = Field(default=0.0, ge=0.0, le=1.0)
    domain_expertise: float = Field(default=0.0, ge=0.0, le=1.0)
    leadership_impact: float = Field(default=0.0, ge=0.0, le=1.0)
    learning_agility: float = Field(default=0.0, ge=0.0, le=1.0)
    work_stability: float = Field(default=0.0, ge=0.0, le=1.0)
    behavioral_signals: float = Field(default=0.0, ge=0.0, le=1.0)
    hiring_readiness: float = Field(default=0.0, ge=0.0, le=1.0)

    embedding_id: Optional[int] = None  # FAISS internal index
    computed_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def genome_vector(self) -> List[float]:
        """Return genome dimensions as a list for radar chart data."""
        return [
            self.technical_capability,
            self.career_progression,
            self.domain_expertise,
            self.leadership_impact,
            self.learning_agility,
            self.work_stability,
            self.behavioral_signals,
            self.hiring_readiness,
        ]
