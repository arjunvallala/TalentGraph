"""
TalentGraph AI — Base Council Evaluator

Defines the abstract base class for all council members.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from shared.types.candidate import CandidateGenome
from shared.types.council import CouncilType, CouncilVote
from shared.types.job import JobGenome


class BaseCouncil(ABC):
    """
    Abstract base class for all 5 independent council evaluators.
    """

    def __init__(self, council_type: CouncilType) -> None:
        """Initialize the council evaluator."""
        self.council_type = council_type

    @abstractmethod
    def evaluate(self, candidate: CandidateGenome, job: JobGenome) -> CouncilVote:
        """
        Evaluate a candidate genome against job genome requirements.

        Args:
            candidate: Candidate capabilites and features genome.
            job: Job description genome targets and weights.

        Returns:
            An independent CouncilVote containing scores, strengths, and rationales.
        """
        pass
