"""
TalentGraph AI — Feature Ranker

Performs Stage 2 feature-based ranking. Filters Stage 1 hybrid retrieval output
from 2,000 to 200 candidates by combining precomputed feature vectors and
JD-dependent scores.
"""
from __future__ import annotations

from typing import List, Dict, Any, Tuple
import numpy as np

from shared.constants import STAGE2_TOP_K
from shared.logging_setup import get_logger
from shared.utils.math_utils import weighted_average, cosine_similarity
from services.preprocessing.feature_store import FeatureStore
from shared.types.job import JobProfile, JobGenome
from shared.types.candidate import CandidateProfile, CandidateFeatures

logger = get_logger(__name__)


class FeatureRanker:
    """
    Ranks Stage 1 candidates using weighted multi-feature scoring.
    """

    def __init__(self, db: FeatureStore) -> None:
        """Initialize the feature ranker."""
        self.db = db
        logger.info("FeatureRanker initialised")

    def rank_candidates(
        self,
        candidate_ids: List[str],
        job_profile: JobProfile,
        job_genome: JobGenome,
        top_k: int = STAGE2_TOP_K,
    ) -> List[Tuple[str, float, CandidateFeatures]]:
        """
        Rank candidate IDs and output the top candidates with their feature vectors.

        Args:
            candidate_ids: List of candidates from Stage 1 retrieval.
            job_profile: Structured job posting profile.
            job_genome: Job target genome and weights.
            top_k: Number of ranked results to return.

        Returns:
            A list of tuples: (candidate_id, Stage 2 score, CandidateFeatures object).
        """
        if not candidate_ids:
            return []

        # 1. Fetch precomputed features from Feature Store in bulk
        df_features = self.db.get_features_dataframe(candidate_ids)
        if df_features.is_empty():
            logger.warning("No features found in store for candidates.")
            return []

        # Convert to dictionary mapping candidate_id -> feature row
        features_map = {}
        for row in df_features.to_dicts():
            cid = row["candidate_id"]
            features_map[cid] = row

        job_required_skills = set(job_profile.all_required_skill_names)
        job_all_skills = set(job_profile.all_skill_names)

        scored_candidates = []

        # 2. Score each candidate
        for cid in candidate_ids:
            if cid not in features_map:
                continue

            row = features_map[cid]
            profile = self.db.get_candidate_profile(cid)
            if not profile:
                continue

            # Calculate JD-dependent features:
            
            # A. Skill Coverage
            candidate_skills = set(profile.skills or [])
            if job_all_skills:
                skill_coverage = len(candidate_skills.intersection(job_all_skills)) / len(job_all_skills)
            else:
                skill_coverage = 0.5

            # B. Domain Match
            # Check overlap in domains or use primary domain string matching
            domain_match = 0.0
            if job_profile.primary_domain:
                # If candidate has primary domain skills, score domain match higher
                domain_skills = set(job_profile.all_required_skill_names)
                if domain_skills:
                    domain_overlap = len(candidate_skills.intersection(domain_skills)) / len(domain_skills)
                    domain_match = domain_overlap * 0.7 + (0.3 if job_profile.primary_domain in [s.lower() for s in profile.skills] else 0.0)
                else:
                    domain_match = 0.5
            else:
                domain_match = 0.5

            # Create CandidateFeatures object with both precomputed and JD-dependent features
            features_obj = CandidateFeatures(
                candidate_id=cid,
                experience_score=row.get("experience_score", 0.0),
                career_stability=row.get("stability_score", row.get("career_stability", 0.0)),
                promotion_score=row.get("promotion_score", 0.0),
                skill_coverage=skill_coverage,
                domain_match=domain_match,
                leadership_score=row.get("leadership_score", 0.0),
                learning_score=row.get("learning_score", 0.0),
                research_score=row.get("research_score", 0.0),
                behavior_score=row.get("behavior_score", 0.0),
                hiring_availability=row.get("availability_score", row.get("hiring_availability", 0.0)),
                profile_completeness=row.get("profile_completeness", 0.0),
                career_velocity=row.get("career_velocity", 0.0),
                skill_consistency=row.get("skill_consistency", 0.0),
                job_hop_risk=row.get("job_hop_risk", 0.0),
                gap_risk=row.get("gap_risk", 0.0),
                education_level_score=row.get("education_score", 0.0),
                certification_count=int(row.get("certifications_score", 0.0) * 5.0),
            )

            # Map features to dict for weighted average
            features_dict = {
                "experience_score": features_obj.experience_score,
                "skill_coverage": features_obj.skill_coverage,
                "semantic_similarity": features_obj.domain_match,
                "domain_match": features_obj.domain_match,
                "career_velocity": features_obj.career_velocity,
                "leadership_score": features_obj.leadership_score,
                "education_score": features_obj.education_score,
                "stability_score": features_obj.career_stability,
                "certifications_score": features_obj.certifications_score,
                "availability_score": features_obj.hiring_availability,
            }

            # Calculate overall Stage 2 score
            weights = job_genome.weights or {
                "experience_score": 0.15,
                "skill_coverage": 0.25,
                "semantic_similarity": 0.15,
                "domain_match": 0.10,
                "career_velocity": 0.10,
                "leadership_score": 0.08,
                "stability_score": 0.07,
                "availability_score": 0.10,
            }

            score = weighted_average(features_dict, weights)
            scored_candidates.append((cid, score, features_obj))

        # Sort descending by score
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        truncated = scored_candidates[:top_k]
        
        logger.info(f"Feature Ranker complete: ranked {len(scored_candidates)} candidates down to {len(truncated)}")
        return truncated
