"""
TalentGraph AI — Feature Ranker

Performs Stage 2 feature-based ranking. Filters Stage 1 hybrid retrieval output
from 2,000 to 200 candidates by combining precomputed feature vectors and
JD-dependent scores.
"""
from __future__ import annotations

import numpy as np

from services.preprocessing.feature_store import FeatureStore
from shared.constants import STAGE2_TOP_K
from shared.logging_setup import get_logger
from shared.types.candidate import CandidateFeatures
from shared.types.job import JobGenome, JobProfile

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
        candidate_ids: list[str],
        job_profile: JobProfile,
        job_genome: JobGenome,
        top_k: int = STAGE2_TOP_K,
    ) -> list[tuple[str, float, CandidateFeatures]]:
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

            # Map features to dict for TOPSIS evaluation
            features_dict = {
                "experience_score": features_obj.experience_score,
                "skill_coverage": features_obj.skill_coverage,
                "semantic_similarity": features_obj.domain_match,
                "domain_match": features_obj.domain_match,
                "career_velocity": features_obj.career_velocity,
                "leadership_score": features_obj.leadership_score,
                "education_score": features_obj.education_score,
                "stability_score": features_obj.career_stability,
                "certifications_score": float(features_obj.certification_count) / 5.0,
                "availability_score": features_obj.hiring_availability,
            }

            scored_candidates.append((cid, features_dict, features_obj))

        if not scored_candidates:
            return []

        # ── TOPSIS Algorithm Implementation ──────────────────────────────────────
        # Weights normalized
        weights_dict = job_genome.weights or {
            "experience_score": 0.15,
            "skill_coverage": 0.25,
            "semantic_similarity": 0.15,
            "domain_match": 0.10,
            "career_velocity": 0.10,
            "leadership_score": 0.08,
            "stability_score": 0.07,
            "availability_score": 0.10,
        }

        # Pseudo-Relevance Feedback: Self-calibrate default fallback weights if JD is double-vague
        is_fallback = job_genome.weights is None or (
            abs(job_genome.weights.get("experience_score", 0.0) - 0.15) < 0.01 and
            abs(job_genome.weights.get("skill_coverage", 0.0) - 0.20) < 0.01
        )
        if is_fallback and candidate_ids:
            feedback_sample = candidate_ids[:30]
            sample_feats = [features_map[cid] for cid in feedback_sample if cid in features_map]
            if sample_feats:
                avg_exp = float(np.mean([f.get("experience_score", 0.0) for f in sample_feats]))
                avg_lead = float(np.mean([f.get("leadership_score", 0.0) for f in sample_feats]))
                avg_stab = float(np.mean([f.get("stability_score", 0.0) for f in sample_feats]))
                weights_dict["experience_score"] = 0.15 * (1.0 + avg_exp)
                weights_dict["skill_coverage"] = 0.20 * (1.0 - avg_lead) # Inverse manager check
                weights_dict["leadership_score"] = 0.08 * (1.0 + avg_lead)
                weights_dict["stability_score"] = 0.08 * (1.0 + avg_stab)

        keys = list(weights_dict.keys())
        w_vals = np.array([weights_dict.get(k, 0.01) for k in keys])
        w_normalized = w_vals / np.sum(w_vals)

        # Build Decision Matrix
        matrix = []
        for _, f_dict, _ in scored_candidates:
            matrix.append([f_dict.get(k, 0.0) for k in keys])
        matrix = np.array(matrix)

        # Vector normalization
        sq_sums = np.sqrt(np.sum(matrix ** 2, axis=0))
        # Prevent division by zero
        sq_sums[sq_sums == 0] = 1e-8
        matrix_norm = matrix / sq_sums

        # Weighted Normalized Decision Matrix
        matrix_weighted = matrix_norm * w_normalized

        # Ideal positive and negative solutions
        ideal_best = np.max(matrix_weighted, axis=0)
        ideal_worst = np.min(matrix_weighted, axis=0)

        # Distances to ideal solutions
        d_best = np.sqrt(np.sum((matrix_weighted - ideal_best) ** 2, axis=1))
        d_worst = np.sqrt(np.sum((matrix_weighted - ideal_worst) ** 2, axis=1))

        # Closeness coefficients (TOPSIS score)
        denom = d_best + d_worst
        denom[denom == 0] = 1e-8
        topsis_scores = d_worst / denom

        # Build final list
        final_ranked = []
        for idx, (cid, _, f_obj) in enumerate(scored_candidates):
            final_ranked.append((cid, float(topsis_scores[idx]), f_obj))

        # Sort descending by TOPSIS closeness coefficient score
        final_ranked.sort(key=lambda x: x[1], reverse=True)
        truncated = final_ranked[:top_k]

        logger.info(f"Feature Ranker complete: ranked {len(scored_candidates)} candidates using TOPSIS engine down to {len(truncated)}")
        return truncated
