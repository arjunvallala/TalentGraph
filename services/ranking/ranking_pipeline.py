"""
TalentGraph AI — Ranking Pipeline

Orchestrates the entire multi-stage ranking pipeline:
1. Job description analysis (Job Intelligence)
2. Stage 1: Hybrid Retrieval (FAISS semantic + BM25 keyword RRF)
3. Stage 2: Feature Ranking (weighted multi-feature score)
4. Stage 3: Hiring Committee Council consensus
5. Stage 4: Explainability narrative generation
"""
from __future__ import annotations

import time
from datetime import datetime

from services.explainability.explanation_generator import ExplanationGenerator
from services.intelligence.candidate_intelligence import CandidateIntelligenceEngine
from services.intelligence.job_intelligence import JobIntelligenceEngine
from services.preprocessing.feature_store import FeatureStore
from services.ranking.confidence_engine import ConfidenceEngine
from services.ranking.council.hiring_council import HiringCouncil
from services.ranking.feature_ranker import FeatureRanker
from services.retrieval.hybrid_retrieval import HybridRetrievalEngine
from shared.config import Settings
from shared.constants import (
    FINAL_TOP_K,
    STAGE1_TOP_K,
    STAGE2_TOP_K,
    STAGE3_TOP_K,
)
from shared.logging_setup import get_logger
from shared.types.job import JobRaw
from shared.types.ranking import (
    CandidateResult,
    HiringRecommendation,
    RankedList,
    RankingStageResult,
)

logger = get_logger(__name__)


class RankingPipeline:
    """
    Coordinates and executes the 4-stage talent ranking workflow.
    """

    def __init__(self, config: Settings, feature_store: FeatureStore | None = None) -> None:
        """Initialize all pipeline engine stages."""
        self.settings = config
        self.db = feature_store or FeatureStore(config.duckdb_path)
        self.job_engine = JobIntelligenceEngine()
        self.candidate_engine = CandidateIntelligenceEngine()
        self.retrieval_engine = HybridRetrievalEngine(self.db)
        self.ranker = FeatureRanker(self.db)
        self.council = HiringCouncil()
        self.confidence_engine = ConfidenceEngine()
        self.explanation_generator = ExplanationGenerator()
        logger.info("RankingPipeline initialized")

    def rank(self, raw_job: JobRaw, limit: int = FINAL_TOP_K) -> RankedList:
        """Alias for run_pipeline to match scripts/rank.py execution."""
        return self.run_pipeline(raw_job, limit)

    def run_pipeline(
        self, raw_job: JobRaw, limit: int = FINAL_TOP_K
    ) -> RankedList:
        """
        Execute the end-to-end ranking pipeline on raw job details.

        Args:
            raw_job: Raw job title and description text.
            limit: Size of final shortlist.

        Returns:
            RankedList object containing all candidates, stage logs, and descriptions.
        """
        pipeline_start = time.perf_counter()
        self.db.connect()

        # ── STEP 1: JOB DESCRIPTION INTELLIGENCE ──
        logger.info("Analyzing job description requirements...")
        job_profile, job_persona, job_genome = self.job_engine.analyze_job(raw_job)

        # Generate query vector embedding for retrieval
        from services.preprocessing.embedding_generator import EmbeddingGenerator
        emb_generator = EmbeddingGenerator(self.settings.embedding_model_name)
        emb_generator.load_model()
        logger.info("Generating dense vector embedding for query...")
        query_embedding = emb_generator.encode_batch([raw_job.raw_text])[0]
        job_genome.embedding = query_embedding.tolist()

        # Save job profile to Feature Store
        self.db.save_job(
            raw_job.job_id,
            raw_job.title,
            raw_job.description,
            job_profile,
            job_genome.weights,
            job_genome.model_dump(),
        )

        stage_results: list[RankingStageResult] = []

        # ── STAGE 1: HYBRID RETRIEVAL ──
        stage1_start = time.perf_counter()
        logger.info("--- Stage 1: Running Hybrid Retrieval ---")
        retrieved_ids = self.retrieval_engine.retrieve(
            job_genome.embedding, job_genome.key_terms, top_k=STAGE1_TOP_K
        )
        stage1_duration = time.perf_counter() - stage1_start

        stage_results.append(
            RankingStageResult(
                stage=1,
                stage_name="Hybrid Retrieval",
                input_count=100000,  # Estimated corpus size
                output_count=len(retrieved_ids),
                duration_seconds=stage1_duration,
                candidate_ids=retrieved_ids,
                scores={cid: float(1.0 / (i + 1)) for i, cid in enumerate(retrieved_ids)},
            )
        )

        # ── STAGE 2: FEATURE-BASED RANKING ──
        stage2_start = time.perf_counter()
        logger.info("--- Stage 2: Running Feature Ranking ---")
        stage2_ranked = self.ranker.rank_candidates(
            retrieved_ids, job_profile, job_genome, top_k=STAGE2_TOP_K
        )
        stage2_duration = time.perf_counter() - stage2_start

        stage2_ids = [res[0] for res in stage2_ranked]
        stage2_scores = {res[0]: res[1] for res in stage2_ranked}
        stage2_features_map = {res[0]: res[2] for res in stage2_ranked}

        stage_results.append(
            RankingStageResult(
                stage=2,
                stage_name="Feature Ranking",
                input_count=len(retrieved_ids),
                output_count=len(stage2_ranked),
                duration_seconds=stage2_duration,
                candidate_ids=stage2_ids,
                scores=stage2_scores,
            )
        )

        # ── STAGE 3: COMMITTEE CONSENSUS & CONSENSUS SCORING ──
        stage3_start = time.perf_counter()
        logger.info("--- Stage 3: Running Hiring Council Committee ---")

        scored_results: list[CandidateResult] = []

        # Evaluate top candidates
        for _rank_idx, cid in enumerate(stage2_ids[:STAGE3_TOP_K]):
            features = stage2_features_map[cid]
            profile = self.db.get_candidate_profile(cid)
            evidence_obj = None
            conn = self.db.connect()
            ev_res = conn.execute("SELECT evidence FROM candidate_evidence WHERE candidate_id = ?", [cid]).fetchone()
            if ev_res:
                import json

                from shared.types.candidate import CandidateEvidence
                ev_data = json.loads(ev_res[0])
                evidence_obj = CandidateEvidence(
                    candidate_id=cid,
                    skill_evidence=ev_data.get("skill_evidence", {}),
                    experience_evidence=ev_data.get("experience_evidence", []),
                    leadership_evidence=ev_data.get("leadership_evidence", []),
                    learning_evidence=ev_data.get("learning_evidence", []),
                    stability_evidence=ev_data.get("stability_evidence", []),
                    risk_evidence=ev_data.get("risk_evidence", []),
                    behavior_evidence=ev_data.get("behavior_evidence", []),
                    evidence_strength=ev_data.get("evidence_strength", 0.9),
                )

            if not evidence_obj:
                from services.preprocessing.feature_extractor import FeatureExtractor
                extractor = FeatureExtractor()
                evidence_obj = extractor.build_evidence(profile, features)

            # Build multidimensional genome
            genome = self.candidate_engine.build_genome(profile, features, evidence_obj)

            # Get Hiring Council Consensus Decision
            decision = self.council.evaluate_candidate(genome, job_genome)

            # ── STAGE 4: EXPLAINABILITY & CONFIDENCE ESTIMATION ──
            # Determine Hiring Recommendation
            # Strong Hire: score ≥ 0.82
            # Hire:        score ≥ 0.68
            # Consider:    score ≥ 0.52
            # Pass:        score ≥ 0.38
            # Reject:      score < 0.38
            f_score = decision.final_score
            if f_score >= 0.82:
                rec = HiringRecommendation.STRONG_HIRE
            elif f_score >= 0.68:
                rec = HiringRecommendation.HIRE
            elif f_score >= 0.52:
                rec = HiringRecommendation.CONSIDER
            elif f_score >= 0.38:
                rec = HiringRecommendation.PASS
            else:
                rec = HiringRecommendation.REJECT

            # Confidence Level
            conf_val, conf_level = self.confidence_engine.estimate_confidence(features, decision)

            # Explanation Report
            explanation = self.explanation_generator.generate_explanation(
                cid, features, job_genome, decision, rec, conf_level.value
            )

            # Build CandidateResult
            candidate_result = CandidateResult(
                candidate_id=cid,
                rank=0,  # Filled after sorting
                overall_score=f_score,
                confidence_level=conf_level,
                hiring_recommendation=rec,
                profile=profile,
                features=features,
                explanation=explanation,
                stage1_score=float(1.0 / (retrieved_ids.index(cid) + 1)),
                stage2_score=stage2_scores[cid],
                stage3_score=decision.council_score,
                council_scores=decision.individual_scores,
                feature_scores={
                    "experience_score": features.experience_score,
                    "skill_coverage": features.skill_coverage,
                    "domain_match": features.domain_match,
                    "career_velocity": features.career_velocity,
                },
                ranked_at=datetime.utcnow(),
            )
            scored_results.append(candidate_result)

        # Sort descending by consensus overall score
        scored_results.sort(key=lambda x: x.overall_score, reverse=True)

        # Truncate and assign 1-indexed ranks
        final_list = scored_results[:limit]
        for rank_idx, cand in enumerate(final_list):
            cand.rank = rank_idx + 1

        stage3_duration = time.perf_counter() - stage3_start
        stage_results.append(
            RankingStageResult(
                stage=3,
                stage_name="Hiring Council consensus",
                input_count=len(stage2_ids[:STAGE3_TOP_K]),
                output_count=len(final_list),
                duration_seconds=stage3_duration,
                candidate_ids=[c.candidate_id for c in final_list],
                scores={c.candidate_id: c.overall_score for c in final_list},
            )
        )

        pipeline_duration = time.perf_counter() - pipeline_start

        # Persist rankings to DB for dashboard read-out
        rankings_payload = []
        for c in final_list:
            rankings_payload.append({
                "candidate_id": c.candidate_id,
                "rank": c.rank,
                "overall_score": c.overall_score,
                "confidence_level": c.confidence_level.value,
                "hiring_recommendation": c.hiring_recommendation.value,
                "explanation": c.explanation.model_dump() if c.explanation else {},
                "stage_scores": {
                    "stage1_score": c.stage1_score,
                    "stage2_score": c.stage2_score,
                    "stage3_score": c.stage3_score,
                },
            })
        self.db.save_rankings(raw_job.job_id, rankings_payload)

        self.db.close()

        return RankedList(
            job_id=raw_job.job_id,
            candidates=final_list,
            total_processed=len(retrieved_ids),
            stage_results=stage_results,
            ranking_duration_seconds=pipeline_duration,
            ranked_at=datetime.utcnow(),
        )
