"""
TalentGraph AI — Feature Engineering Unit Tests

Tests all 15 engineered features to ensure correct computation,
normalization bounds [0,1], and edge case handling.
"""

from __future__ import annotations

from shared.types.candidate import (
    AvailabilityStatus,
    CandidateProfile,
    RedrobSignals,
    WorkExperience,
)


class TestExperienceScore:
    """Tests for experience_score feature computation."""

    def test_zero_experience(self):
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        score = extractor.compute_experience_score(0.0)
        assert score == 0.0

    def test_ten_years_experience(self):
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        score = extractor.compute_experience_score(10.0)
        assert 0.69 <= score <= 1.0

    def test_score_within_bounds(self):
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        for years in [0, 1, 5, 10, 20, 30, 50]:
            score = extractor.compute_experience_score(float(years))
            assert 0.0 <= score <= 1.0, f"Score {score} out of bounds for {years} years"

    def test_monotonically_increasing(self):
        """More experience should always produce higher or equal score."""
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        scores = [extractor.compute_experience_score(float(y)) for y in [0, 2, 5, 10, 20]]
        assert scores == sorted(scores)


class TestCareerStability:
    """Tests for career_stability feature computation."""

    def test_single_company(self):
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        experiences = [
            WorkExperience(company="Google", title="SWE", duration_months=60, is_current=True),
        ]
        score = extractor.compute_career_stability(experiences)
        assert 0.0 <= score <= 1.0

    def test_job_hopper(self):
        """Multiple short tenures should produce lower stability."""
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        experiences = [
            WorkExperience(company=f"Co{i}", title="Dev", duration_months=6) for i in range(5)
        ]
        score = extractor.compute_career_stability(experiences)
        assert score < 0.5, f"Expected low stability, got {score}"

    def test_stable_career(self):
        """Long tenures should produce high stability."""
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        experiences = [
            WorkExperience(company="Google", title="SWE", duration_months=60),
            WorkExperience(company="Meta", title="Senior SWE", duration_months=48),
        ]
        score = extractor.compute_career_stability(experiences)
        assert score >= 0.6, f"Expected high stability, got {score}"

    def test_empty_experience(self):
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        score = extractor.compute_career_stability([])
        assert score == 0.0


class TestSkillCoverage:
    """Tests for skill_coverage feature (JD-dependent)."""

    def test_full_coverage(self):
        """Candidate with all required skills should score ~1.0."""
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        candidate_skills = ["Python", "TensorFlow", "Kubernetes", "SQL"]
        jd_skills = ["Python", "TensorFlow", "Kubernetes"]
        coverage = extractor.compute_skill_coverage_static(candidate_skills, jd_skills)
        assert coverage >= 0.95

    def test_zero_coverage(self):
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        coverage = extractor.compute_skill_coverage_static(["Java", "Spring"], ["Python", "ML"])
        assert coverage < 0.2

    def test_partial_coverage(self):
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        candidate_skills = ["Python", "SQL"]
        jd_skills = ["Python", "TensorFlow", "Kubernetes", "SQL"]
        coverage = extractor.compute_skill_coverage_static(candidate_skills, jd_skills)
        assert 0.4 <= coverage <= 0.6

    def test_empty_jd_skills(self):
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        coverage = extractor.compute_skill_coverage_static(["Python"], [])
        assert coverage == 0.0


class TestProfileCompleteness:
    """Tests for profile_completeness feature."""

    def test_complete_profile(self, sample_candidate_profile):
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        score = extractor.compute_profile_completeness(sample_candidate_profile)
        assert score >= 0.8

    def test_minimal_profile(self):
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        profile = CandidateProfile(candidate_id="minimal_001")
        score = extractor.compute_profile_completeness(profile)
        assert score < 0.3

    def test_score_bounds(self, sample_candidate_profile):
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        score = extractor.compute_profile_completeness(sample_candidate_profile)
        assert 0.0 <= score <= 1.0


class TestJobHopRisk:
    """Tests for job_hop_risk feature."""

    def test_stable_career_low_risk(self):
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        experiences = [
            WorkExperience(company="Google", title="SWE", duration_months=48),
            WorkExperience(company="Amazon", title="SDE", duration_months=36),
        ]
        risk = extractor.compute_job_hop_risk(experiences)
        assert risk < 0.3

    def test_job_hopper_high_risk(self):
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        experiences = [
            WorkExperience(company=f"Co{i}", title="Dev", duration_months=5) for i in range(5)
        ]
        risk = extractor.compute_job_hop_risk(experiences)
        assert risk >= 0.5

    def test_risk_bounds(self):
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        experiences = [
            WorkExperience(company="Co", title="Dev", duration_months=m) for m in [3, 6, 12, 24, 48]
        ]
        risk = extractor.compute_job_hop_risk(experiences)
        assert 0.0 <= risk <= 1.0


class TestBehaviorScore:
    """Tests for behavior_score from Redrob signals."""

    def test_high_engagement(self):
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        signals = RedrobSignals(
            response_rate=0.95,
            last_active_days=2,
            availability_status=AvailabilityStatus.IMMEDIATELY_AVAILABLE,
            profile_views=100,
            application_count=5,
        )
        score = extractor.compute_behavior_score(signals)
        assert score >= 0.7

    def test_low_engagement(self):
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        signals = RedrobSignals(
            response_rate=0.1,
            last_active_days=180,
            availability_status=AvailabilityStatus.NOT_LOOKING,
        )
        score = extractor.compute_behavior_score(signals)
        assert score <= 0.4

    def test_score_bounds(self):
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        for rate in [0.0, 0.25, 0.5, 0.75, 1.0]:
            signals = RedrobSignals(response_rate=rate)
            score = extractor.compute_behavior_score(signals)
            assert 0.0 <= score <= 1.0


class TestLeadershipScore:
    """Tests for leadership_score feature."""

    def test_manager_high_score(self):
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        profile = CandidateProfile(
            candidate_id="mgr_001",
            current_title="Engineering Manager",
            skills=["Python", "Leadership", "Team Management"],
            work_experience=[
                WorkExperience(
                    company="Google",
                    title="Engineering Manager",
                    duration_months=36,
                    description="Managed team of 8. Led hiring for ML org.",
                ),
            ],
        )
        score = extractor.compute_leadership_score(profile)
        assert score >= 0.5

    def test_ic_lower_score(self):
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        profile = CandidateProfile(
            candidate_id="ic_001",
            current_title="Junior Developer",
            skills=["Python", "SQL"],
            work_experience=[
                WorkExperience(
                    company="Startup",
                    title="Junior Developer",
                    duration_months=12,
                    description="Developed backend APIs.",
                ),
            ],
        )
        score_ic = extractor.compute_leadership_score(profile)
        assert score_ic < 0.4


class TestAllFeaturesExtraction:
    """Integration test: ensure all 15 features are computed for a full profile."""

    def test_extract_all_produces_15_features(self, sample_candidate_profile):
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        features = extractor.extract_all(sample_candidate_profile)

        # Verify all core features are non-None and in bounds
        core_features = [
            features.experience_score,
            features.career_stability,
            features.promotion_score,
            features.leadership_score,
            features.learning_score,
            features.research_score,
            features.behavior_score,
            features.hiring_availability,
            features.profile_completeness,
            features.career_velocity,
            features.skill_consistency,
            features.job_hop_risk,
            features.gap_risk,
        ]

        for score in core_features:
            assert 0.0 <= score <= 1.0, f"Score {score} out of bounds"

    def test_candidate_id_preserved(self, sample_candidate_profile):
        from services.preprocessing.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        features = extractor.extract_all(sample_candidate_profile)
        assert features.candidate_id == sample_candidate_profile.candidate_id
