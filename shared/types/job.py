"""
TalentGraph AI — Job & Ideal Candidate Persona Data Models

Defines all models related to job descriptions, structured job profiles,
the Ideal Candidate Persona, and the Job Genome.

Pipeline flow:
    Raw JD Text → JobRaw → JobProfile → IdealCandidatePersona + JobGenome
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ── Enums ─────────────────────────────────────────────────────────────────────

class ExperienceLevel(str, Enum):
    """
    Standardised seniority levels for job roles.

    Maps to approximate year ranges:
        entry: 0–2 years
        junior: 2–4 years
        mid: 4–7 years
        senior: 7–12 years
        principal: 12–20 years
        executive: 20+ years
    """
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    PRINCIPAL = "principal"
    EXECUTIVE = "executive"


class JobType(str, Enum):
    """Employment type for the role."""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"


# ── Sub-Models ────────────────────────────────────────────────────────────────

class SkillRequirement(BaseModel):
    """
    A single skill requirement extracted from the job description.

    Attributes:
        skill: Normalised skill name.
        importance: Relative importance [0, 1]. 1.0 = mandatory.
        min_years: Minimum years of experience required.
        is_mandatory: True if the skill is explicitly required (not preferred).
        category: Skill category (e.g., 'programming', 'domain', 'soft').
    """
    skill: str
    importance: float = Field(default=1.0, ge=0.0, le=1.0)
    min_years: Optional[float] = Field(default=None, ge=0.0)
    is_mandatory: bool = True
    category: Optional[str] = None


# ── Core Models ───────────────────────────────────────────────────────────────

class JobRaw(BaseModel):
    """
    Raw job description as received from the user.

    This is the entry point for the Job Intelligence pipeline.

    Attributes:
        job_id: Unique identifier for this job posting.
        title: Job title as provided.
        description: Full job description text.
        company: Hiring company name.
        location: Job location.
        job_type: Employment type.
        raw_text: Full text used for embedding (title + description merged).
        created_at: When this JD was submitted.
    """
    job_id: str
    title: str
    description: str
    company: Optional[str] = None
    location: Optional[str] = None
    job_type: JobType = JobType.FULL_TIME
    raw_text: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def model_post_init(self, __context) -> None:
        """Auto-populate raw_text from title + description if not set."""
        if not self.raw_text:
            object.__setattr__(
                self, "raw_text", f"{self.title}\n\n{self.description}"
            )


class JobProfile(BaseModel):
    """
    Structured analysis of a job description.

    Produced by the Job Intelligence Engine from a JobRaw input.
    Contains extracted, normalised requirements ready for candidate matching.

    Attributes:
        job_id: Reference to source JobRaw.
        title: Normalised job title.
        seniority_level: Inferred experience level.
        required_skills: Mandatory skills with importance weights.
        preferred_skills: Nice-to-have skills.
        min_experience_years: Minimum required experience.
        max_experience_years: Maximum preferred experience (optional).
        primary_domain: Main domain (e.g., 'machine learning', 'backend').
        secondary_domains: Adjacent domains.
        industry: Target industry sector.
        education_required: Minimum education qualification.
        education_preferred: Preferred education qualification.
        key_responsibilities: Main responsibilities extracted from JD.
        leadership_required: Whether people management is expected.
        remote_friendly: Whether remote/hybrid is supported.
        travel_required: Whether significant travel is required.
        analyzed_at: Timestamp of analysis.
    """
    job_id: str
    title: str
    seniority_level: ExperienceLevel = ExperienceLevel.MID
    required_skills: List[SkillRequirement] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    min_experience_years: float = Field(default=0.0, ge=0.0)
    max_experience_years: Optional[float] = Field(default=None, ge=0.0)
    primary_domain: Optional[str] = None
    secondary_domains: List[str] = Field(default_factory=list)
    industry: Optional[str] = None
    education_required: Optional[str] = None
    education_preferred: Optional[str] = None
    key_responsibilities: List[str] = Field(default_factory=list)
    leadership_required: bool = False
    remote_friendly: bool = False
    travel_required: bool = False
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def all_required_skill_names(self) -> List[str]:
        """Return flat list of mandatory skill names."""
        return [s.skill for s in self.required_skills if s.is_mandatory]

    @property
    def all_skill_names(self) -> List[str]:
        """Return all skill names (required + preferred)."""
        required = [s.skill for s in self.required_skills]
        return required + self.preferred_skills


class IdealCandidatePersona(BaseModel):
    """
    The Ideal Candidate Profile derived from Job Intelligence.

    This is the conceptual 'perfect candidate' that the hiring committee
    would unanimously approve. It serves as the reference point for all
    candidate evaluations.

    Attributes:
        job_id: Reference to the source job.
        must_have_skills: Non-negotiable required skills.
        nice_to_have_skills: Beneficial but not required skills.
        min_experience_years: Minimum experience required.
        ideal_experience_years: Experience sweet spot.
        preferred_career_progression: Expected career path pattern.
        preferred_company_types: Types of companies valued (startup, MNC, etc.).
        expected_seniority: Expected career level of ideal candidate.
        domain_weight: Importance of domain expertise [0, 1].
        technical_weight: Importance of technical skills [0, 1].
        leadership_weight: Importance of leadership [0, 1].
        implicit_expectations: Inferred expectations not stated in JD.
        red_flags: Profile signals that would concern the hiring committee.
        feature_weights: Custom feature weights for this role's ranking.
        created_at: When this persona was generated.
    """
    job_id: str
    must_have_skills: List[str] = Field(default_factory=list)
    nice_to_have_skills: List[str] = Field(default_factory=list)
    min_experience_years: float = Field(default=0.0, ge=0.0)
    ideal_experience_years: float = Field(default=3.0, ge=0.0)
    preferred_career_progression: List[str] = Field(default_factory=list)
    preferred_company_types: List[str] = Field(default_factory=list)
    expected_seniority: ExperienceLevel = ExperienceLevel.MID
    domain_weight: float = Field(default=0.8, ge=0.0, le=1.0)
    technical_weight: float = Field(default=0.7, ge=0.0, le=1.0)
    leadership_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    implicit_expectations: List[str] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)
    feature_weights: Dict[str, float] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JobGenome(BaseModel):
    """
    The weighted feature target vector representing the ideal candidate.

    This is the 'genetic fingerprint' of the role, used during Stage 2
    feature ranking to score candidates against the job's requirements.

    Attributes:
        job_id: Reference to the source job.
        target_*: Target feature scores the ideal candidate should have.
        weights: Feature importance weights for this specific role.
        embedding: Dense vector representation of the job description.
        key_terms: BM25 index terms extracted from the JD.
        created_at: When this genome was generated.
    """
    job_id: str

    # ── Target Feature Scores [0, 1] ──────────────────────────────────────────
    target_experience_score: float = Field(default=0.8, ge=0.0, le=1.0)
    target_career_stability: float = Field(default=0.7, ge=0.0, le=1.0)
    target_skill_coverage: float = Field(default=0.9, ge=0.0, le=1.0)
    target_domain_match: float = Field(default=0.85, ge=0.0, le=1.0)
    target_leadership_score: float = Field(default=0.5, ge=0.0, le=1.0)
    target_learning_score: float = Field(default=0.7, ge=0.0, le=1.0)
    target_behavior_score: float = Field(default=0.7, ge=0.0, le=1.0)

    # ── Feature Weights for This Role ─────────────────────────────────────────
    weights: Dict[str, float] = Field(default_factory=dict)

    # ── Retrieval Artifacts ───────────────────────────────────────────────────
    embedding: Optional[List[float]] = None      # dense vector for FAISS
    key_terms: List[str] = Field(default_factory=list)  # BM25 terms

    created_at: datetime = Field(default_factory=datetime.utcnow)
