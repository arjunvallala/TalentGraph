"""
TalentGraph AI — Test Fixtures and Configuration

Provides shared fixtures for all test suites including:
- Sample candidate profiles
- Sample job descriptions
- Mock feature store
- Test settings
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Generator
from pathlib import Path

import pytest

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment
os.environ["APP_ENV"] = "test"
os.environ["DEMO_MODE"] = "true"
os.environ["DUCKDB_PATH"] = ":memory:"

# Mock sentence_transformers package globally
import sys
from unittest.mock import MagicMock
import numpy as np

class MockSentenceTransformer:
    def __init__(self, model_name_or_path, *args, **kwargs):
        self.model_name_or_path = model_name_or_path
    def encode(self, sentences, *args, **kwargs):
        count = len(sentences) if isinstance(sentences, list) else 1
        # generate repeatable mock embeddings
        np.random.seed(42)
        emb = np.random.randn(count, 384)
        norms = np.linalg.norm(emb, axis=1, keepdims=True)
        emb = emb / (norms + 1e-8)
        return emb.astype(np.float32) if isinstance(sentences, list) else emb[0].astype(np.float32)
    def save(self, *args, **kwargs):
        pass

mock_st_module = MagicMock()
mock_st_module.SentenceTransformer = MockSentenceTransformer
sys.modules["sentence_transformers"] = mock_st_module

from shared.config import get_settings
from shared.types.candidate import (
    CandidateProfile, CandidateFeatures, CandidateEvidence,
    WorkExperience, EducationEntry, RedrobSignals,
    AvailabilityStatus, EducationLevel,
)
from shared.types.job import JobRaw, JobProfile, ExperienceLevel, SkillRequirement


# ── Test Settings ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_settings():
    """Return test-specific settings."""
    get_settings.cache_clear()
    s = get_settings()
    return s


# ── Sample Candidate Profiles ─────────────────────────────────────────────────

@pytest.fixture
def sample_work_experience():
    """Return a list of sample work experience entries."""
    return [
        WorkExperience(
            company="Google",
            title="Senior Software Engineer",
            start_date="2020-01",
            end_date="Present",
            is_current=True,
            duration_months=48,
            description="Led ML platform development. Managed team of 5.",
            skills_used=["Python", "TensorFlow", "Kubernetes", "GCP"],
        ),
        WorkExperience(
            company="Flipkart",
            title="Software Engineer",
            start_date="2018-06",
            end_date="2019-12",
            is_current=False,
            duration_months=18,
            description="Backend development for recommendations engine.",
            skills_used=["Python", "Spark", "Kafka"],
        ),
        WorkExperience(
            company="Infosys",
            title="Junior Developer",
            start_date="2016-07",
            end_date="2018-05",
            is_current=False,
            duration_months=22,
            description="Java backend development.",
            skills_used=["Java", "Spring", "MySQL"],
        ),
    ]


@pytest.fixture
def sample_education():
    """Return sample education entries."""
    return [
        EducationEntry(
            institution="IIT Delhi",
            degree="B.Tech in Computer Science",
            field_of_study="Computer Science",
            level=EducationLevel.BACHELORS,
            start_year=2012,
            end_year=2016,
        ),
    ]


@pytest.fixture
def sample_redrob_signals():
    """Return sample Redrob platform signals."""
    return RedrobSignals(
        profile_views=450,
        application_count=12,
        response_rate=0.85,
        last_active_days=3,
        availability_status=AvailabilityStatus.OPEN_TO_OPPORTUNITIES,
        notice_period_days=30,
        expected_salary=2500000.0,
        open_to_remote=True,
    )


@pytest.fixture
def sample_candidate_profile(sample_work_experience, sample_education, sample_redrob_signals):
    """Return a complete sample candidate profile."""
    return CandidateProfile(
        candidate_id="test_c001",
        name="Arjun Sharma",
        email="arjun.sharma@email.com",
        location="Bangalore, India",
        current_title="Senior Software Engineer",
        current_company="Google",
        years_of_experience=8.0,
        skills=["Python", "TensorFlow", "PyTorch", "Kubernetes", "GCP", "SQL",
                "Machine Learning", "Deep Learning", "Spark", "Kafka"],
        education=sample_education,
        work_experience=sample_work_experience,
        certifications=["Google Cloud Professional ML Engineer", "AWS Solutions Architect"],
        languages=["English", "Hindi"],
        summary=(
            "Senior ML Engineer with 8 years of experience building scalable "
            "ML platforms and recommendation systems at Google and Flipkart."
        ),
        redrob_signals=sample_redrob_signals,
        raw_text="Senior ML Engineer Python TensorFlow Google Flipkart IIT Delhi",
    )


@pytest.fixture
def sample_candidate_features():
    """Return sample pre-computed features."""
    return CandidateFeatures(
        candidate_id="test_c001",
        experience_score=0.78,
        career_stability=0.82,
        promotion_score=0.65,
        leadership_score=0.70,
        learning_score=0.75,
        research_score=0.30,
        behavior_score=0.88,
        hiring_availability=0.85,
        profile_completeness=0.95,
        career_velocity=0.72,
        skill_consistency=0.80,
        skill_coverage=0.0,     # computed at ranking time
        domain_match=0.0,       # computed at ranking time
        job_hop_risk=0.15,
        gap_risk=0.05,
        total_companies=3,
        avg_tenure_months=29.3,
        max_tenure_months=48.0,
        career_gap_months=1.0,
        skill_count=10,
        certification_count=2,
        education_level_score=0.70,
    )


# ── Sample Job Description ─────────────────────────────────────────────────────

@pytest.fixture
def sample_job_raw():
    """Return a sample job description."""
    return JobRaw(
        job_id="test_job_001",
        title="Senior Machine Learning Engineer",
        description=(
            "We are looking for a Senior ML Engineer with 5+ years of experience. "
            "Required skills: Python, TensorFlow or PyTorch, distributed training, "
            "MLOps, Kubernetes, cloud platforms (GCP/AWS). "
            "Experience with recommendation systems is a plus. "
            "You will lead a team of 3-5 ML engineers. "
            "BS/MS/PhD in Computer Science or related field required."
        ),
        company="TechCorp India",
        location="Bangalore, India",
    )


@pytest.fixture
def sample_job_profile():
    """Return a sample structured job profile."""
    return JobProfile(
        job_id="test_job_001",
        title="Senior Machine Learning Engineer",
        seniority_level=ExperienceLevel.SENIOR,
        required_skills=[
            SkillRequirement(skill="Python", importance=1.0, is_mandatory=True),
            SkillRequirement(skill="TensorFlow", importance=0.9, is_mandatory=True),
            SkillRequirement(skill="PyTorch", importance=0.9, is_mandatory=False),
            SkillRequirement(skill="Kubernetes", importance=0.8, is_mandatory=True),
        ],
        preferred_skills=["MLOps", "Recommendation Systems", "GCP"],
        min_experience_years=5.0,
        primary_domain="machine learning",
        education_required="bachelors",
        key_responsibilities=[
            "Lead ML model development",
            "Build and maintain ML pipelines",
            "Mentor junior engineers",
        ],
        leadership_required=True,
    )


# ── HTTP Client ───────────────────────────────────────────────────────────────

@pytest.fixture
def api_client(test_settings):
    """Return an async HTTP test client for the FastAPI app."""
    from httpx import AsyncClient, ASGITransport
    from apps.api.main import app
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
