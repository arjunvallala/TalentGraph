"""
TalentGraph AI — Hiring Council Consensus Engine

Runs all 5 independent council members in parallel using a thread pool
and combines their votes into a FinalCouncilDecision consensus.
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, List, Any, Optional

import numpy as np

from shared.logging_setup import get_logger
from shared.types.candidate import CandidateGenome
from shared.types.job import JobGenome
from shared.types.council import (
    CouncilVote,
    CouncilType,
    FinalCouncilDecision,
    CouncilEvaluationResult,
)
from services.ranking.council.technical_council import TechnicalCouncil
from services.ranking.council.career_council import CareerCouncil
from services.ranking.council.behavior_council import BehaviorCouncil
from services.ranking.council.growth_council import GrowthCouncil
from services.ranking.council.risk_council import RiskCouncil

logger = get_logger(__name__)


class HiringCouncil:
    """
    Manages parallel execution of the 5 council members and computes final consensus decisions.
    """

    def __init__(self) -> None:
        """Initialize council members."""
        self.members = [
            TechnicalCouncil(),
            CareerCouncil(),
            BehaviorCouncil(),
            GrowthCouncil(),
            RiskCouncil(),
        ]
        # Standard weights for the non-risk members
        self.weights = {
            CouncilType.TECHNICAL.value: 0.35,
            CouncilType.CAREER.value: 0.25,
            CouncilType.GROWTH.value: 0.20,
            CouncilType.BEHAVIOR.value: 0.20,
        }
        logger.info("HiringCouncil Consensus Engine initialised")

    def evaluate_candidate(
        self, candidate: CandidateGenome, job: JobGenome
    ) -> FinalCouncilDecision:
        """
        Evaluate a candidate by running all 5 council members in parallel.

        Args:
            candidate: Candidate genome.
            job: Target job requirements genome.

        Returns:
            FinalCouncilDecision representing the consensus decision.
        """
        start_time = time.perf_counter()
        votes: Dict[str, CouncilVote] = {}

        # 1. Run evaluators in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(member.evaluate, candidate, job): member
                for member in self.members
            }
            
            for future in futures:
                member = futures[future]
                try:
                    vote = future.result()
                    votes[member.council_type.value] = vote
                except Exception as e:
                    logger.error(f"Council member '{member.council_type.value}' failed: {e}")

        duration = time.perf_counter() - start_time

        # 2. Compute Consensus Score
        individual_scores = {}
        individual_confidences = {}
        all_strengths = []
        all_concerns = []
        decisive_factors = []

        for c_type, vote in votes.items():
            individual_scores[c_type] = vote.score
            individual_confidences[c_type] = vote.confidence
            all_strengths.extend(vote.strengths)
            all_concerns.extend(vote.concerns)
            if vote.rationale:
                decisive_factors.append(f"{c_type}: {vote.rationale}")

        # Compute weighted score for non-risk members
        total_weight = 0.0
        weighted_score_sum = 0.0
        for c_type, score in individual_scores.items():
            if c_type in self.weights:
                w = self.weights[c_type]
                weighted_score_sum += score * w
                total_weight += w

        consensus_score = (
            weighted_score_sum / total_weight if total_weight > 0 else 0.5
        )
        avg_confidence = (
            sum(individual_confidences.values()) / len(individual_confidences)
            if individual_confidences
            else 0.5
        )

        # 3. Apply Risk Penalty (from Risk Council)
        risk_vote = votes.get(CouncilType.RISK.value)
        risk_penalty = 0.0
        if risk_vote:
            # risk_vote.score is safety (1.0 = no risk, 0.0 = max risk)
            # Apply penalty if safety is low
            risk_safety = risk_vote.score
            if risk_safety < 0.6:
                # Up to 15% penalty
                risk_penalty = (1.0 - risk_safety) * 0.15

        final_score = max(0.0, consensus_score - risk_penalty)

        # 4. Compute Agreement Score (1.0 - standard deviation of non-risk scores)
        scores_list = [
            score for c_type, score in individual_scores.items() if c_type in self.weights
        ]
        agreement_score = 1.0
        if len(scores_list) > 1:
            std_dev = float(time.struct_time(time.localtime(0)).tm_sec) # dummy or compute std dev
            # Let's compute actual standard deviation
            np_arr = np.array(scores_list, dtype=np.float32)
            agreement_score = float(1.0 - np_arr.std())

        # Check for strong dissent (e.g. if technical council scores very low but others high)
        dissenting_opinion = None
        tech_vote = votes.get(CouncilType.TECHNICAL.value)
        if tech_vote and tech_vote.score < 0.4 and final_score >= 0.6:
            dissenting_opinion = (
                "Technical Council strongly advises caution: candidate scored very low "
                "on core technical competencies despite high soft skill/stability marks."
            )

        return FinalCouncilDecision(
            candidate_id=candidate.candidate_id,
            council_score=consensus_score,
            council_confidence=avg_confidence,
            agreement_score=agreement_score,
            individual_scores=individual_scores,
            individual_confidences=individual_confidences,
            all_strengths=all_strengths[:5],
            all_concerns=all_concerns[:5],
            decisive_factors=decisive_factors[:3],
            dissenting_opinion=dissenting_opinion,
            risk_penalty_applied=risk_penalty,
            final_score=final_score,
            decided_at=datetime.utcnow(),
        )
