"""
TalentGraph AI — Job Intelligence Engine

Extracts job requirements, seniority level, and domains from a raw job description
to construct the structured JobProfile, IdealCandidatePersona, and JobGenome.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple, Any

from shared.logging_setup import get_logger
from shared.types.job import (
    JobRaw,
    JobProfile,
    SkillRequirement,
    IdealCandidatePersona,
    JobGenome,
    ExperienceLevel,
    JobType,
)
from shared.utils.text_utils import (
    normalize_text,
    extract_skills_from_text,
    extract_years_of_experience,
    detect_seniority_from_title,
    tokenize_for_bm25,
)

logger = get_logger(__name__)

# Domain keyword maps
DOMAINS = {
    "machine learning": [
        "machine learning", "ml", "deep learning", "nlp", "computer vision",
        "pytorch", "tensorflow", "scikit-learn", "transformers", "llm"
    ],
    "data science": [
        "data science", "data scientist", "pandas", "numpy", "statistics",
        "analytics", "regression", "clustering"
    ],
    "backend": [
        "backend", "django", "flask", "fastapi", "spring boot", "express",
        "node", "apis", "databases", "postgresql", "mysql"
    ],
    "frontend": [
        "frontend", "react", "angular", "vue", "typescript", "javascript",
        "html", "css", "tailwind", "next.js"
    ],
    "devops": [
        "devops", "docker", "kubernetes", "k8s", "aws", "gcp", "azure",
        "ci/cd", "jenkins", "terraform", "ansible"
    ],
    "data engineering": [
        "data engineering", "spark", "hadoop", "kafka", "etl", "airflow",
        "snowflake", "redshift", "bigquery"
    ],
}


class JobIntelligenceEngine:
    """
    Parses raw job descriptions deterministically to construct profiles,
    personas, and target genomes.
    """

    def __init__(self) -> None:
        """Initialize the job intelligence engine."""
        logger.info("JobIntelligenceEngine initialised")

    def analyze_job(
        self, raw_job: JobRaw
    ) -> Tuple[JobProfile, IdealCandidatePersona, JobGenome]:
        """
        Analyze a raw job description and construct matching structures.

        Args:
            raw_job: Raw job description inputs.

        Returns:
            A tuple of (JobProfile, IdealCandidatePersona, JobGenome).
        """
        logger.info(f"Analyzing job description: {raw_job.title}")

        text = raw_job.raw_text or f"{raw_job.title}\n\n{raw_job.description}"
        norm_text = normalize_text(text)

        # 1. Seniority Level Detection
        seniority = detect_seniority_from_title(raw_job.title)

        # 2. Years of Experience Extraction
        extracted_yoe = extract_years_of_experience(norm_text)
        if extracted_yoe > 0.0:
            min_yoe = extracted_yoe
            max_yoe = min_yoe + 5.0
        else:
            # Seniority default fallbacks
            min_yoe = {
                ExperienceLevel.ENTRY: 0.0,
                ExperienceLevel.JUNIOR: 1.0,
                ExperienceLevel.MID: 3.0,
                ExperienceLevel.SENIOR: 6.0,
                ExperienceLevel.PRINCIPAL: 10.0,
                ExperienceLevel.EXECUTIVE: 15.0,
            }.get(seniority, 2.0)
            max_yoe = min_yoe + 4.0 if min_yoe > 0 else None

        # 3. Domain Detection
        primary_domain = None
        secondary_domains = []
        domain_counts = {}
        for domain, kws in DOMAINS.items():
            count = sum(1 for kw in kws if kw in norm_text)
            if count > 0:
                domain_counts[domain] = count

        if domain_counts:
            sorted_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)
            primary_domain = sorted_domains[0][0]
            secondary_domains = [d[0] for d in sorted_domains[1:3]]

        # 4. Extract Skills
        skills = extract_skills_from_text(norm_text)
        required_skills = []
        preferred_skills = []

        # Simple heuristic: if mentioned near "required", "must", "essential", mark required
        # For simplicity, we treat first 70% as required, rest preferred
        split_idx = int(len(skills) * 0.7)
        req_list = skills[:split_idx]
        pref_list = skills[split_idx:]

        for s in req_list:
            required_skills.append(
                SkillRequirement(
                    skill=s,
                    importance=1.0 if s in raw_job.title.lower() else 0.8,
                    min_years=min_yoe,
                    is_mandatory=True,
                    category=primary_domain,
                )
            )
        for s in pref_list:
            preferred_skills.append(s)

        # 5. Check if leadership/remote/travel required
        leadership_required = any(
            w in norm_text for w in ["lead", "manage", "director", "mentor", "leadership"]
        )
        remote_friendly = any(
            w in norm_text for w in ["remote", "work from home", "wfh", "hybrid"]
        )

        # Build JobProfile
        profile = JobProfile(
            job_id=raw_job.job_id,
            title=raw_job.title,
            seniority_level=seniority,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            min_experience_years=min_yoe,
            max_experience_years=max_yoe,
            primary_domain=primary_domain,
            secondary_domains=secondary_domains,
            leadership_required=leadership_required,
            remote_friendly=remote_friendly,
        )

        # Build IdealCandidatePersona
        ideal_yoe = min_yoe + 2.0
        # ── Dynamic Archetype Overlap Weight Engine ────────────────────────────────
        # Resolve vague cold-starts by matching against structured archetype distributions
        archetypes = {
            "technical": {
                "keywords": ["developer", "engineer", "programmer", "coding", "software", "backend", "frontend", "fullstack", "architect", "sysadmin", "database", "infrastructure", "pytorch", "tensorflow", "fastapi", "django"],
                "weights": {
                    "experience_score": 0.12,
                    "skill_coverage": 0.35,
                    "semantic_similarity": 0.15,
                    "domain_match": 0.15,
                    "career_velocity": 0.08,
                    "leadership_score": 0.03,
                    "education_score": 0.04,
                    "stability_score": 0.06,
                    "certifications_score": 0.04,
                    "availability_score": 0.03,
                }
            },
            "leadership": {
                "keywords": ["lead", "manager", "director", "head", "executive", "vp", "president", "chief", "cto", "cio", "cfo", "coo", "manage", "leadership", "teams", "scrum", "agile", "supervise"],
                "weights": {
                    "experience_score": 0.15,
                    "skill_coverage": 0.10,
                    "semantic_similarity": 0.10,
                    "domain_match": 0.10,
                    "career_velocity": 0.15,
                    "leadership_score": 0.30,
                    "education_score": 0.05,
                    "stability_score": 0.10,
                    "certifications_score": 0.02,
                    "availability_score": 0.03,
                }
            },
            "research": {
                "keywords": ["researcher", "scientist", "phd", "academic", "publications", "journals", "statistics", "math", "mathematical", "postdoc", "fellow", "lab", "novel", "papers"],
                "weights": {
                    "experience_score": 0.10,
                    "skill_coverage": 0.15,
                    "semantic_similarity": 0.15,
                    "domain_match": 0.10,
                    "career_velocity": 0.05,
                    "leadership_score": 0.03,
                    "education_score": 0.25,
                    "stability_score": 0.05,
                    "certifications_score": 0.02,
                    "availability_score": 0.05,
                }
            }
        }

        # Count occurrences of archetype keywords in JD text
        match_scores = {}
        total_matches = 0
        for arch_name, arch_data in archetypes.items():
            matches = sum(1 for kw in arch_data["keywords"] if kw in norm_text)
            match_scores[arch_name] = matches
            total_matches += matches

        # ── Semantic Title-Archetype Fallback ────────────────────────────────────
        # Resolve zero-vocabulary descriptions by analyzing standard title terms
        if total_matches == 0:
            title_lower = raw_job.title.lower()
            if any(w in title_lower for w in ["lead", "manager", "director", "head", "vp", "president", "chief", "cto", "cio", "coo", "officer", "scrum", "agile", "supervise"]):
                match_scores = {"technical": 1, "leadership": 4, "research": 0}
                total_matches = 5
            elif any(w in title_lower for w in ["researcher", "scientist", "phd", "academic", "postdoc", "fellow", "professor", "lab"]):
                match_scores = {"technical": 2, "leadership": 0, "research": 4}
                total_matches = 6
            elif any(w in title_lower for w in ["developer", "engineer", "programmer", "coding", "software", "backend", "frontend", "fullstack", "architect", "sysadmin", "analyst", "devops"]):
                match_scores = {"technical": 5, "leadership": 1, "research": 1}
                total_matches = 7

        # Interpolate weights based on overlap scores
        feature_weights = {
            "experience_score": 0.0,
            "skill_coverage": 0.0,
            "semantic_similarity": 0.0,
            "domain_match": 0.0,
            "career_velocity": 0.0,
            "leadership_score": 0.0,
            "education_score": 0.0,
            "stability_score": 0.0,
            "certifications_score": 0.0,
            "availability_score": 0.0,
        }

        if total_matches > 0:
            for arch_name, score in match_scores.items():
                weight_fraction = score / total_matches
                arch_weights = archetypes[arch_name]["weights"]
                for k in feature_weights.keys():
                    feature_weights[k] += arch_weights.get(k, 0.01) * weight_fraction
        else:
            # Balanced default fallback for extremely vague job descriptions & titles
            feature_weights = {
                "experience_score": 0.15,
                "skill_coverage": 0.20,
                "semantic_similarity": 0.15,
                "domain_match": 0.12,
                "career_velocity": 0.08,
                "leadership_score": 0.08,
                "education_score": 0.08,
                "stability_score": 0.08,
                "certifications_score": 0.04,
                "availability_score": 0.04,
            }

        # Normalize weights to sum strictly to 1.0
        w_sum = sum(feature_weights.values())
        if w_sum > 0:
            feature_weights = {k: v / w_sum for k, v in feature_weights.items()}

        # Boost leadership if role requires it
        if leadership_required:
            feature_weights["leadership_score"] = 0.15
            feature_weights["experience_score"] = 0.12

        persona = IdealCandidatePersona(
            job_id=raw_job.job_id,
            must_have_skills=[s.skill for s in required_skills],
            nice_to_have_skills=preferred_skills,
            min_experience_years=min_yoe,
            ideal_experience_years=ideal_yoe,
            expected_seniority=seniority,
            domain_weight=0.8,
            technical_weight=0.9 if primary_domain in ["machine learning", "backend", "data engineering"] else 0.7,
            leadership_weight=0.8 if leadership_required else 0.4,
            feature_weights=feature_weights,
            implicit_expectations=[
                f"Strong communication in a {primary_domain or 'technical'} role",
                "Ability to work in agile teams",
            ],
        )

        # Build Job Genome Target
        # Set ideal targets [0.0, 1.0]
        target_exp = min(1.0, min_yoe / 10.0)
        target_leadership = 0.8 if leadership_required else 0.3

        # BM25 terms for exact retrieval
        key_terms = tokenize_for_bm25(raw_job.title) + [s.skill for s in required_skills[:5]]

        genome = JobGenome(
            job_id=raw_job.job_id,
            target_experience_score=target_exp,
            target_career_stability=0.75,
            target_skill_coverage=0.85,
            target_domain_match=0.80,
            target_leadership_score=target_leadership,
            target_learning_score=0.70,
            target_behavior_score=0.70,
            weights=feature_weights,
            key_terms=key_terms,
        )

        return profile, persona, genome
