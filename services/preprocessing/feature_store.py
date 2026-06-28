"""
TalentGraph AI — DuckDB Feature Store

Responsible for writing, updating, and reading candidate profiles,
feature vectors, and evidence tables in DuckDB.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb
import polars as pl

from shared.config import settings
from shared.constants import (
    DUCKDB_CANDIDATE_TABLE,
    DUCKDB_EVIDENCE_TABLE,
    DUCKDB_FEATURES_TABLE,
    DUCKDB_JOBS_TABLE,
    DUCKDB_RANKINGS_TABLE,
)
from shared.logging_setup import get_logger
from shared.types.candidate import (
    CandidateEvidence,
    CandidateFeatures,
    CandidateProfile,
)
from shared.types.job import JobProfile
from shared.types.ranking import CandidateResult

logger = get_logger(__name__)


def safe_json_dumps(obj: Any) -> str:
    """Safely serialize an object to JSON, handling datetimes, enums, and Pydantic models."""
    from datetime import datetime
    from enum import Enum

    def default_serializer(o: Any) -> Any:
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Enum):
            return o.value
        if hasattr(o, "model_dump"):
            return o.model_dump(mode="json")
        return str(o)

    return json.dumps(obj, default=default_serializer)



class FeatureStore:
    """
    Manages DuckDB interactions for persistent storage of candidates,
    features, evidence, jobs, and rankings.
    """

    def __init__(self, db_path: str = settings.duckdb_path) -> None:
        """Initialize the feature store with the specified DuckDB file path."""
        self.db_path = db_path
        # Ensure parent directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        logger.info(f"FeatureStore initialized with DuckDB path: {db_path}")

    def connect(self) -> duckdb.DuckDBPyConnection:
        """Establish a connection to DuckDB. Reuses active connection if available."""
        if self.conn is None:
            self.conn = duckdb.connect(self.db_path)
            self._create_tables()
        return self.conn

    def close(self) -> None:
        """Close the DuckDB connection."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def _create_tables(self) -> None:
        """Create database tables if they do not exist."""
        conn = self.conn
        # Candidate Profiles table
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {DUCKDB_CANDIDATE_TABLE} (
                candidate_id VARCHAR PRIMARY KEY,
                name VARCHAR,
                current_title VARCHAR,
                current_company VARCHAR,
                location VARCHAR,
                email VARCHAR,
                phone VARCHAR,
                linkedin VARCHAR,
                years_of_experience DOUBLE,
                education JSON,
                work_experience JSON,
                skills JSON,
                certifications JSON,
                raw_text VARCHAR,
                embedding_id INTEGER
            )
        """)

        # Candidate Features table
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {DUCKDB_FEATURES_TABLE} (
                candidate_id VARCHAR PRIMARY KEY,
                experience_score DOUBLE,
                skill_coverage DOUBLE,
                semantic_similarity DOUBLE,
                domain_match DOUBLE,
                career_velocity DOUBLE,
                leadership_score DOUBLE,
                education_score DOUBLE,
                stability_score DOUBLE,
                certifications_score DOUBLE,
                location_match DOUBLE,
                availability_score DOUBLE,
                research_score DOUBLE,
                behavior_score DOUBLE,
                profile_completeness DOUBLE,
                gap_risk DOUBLE,
                job_hop_risk DOUBLE,
                skill_consistency DOUBLE
            )
        """)

        # Candidate Evidence table
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {DUCKDB_EVIDENCE_TABLE} (
                candidate_id VARCHAR PRIMARY KEY,
                evidence JSON,
                timeline JSON
            )
        """)

        # Jobs table
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {DUCKDB_JOBS_TABLE} (
                job_id VARCHAR PRIMARY KEY,
                title VARCHAR,
                description VARCHAR,
                requirements JSON,
                weights JSON,
                genome JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Rankings table
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {DUCKDB_RANKINGS_TABLE} (
                job_id VARCHAR,
                candidate_id VARCHAR,
                rank INTEGER,
                overall_score DOUBLE,
                confidence_level VARCHAR,
                hiring_recommendation VARCHAR,
                explanation JSON,
                stage_scores JSON,
                PRIMARY KEY (job_id, candidate_id)
            )
        """)
        logger.debug("DuckDB tables verified/created")

    def save_candidate_profile(self, profile: CandidateProfile) -> None:
        """Save a single candidate profile to DuckDB."""
        conn = self.connect()
        edu_json = safe_json_dumps([e.model_dump() for e in (profile.education or [])])
        work_json = safe_json_dumps([w.model_dump() for w in (profile.work_experience or [])])
        skills_json = safe_json_dumps(profile.skills or [])
        certs_json = safe_json_dumps(profile.certifications or [])

        conn.execute(
            f"""
            INSERT OR REPLACE INTO {DUCKDB_CANDIDATE_TABLE} (
                candidate_id, name, current_title, current_company, location,
                email, phone, linkedin, years_of_experience, education,
                work_experience, skills, certifications, raw_text, embedding_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?::JSON, ?::JSON, ?::JSON, ?::JSON, ?, ?)
            """,
            [
                profile.candidate_id,
                profile.name or "",
                profile.current_title or "",
                profile.current_company or "",
                profile.location or "",
                profile.email or "",
                profile.phone or "",
                profile.linkedin or "",
                profile.years_of_experience or 0.0,
                edu_json,
                work_json,
                skills_json,
                certs_json,
                profile.raw_text or "",
                profile.embedding_id,
            ],
        )

    def save_candidate_features(self, features: CandidateFeatures) -> None:
        """Save a candidate's features to DuckDB."""
        conn = self.connect()
        conn.execute(
            f"""
            INSERT OR REPLACE INTO {DUCKDB_FEATURES_TABLE} (
                candidate_id, experience_score, skill_coverage, semantic_similarity,
                domain_match, career_velocity, leadership_score, education_score,
                stability_score, certifications_score, location_match, availability_score,
                research_score, behavior_score, profile_completeness, gap_risk,
                job_hop_risk, skill_consistency
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                features.candidate_id,
                features.experience_score,
                features.skill_coverage,
                features.semantic_similarity,
                features.domain_match,
                features.career_velocity,
                features.leadership_score,
                features.education_score,
                features.stability_score,
                features.certifications_score,
                features.location_match,
                features.availability_score,
                features.research_score,
                features.behavior_score,
                features.profile_completeness,
                features.gap_risk,
                features.job_hop_risk,
                features.skill_consistency,
            ],
        )

    def save_candidate_evidence(
        self, candidate_id: str, evidence: CandidateEvidence
    ) -> None:
        """Save a candidate's evidence to DuckDB."""
        conn = self.connect()
        evidence_json = safe_json_dumps(evidence.evidence or {})
        timeline_json = safe_json_dumps([t.model_dump() for t in (evidence.timeline or [])])

        conn.execute(
            f"""
            INSERT OR REPLACE INTO {DUCKDB_EVIDENCE_TABLE} (
                candidate_id, evidence, timeline
            ) VALUES (?, ?::JSON, ?::JSON)
            """,
            [candidate_id, evidence_json, timeline_json],
        )

    def get_candidate_profile(self, candidate_id: str) -> CandidateProfile | None:
        """Retrieve a candidate profile from DuckDB by ID."""
        conn = self.connect()
        res = conn.execute(
            f"SELECT * FROM {DUCKDB_CANDIDATE_TABLE} WHERE candidate_id = ?",
            [candidate_id],
        ).fetchone()

        if not res:
            return None

        # DuckDB returns columns in order of CREATE TABLE
        edu_list = json.loads(res[9]) if res[9] else []
        work_list = json.loads(res[10]) if res[10] else []
        skills_list = json.loads(res[11]) if res[11] else []
        certs_list = json.loads(res[12]) if res[12] else []

        return CandidateProfile(
            candidate_id=res[0],
            name=res[1],
            current_title=res[2],
            current_company=res[3],
            location=res[4],
            email=res[5],
            phone=res[6],
            linkedin=res[7],
            years_of_experience=res[8],
            education=edu_list,
            work_experience=work_list,
            skills=skills_list,
            certifications=certs_list,
            raw_text=res[13],
            embedding_id=res[14],
        )

    def get_candidate_features(self, candidate_id: str) -> CandidateFeatures | None:
        """Retrieve a candidate's features from DuckDB."""
        conn = self.connect()
        res = conn.execute(
            f"SELECT * FROM {DUCKDB_FEATURES_TABLE} WHERE candidate_id = ?",
            [candidate_id],
        ).fetchone()

        if not res:
            return None

        return CandidateFeatures(
            candidate_id=res[0],
            experience_score=res[1],
            skill_coverage=res[2],
            semantic_similarity=res[3],
            domain_match=res[4],
            career_velocity=res[5],
            leadership_score=res[6],
            education_score=res[7],
            stability_score=res[8],
            certifications_score=res[9],
            location_match=res[10],
            availability_score=res[11],
            research_score=res[12],
            behavior_score=res[13],
            profile_completeness=res[14],
            gap_risk=res[15],
            job_hop_risk=res[16],
            skill_consistency=res[17],
        )

    def save_job(self, job_id: str, title: str, description: str, profile: JobProfile, weights: dict[str, float], genome: dict[str, Any]) -> None:
        """Save a job description and parsed details to DuckDB."""
        conn = self.connect()
        reqs_json = safe_json_dumps(profile)
        weights_json = safe_json_dumps(weights)
        genome_json = safe_json_dumps(genome)

        conn.execute(
            f"""
            INSERT OR REPLACE INTO {DUCKDB_JOBS_TABLE} (
                job_id, title, description, requirements, weights, genome
            ) VALUES (?, ?, ?, ?::JSON, ?::JSON, ?::JSON)
            """,
            [job_id, title, description, reqs_json, weights_json, genome_json],
        )

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        """Retrieve a job profile and configuration from DuckDB."""
        conn = self.connect()
        res = conn.execute(
            f"SELECT title, description, requirements, weights, genome FROM {DUCKDB_JOBS_TABLE} WHERE job_id = ?",
            [job_id],
        ).fetchone()

        if not res:
            return None

        return {
            "job_id": job_id,
            "title": res[0],
            "description": res[1],
            "requirements": json.loads(res[2]) if res[2] else {},
            "weights": json.loads(res[3]) if res[3] else {},
            "genome": json.loads(res[4]) if res[4] else {},
        }

    def save_rankings(self, job_id: str, rankings: list[dict[str, Any]]) -> None:
        """Save final ranked results to DuckDB."""
        conn = self.connect()
        # Clean existing rankings for this job first
        conn.execute(f"DELETE FROM {DUCKDB_RANKINGS_TABLE} WHERE job_id = ?", [job_id])

        for rank_entry in rankings:
            expl_json = safe_json_dumps(rank_entry.get("explanation", {}))
            stage_json = safe_json_dumps(rank_entry.get("stage_scores", {}))

            conn.execute(
                f"""
                INSERT INTO {DUCKDB_RANKINGS_TABLE} (
                    job_id, candidate_id, rank, overall_score, confidence_level,
                    hiring_recommendation, explanation, stage_scores
                ) VALUES (?, ?, ?, ?, ?, ?, ?::JSON, ?::JSON)
                """,
                [
                    job_id,
                    rank_entry["candidate_id"],
                    rank_entry["rank"],
                    rank_entry["overall_score"],
                    rank_entry["confidence_level"],
                    rank_entry["hiring_recommendation"],
                    expl_json,
                    stage_json,
                ],
            )
        logger.info(f"Saved {len(rankings)} rankings for job {job_id}")

    def get_rankings(self, job_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Retrieve rankings for a specific job from DuckDB."""
        conn = self.connect()
        res = conn.execute(
            f"""
            SELECT r.candidate_id, r.rank, r.overall_score, r.confidence_level,
                   r.hiring_recommendation, r.explanation, r.stage_scores,
                   c.name, c.current_title, c.current_company
            FROM {DUCKDB_RANKINGS_TABLE} r
            JOIN {DUCKDB_CANDIDATE_TABLE} c ON r.candidate_id = c.candidate_id
            WHERE r.job_id = ?
            ORDER BY r.rank ASC
            LIMIT ?
            """,
            [job_id, limit],
        ).fetchall()

        out = []
        for row in res:
            out.append({
                "candidate_id": row[0],
                "rank": row[1],
                "overall_score": row[2],
                "confidence_level": row[3],
                "hiring_recommendation": row[4],
                "explanation": json.loads(row[5]) if row[5] else {},
                "stage_scores": json.loads(row[6]) if row[6] else {},
                "name": row[7],
                "current_title": row[8],
                "current_company": row[9],
            })
        return out

    def get_features_dataframe(self, candidate_ids: list[str]) -> pl.DataFrame:
        """Retrieve features for a list of candidate IDs as a Polars DataFrame."""
        conn = self.connect()
        ids_str = ",".join([f"'{cid}'" for cid in candidate_ids])
        if not ids_str:
            return pl.DataFrame()

        df_arrow = conn.execute(
            f"SELECT * FROM {DUCKDB_FEATURES_TABLE} WHERE candidate_id IN ({ids_str})"
        ).arrow()
        return pl.from_arrow(df_arrow)

    def get_features(self, candidate_id: str) -> CandidateFeatures | None:
        """Alias for get_candidate_features."""
        return self.get_candidate_features(candidate_id)

    def get_job_profile(self, job_id: str) -> JobProfile | None:
        """Retrieve structured JobProfile from database."""
        conn = self.connect()
        res = conn.execute(
            f"SELECT requirements FROM {DUCKDB_JOBS_TABLE} WHERE job_id = ?",
            [job_id]
        ).fetchone()
        if not res:
            return None
        return JobProfile.model_validate_json(res[0])

    def get_ranking_results(self, job_id: str) -> list[CandidateResult]:
        """Retrieve ranking results as list of CandidateResult models."""
        from shared.types.ranking import (
            CandidateExplanation,
            CandidateResult,
            ConfidenceLevel,
            HiringRecommendation,
        )

        conn = self.connect()
        res = conn.execute(
            f"SELECT candidate_id, rank, overall_score, confidence_level, hiring_recommendation, explanation, stage_scores "
            f"FROM {DUCKDB_RANKINGS_TABLE} WHERE job_id = ? ORDER BY rank ASC",
            [job_id]
        ).fetchall()

        results = []
        for row in res:
            cid = row[0]
            profile = self.get_candidate_profile(cid)
            features = self.get_candidate_features(cid)

            expl_data = json.loads(row[5]) if row[5] else {}
            explanation = CandidateExplanation.model_validate(expl_data) if expl_data else None

            stage_scores = json.loads(row[6]) if row[6] else {}

            results.append(
                CandidateResult(
                    candidate_id=cid,
                    rank=row[1],
                    overall_score=row[2],
                    confidence_level=ConfidenceLevel(row[3]),
                    hiring_recommendation=HiringRecommendation(row[4]),
                    profile=profile,
                    features=features,
                    explanation=explanation,
                    stage1_score=stage_scores.get("stage1_score", 0.0),
                    stage2_score=stage_scores.get("stage2_score", 0.0),
                    stage3_score=stage_scores.get("stage3_score", 0.0),
                )
            )
        return results

