"""
TalentGraph AI — Feature Extractor

The core feature engineering module. Computes all 15 candidate features
from a structured CandidateProfile. Each feature is normalised to [0.0, 1.0].

Features are stored in CandidateFeatures and used by the ranking pipeline
for Stage 2 (Feature Ranking) scoring.

All computations are deterministic — no randomness, no LLMs.
"""
from __future__ import annotations

import math

from services.preprocessing.career_parser import CareerParser
from shared.constants import (
    CAREER_GAP_THRESHOLD_MONTHS,
    EPSILON,
    LEADERSHIP_MODERATE_KEYWORDS,
    LEADERSHIP_STRONG_KEYWORDS,
    MAX_EXPERIENCE_YEARS,
    MIN_TENURE_MONTHS_STABLE,
    RESEARCH_KEYWORDS,
)
from shared.logging_setup import get_logger
from shared.types.candidate import (
    CandidateFeatures,
    CandidateProfile,
    EducationLevel,
    RedrobSignals,
    WorkExperience,
)
from shared.utils.math_utils import clip, normalize_log, safe_divide

logger = get_logger(__name__)

# Education level → score mapping
_EDU_LEVEL_SCORES: dict[EducationLevel, float] = {
    EducationLevel.PHD: 1.0,
    EducationLevel.MASTERS: 0.85,
    EducationLevel.MBA: 0.80,
    EducationLevel.BACHELORS: 0.65,
    EducationLevel.DIPLOMA: 0.45,
    EducationLevel.HIGH_SCHOOL: 0.25,
    EducationLevel.OTHER: 0.30,
    EducationLevel.UNKNOWN: 0.35,
}

# Required fields for completeness scoring
_COMPLETENESS_FIELD_WEIGHTS: dict[str, float] = {
    "name": 0.05,
    "current_title": 0.12,
    "current_company": 0.08,
    "skills": 0.15,
    "work_experience": 0.20,
    "education": 0.10,
    "summary": 0.10,
    "email": 0.05,
    "location": 0.05,
    "certifications": 0.05,
    "years_of_experience": 0.05,
}


class FeatureExtractor:
    """
    Computes the 15-feature vector for each candidate profile.

    Features:
        1. experience_score — Log-normalised total years of experience
        2. career_stability — Consistency of tenure lengths (inverse of std/mean)
        3. promotion_score — Title progression rate across career
        4. leadership_score — Weighted leadership signals
        5. learning_score — Composite learning agility
        6. research_score — Research and innovation signals
        7. behavior_score — Redrob platform behavioral signals
        8. hiring_availability — Inverse notice period / availability
        9. profile_completeness — Fraction of profile populated
        10. career_velocity — Advancement speed relative to career age
        11. skill_consistency — Skill coherence across career stages
        12. job_hop_risk — Risk from frequent company switches
        13. gap_risk — Risk from employment gaps
        14. skill_coverage — JD-specific (set to 0.0, computed at ranking time)
        15. domain_match — JD-specific (set to 0.0, computed at ranking time)

    Example:
        extractor = FeatureExtractor()
        features = extractor.extract_all(profile)
    """

    def __init__(self) -> None:
        """Initialise the feature extractor."""
        self._career_parser = CareerParser()
        logger.debug("FeatureExtractor initialised")

    def extract_all(self, profile: CandidateProfile) -> CandidateFeatures:
        """
        Compute all features for a candidate profile.

        Args:
            profile: Structured CandidateProfile instance.

        Returns:
            CandidateFeatures with all 15 features computed.
        """
        try:
            experiences = profile.work_experience
            signals = profile.redrob_signals
            years = profile.years_of_experience

            # Career metadata
            total_companies = len({e.company.strip().lower() for e in experiences if e.company.strip()})
            avg_tenure = self._career_parser.compute_avg_tenure(experiences)
            max_tenure = max(
                (e.duration_months for e in experiences if e.duration_months),
                default=0
            )
            career_gap_months_list = self._career_parser.find_career_gaps(experiences)
            max_gap = career_gap_months_list[0][2] if career_gap_months_list else 0

            # Core feature computation
            experience_score = self.compute_experience_score(years)
            career_stability = self.compute_career_stability(experiences)
            promotion_score = self.compute_promotion_score(experiences, years)
            leadership_score = self.compute_leadership_score(profile)
            learning_score = self.compute_learning_score(profile)
            research_score = self.compute_research_score(profile)
            behavior_score = self.compute_behavior_score(signals)
            hiring_availability = self.compute_hiring_availability(signals)
            profile_completeness = self.compute_profile_completeness(profile)
            career_velocity = self.compute_career_velocity(experiences, years)
            skill_consistency = self.compute_skill_consistency(experiences)
            job_hop_risk = self.compute_job_hop_risk(experiences)
            gap_risk = self.compute_gap_risk(experiences)
            education_level_score = self.compute_education_level_score(profile.education)

            return CandidateFeatures(
                candidate_id=profile.candidate_id,
                experience_score=experience_score,
                career_stability=career_stability,
                promotion_score=promotion_score,
                leadership_score=leadership_score,
                learning_score=learning_score,
                research_score=research_score,
                behavior_score=behavior_score,
                hiring_availability=hiring_availability,
                profile_completeness=profile_completeness,
                career_velocity=career_velocity,
                skill_consistency=skill_consistency,
                job_hop_risk=job_hop_risk,
                gap_risk=gap_risk,
                # JD-dependent features — computed at ranking time
                skill_coverage=0.0,
                domain_match=0.0,
                # Raw metadata
                total_companies=total_companies,
                avg_tenure_months=float(avg_tenure),
                max_tenure_months=float(max_tenure),
                career_gap_months=float(max_gap),
                skill_count=len(profile.skills),
                certification_count=len(profile.certifications),
                education_level_score=education_level_score,
            )

        except Exception as exc:
            logger.error(
                "Feature extraction failed for %s: %s",
                profile.candidate_id, exc, exc_info=True
            )
            # Return zero-features rather than crash the pipeline
            return CandidateFeatures(candidate_id=profile.candidate_id)

    def compute_experience_score(self, years: float) -> float:
        """
        Compute log-normalised experience score.

        Uses log(1+x)/log(1+max) to give diminishing returns for very
        senior candidates (30yr vs 25yr matters less than 5yr vs 0yr).

        Args:
            years: Total years of professional experience.

        Returns:
            Score in [0.0, 1.0].
        """
        return normalize_log(years, max_val=MAX_EXPERIENCE_YEARS)

    @staticmethod
    def compute_skill_coverage_static(candidate_skills: list[str], jd_skills: list[str]) -> float:
        """
        Compute static skill coverage score.

        Args:
            candidate_skills: List of candidate skills.
            jd_skills: List of skills required by the job.

        Returns:
            Score in [0.0, 1.0].
        """
        if not jd_skills:
            return 0.0
        candidate_set = {s.strip().lower() for s in candidate_skills if s.strip()}
        jd_set = {s.strip().lower() for s in jd_skills if s.strip()}
        if not jd_set:
            return 0.0
        overlap = len(candidate_set.intersection(jd_set))
        return clip(float(overlap) / len(jd_set))

    def compute_career_stability(self, experiences: list[WorkExperience]) -> float:
        """
        Compute career stability as the inverse coefficient of variation of tenures.

        A candidate who stays ~equal time at each company scores high.
        High variance in tenure lengths scores low.

        Args:
            experiences: List of work experiences.

        Returns:
            Stability score in [0.0, 1.0].
        """
        tenures = [
            e.duration_months for e in experiences
            if e.duration_months is not None and e.duration_months > 0
        ]

        if not tenures:
            return 0.0

        if len(tenures) == 1:
            # Reward longer single tenure
            return clip(tenures[0] / 48.0)  # 4 years = 1.0

        mean_tenure = sum(tenures) / len(tenures)
        variance = sum((t - mean_tenure) ** 2 for t in tenures) / len(tenures)
        std_tenure = math.sqrt(variance)

        # Coefficient of variation: lower = more stable
        cv = safe_divide(std_tenure, mean_tenure, default=1.0)

        # Convert CV to score: cv=0 → 1.0, cv=2 → 0.0
        stability = 1.0 - clip(cv / 2.0)

        # Penalise short average tenures: 2 years (24 months) or more gets no penalty,
        # below 24 months scales down stability.
        tenure_penalty = clip(mean_tenure / 24.0)
        return clip(stability * tenure_penalty)

    def compute_promotion_score(
        self, experiences: list[WorkExperience], years: float
    ) -> float:
        """
        Compute promotion score based on detected title progression.

        Score = promotions_detected / max_possible_promotions
        where max_possible = floor(years / 3) (one promotion per 3 years).

        Args:
            experiences: List of work experiences.
            years: Total years of experience.

        Returns:
            Promotion score in [0.0, 1.0].
        """
        if not experiences or years < 1:
            return 0.0

        promotions = self._career_parser.detect_promotions(experiences)
        max_possible = max(1, int(years / 3.0))
        score = safe_divide(float(promotions), float(max_possible), 0.0)
        return clip(score)

    def compute_leadership_score(self, profile: CandidateProfile) -> float:
        """
        Compute leadership score from title, description, and summary keywords.

        Uses LEADERSHIP_STRONG_KEYWORDS (full weight) and
        LEADERSHIP_MODERATE_KEYWORDS (half weight).

        Args:
            profile: Full CandidateProfile.

        Returns:
            Leadership score in [0.0, 1.0].
        """
        text_sources: list[str] = []
        if profile.current_title:
            text_sources.append(profile.current_title.lower())
        if profile.summary:
            text_sources.append(profile.summary.lower())
        for exp in profile.work_experience[:5]:
            if exp.title:
                text_sources.append(exp.title.lower())
            if exp.description:
                text_sources.append(exp.description.lower()[:500])

        combined = " ".join(text_sources)

        strong_hits = sum(
            1 for kw in LEADERSHIP_STRONG_KEYWORDS if kw.lower() in combined
        )
        moderate_hits = sum(
            1 for kw in LEADERSHIP_MODERATE_KEYWORDS if kw.lower() in combined
        )

        # Normalize: 5 strong hits or 10 moderate hits → 1.0
        score = clip(strong_hits / 5.0 + moderate_hits / 20.0)
        return clip(score)

    def compute_learning_score(self, profile: CandidateProfile) -> float:
        """
        Compute learning agility score from certifications, education diversity,
        and skill breadth.

        Formula:
        - 0.4 × cert_score (certifications / 5, capped at 1.0)
        - 0.3 × skill_breadth_score (skills / 30, capped at 1.0)
        - 0.3 × education_score (more than bachelors → bonus)

        Args:
            profile: Full CandidateProfile.

        Returns:
            Learning score in [0.0, 1.0].
        """
        cert_count = len(profile.certifications)
        skill_count = len(profile.skills)

        cert_score = clip(cert_count / 5.0)
        skill_breadth = clip(skill_count / 30.0)

        # Education learning bonus
        edu_bonus = 0.0
        highest = profile.highest_education
        if highest:
            if highest.level in (EducationLevel.MASTERS, EducationLevel.MBA):
                edu_bonus = 0.5
            elif highest.level == EducationLevel.PHD:
                edu_bonus = 1.0
            elif highest.level == EducationLevel.BACHELORS:
                edu_bonus = 0.3

        score = 0.4 * cert_score + 0.3 * skill_breadth + 0.3 * edu_bonus
        return clip(score)

    def compute_research_score(self, profile: CandidateProfile) -> float:
        """
        Compute research and innovation score from keyword signals.

        Scans summary and work experience descriptions for RESEARCH_KEYWORDS.

        Args:
            profile: Full CandidateProfile.

        Returns:
            Research score in [0.0, 1.0].
        """
        text_sources: list[str] = []
        if profile.summary:
            text_sources.append(profile.summary.lower())
        for exp in profile.work_experience[:5]:
            if exp.description:
                text_sources.append(exp.description.lower()[:500])
        for cert in profile.certifications[:10]:
            text_sources.append(cert.lower())

        combined = " ".join(text_sources)
        hits = sum(1 for kw in RESEARCH_KEYWORDS if kw.lower() in combined)

        # Normalize: 5 research hits → 1.0
        return clip(hits / 5.0)

    def compute_behavior_score(self, signals: RedrobSignals) -> float:
        """
        Compute behavioral signal composite score from Redrob platform data.

        Components:
        - 0.3 × response_rate (direct signal)
        - 0.2 × activity_score (inverse of last_active_days)
        - 0.2 × application_score (log-normalised application_count)
        - 0.2 × profile_view_score (log-normalised profile_views)
        - 0.1 × reliability_penalty (declined interviews/offers)

        Args:
            signals: RedrobSignals instance.

        Returns:
            Behavior score in [0.0, 1.0].
        """
        # Response rate (direct)
        response_score = clip(signals.response_rate)

        # Activity recency (lower days = more active = higher score)
        if signals.last_active_days is not None:
            days = signals.last_active_days
            if days <= 7:
                activity_score = 1.0
            elif days <= 30:
                activity_score = 0.8
            elif days <= 90:
                activity_score = 0.5
            elif days <= 180:
                activity_score = 0.3
            else:
                activity_score = 0.1
        else:
            activity_score = 0.3  # Unknown → neutral

        # Application count (log-normalized, 20 apps = ~1.0)
        app_score = normalize_log(float(signals.application_count), max_val=20.0)

        # Profile views (log-normalized, 500 views = ~1.0)
        view_score = normalize_log(float(signals.profile_views), max_val=500.0)

        # Reliability penalty for declining interviews/offers
        declined_total = signals.interview_declined_count + signals.offer_declined_count
        reliability = clip(1.0 - (declined_total * 0.15))  # -15% per decline

        score = (
            0.35 * response_score
            + 0.25 * activity_score
            + 0.15 * app_score
            + 0.15 * view_score
            + 0.10 * reliability
        )
        return clip(score)

    def compute_hiring_availability(self, signals: RedrobSignals) -> float:
        """
        Compute hiring availability from availability status and notice period.

        Args:
            signals: RedrobSignals instance.

        Returns:
            Availability score in [0.0, 1.0].
        """
        from shared.types.candidate import AvailabilityStatus

        # Base score from availability status
        status_scores = {
            AvailabilityStatus.IMMEDIATELY_AVAILABLE: 1.0,
            AvailabilityStatus.OPEN_TO_OPPORTUNITIES: 0.7,
            AvailabilityStatus.NOTICE_PERIOD: 0.5,
            AvailabilityStatus.NOT_LOOKING: 0.1,
            AvailabilityStatus.UNKNOWN: 0.4,
        }
        base_score = status_scores.get(signals.availability_status, 0.4)

        # Adjust for notice period length
        if signals.notice_period_days is not None:
            days = signals.notice_period_days
            if days <= 0:
                notice_score = 1.0
            elif days <= 15:
                notice_score = 0.9
            elif days <= 30:
                notice_score = 0.7
            elif days <= 60:
                notice_score = 0.5
            elif days <= 90:
                notice_score = 0.35
            else:
                notice_score = 0.2
            # Blend: 70% status, 30% notice period
            return clip(0.7 * base_score + 0.3 * notice_score)

        return clip(base_score)

    def compute_profile_completeness(self, profile: CandidateProfile) -> float:
        """
        Compute weighted profile completeness score.

        Each field has a weight; populated fields contribute their weight to score.

        Args:
            profile: Full CandidateProfile.

        Returns:
            Completeness score in [0.0, 1.0].
        """
        score = 0.0
        for field, weight in _COMPLETENESS_FIELD_WEIGHTS.items():
            val = getattr(profile, field, None)
            if val is None:
                continue
            if isinstance(val, str) and val.strip() or isinstance(val, list) and len(val) > 0 or isinstance(val, int | float) and val > 0:
                score += weight

        return clip(score / sum(_COMPLETENESS_FIELD_WEIGHTS.values()))

    def compute_career_velocity(
        self, experiences: list[WorkExperience], years: float
    ) -> float:
        """
        Compute career velocity: how fast the candidate has advanced.

        Measures the seniority progress (0→8 scale) relative to career age.
        High velocity = reaching senior/lead roles quickly.

        Args:
            experiences: List of work experiences.
            years: Total years of experience.

        Returns:
            Career velocity score in [0.0, 1.0].
        """
        if not experiences or years < 1:
            return 0.0

        from services.preprocessing.career_parser import _get_seniority_score

        if not experiences:
            return 0.0

        # Current (most recent) seniority
        current_titles = [
            e.title for e in experiences[:2] if e.title
        ]
        if not current_titles:
            return 0.0

        current_seniority = max(_get_seniority_score(t) for t in current_titles)
        max_seniority = 8.0  # executive level

        # Velocity = (seniority_level / max_level) / normalized_years
        seniority_ratio = safe_divide(current_seniority, max_seniority, 0.0)
        # Normalize years: 10 years to reach top = 1.0 velocity
        year_factor = clip(years / 10.0)

        if year_factor < EPSILON:
            return clip(seniority_ratio)

        # High seniority in fewer years = high velocity
        velocity = safe_divide(seniority_ratio, year_factor, 0.0)
        return clip(velocity)

    def compute_skill_consistency(self, experiences: list[WorkExperience]) -> float:
        """
        Compute skill coherence across career stages.

        Measures overlap between skills used in different roles.
        High overlap = consistent domain focus; low overlap = scattered.

        Args:
            experiences: List of work experiences.

        Returns:
            Consistency score in [0.0, 1.0].
        """
        # Collect skills from each experience
        exp_skills = [
            set(e.skills_used) for e in experiences
            if e.skills_used
        ]

        if len(exp_skills) < 2:
            return 0.6  # Not enough data → neutral

        # Compute pairwise Jaccard similarity
        total_pairs = 0
        total_similarity = 0.0
        for i in range(len(exp_skills)):
            for j in range(i + 1, len(exp_skills)):
                intersection = len(exp_skills[i] & exp_skills[j])
                union = len(exp_skills[i] | exp_skills[j])
                if union > 0:
                    total_similarity += intersection / union
                    total_pairs += 1

        if total_pairs == 0:
            return 0.5

        avg_similarity = total_similarity / total_pairs
        return clip(avg_similarity)

    def compute_job_hop_risk(self, experiences: list[WorkExperience]) -> float:
        """
        Compute job-hopping risk based on short tenure frequency.

        Job-hopping risk = fraction of roles with tenure < MIN_TENURE_MONTHS_STABLE.

        Args:
            experiences: List of work experiences.

        Returns:
            Risk score in [0.0, 1.0]. Higher = more risky.
        """
        if not experiences:
            return 0.0

        tenures = [
            e.duration_months for e in experiences
            if e.duration_months is not None
        ]

        if not tenures:
            return 0.2  # Unknown → low default risk

        short_tenures = sum(1 for t in tenures if t < MIN_TENURE_MONTHS_STABLE)
        risk = safe_divide(float(short_tenures), float(len(tenures)), 0.0)

        # Apply extra penalty for very recent job-hopping (last 2 roles)
        recent_short = sum(
            1 for e in experiences[:2]
            if e.duration_months is not None and e.duration_months < MIN_TENURE_MONTHS_STABLE
        )
        extra_penalty = recent_short * 0.1

        return clip(risk + extra_penalty)

    def compute_gap_risk(self, experiences: list[WorkExperience]) -> float:
        """
        Compute career gap risk from employment gaps.

        Uses the longest gap as primary signal.

        Args:
            experiences: List of work experiences.

        Returns:
            Risk score in [0.0, 1.0]. Higher = more risky.
        """
        if not experiences:
            return 0.0

        gaps = self._career_parser.find_career_gaps(experiences)
        if not gaps:
            return 0.0

        # Primary signal: longest gap
        longest_gap_months = gaps[0][2]

        if longest_gap_months < CAREER_GAP_THRESHOLD_MONTHS:
            return 0.0
        elif longest_gap_months < 12:
            return 0.2
        elif longest_gap_months < 24:
            return 0.5
        elif longest_gap_months < 36:
            return 0.7
        else:
            return 0.9

    def compute_education_level_score(
        self, education: list
    ) -> float:
        """
        Compute a score based on the highest education level achieved.

        Args:
            education: List of EducationEntry objects.

        Returns:
            Education level score in [0.0, 1.0].
        """
        if not education:
            return 0.3  # Unknown → assume some education

        max_score = 0.0
        for edu in education:
            level_score = _EDU_LEVEL_SCORES.get(edu.level, 0.3)
            max_score = max(max_score, level_score)

        return clip(max_score)

    def extract_features(self, profile: CandidateProfile) -> CandidateFeatures:
        """Compatibility wrapper for extract_all."""
        return self.extract_all(profile)

    def build_evidence(self, profile: CandidateProfile, features: CandidateFeatures):
        """Compatibility wrapper to compile evidence ledger using EvidenceEngine."""
        from services.intelligence.evidence_engine import EvidenceEngine
        engine = EvidenceEngine()
        return engine.build_ledger(profile, features)
