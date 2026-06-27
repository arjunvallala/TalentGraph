"""
TalentGraph AI — Submission Generator

Formats final shortlisted candidates into the standardized submission.csv format
and performs schema and rule-based validation checks.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Tuple

from shared.constants import SUBMISSION_COLUMNS
from shared.logging_setup import get_logger
from shared.types.ranking import CandidateResult

logger = get_logger(__name__)


class SubmissionGenerator:
    """
    Creates and validates the final submission.csv file for the challenge.
    """

    def __init__(self) -> None:
        """Initialize the submission generator."""
        pass

    def generate(self, candidates: List[CandidateResult], output_path: str) -> None:
        """
        Export candidate shortlist to a CSV file.

        Args:
            candidates: Ranked list of CandidateResult items.
            output_path: Destination file path for submission.csv.
        """
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)

        try:
            with p.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow(SUBMISSION_COLUMNS)
                
                # Write rows
                for c in candidates:
                    writer.writerow([
                        c.candidate_id,
                        c.rank,
                        f"{c.overall_score:.6f}",
                        c.confidence_level.value,
                        c.hiring_recommendation.value,
                    ])
            logger.info(f"Successfully generated submission file: {output_path} ({len(candidates)} rows)")

            # Automatically generate XLSX file as well
            try:
                import pandas as pd
                xlsx_path = p.with_suffix(".xlsx")
                data = []
                for c in candidates:
                    data.append({
                        "candidate_id": c.candidate_id,
                        "rank": c.rank,
                        "overall_score": float(f"{c.overall_score:.6f}"),
                        "confidence_level": c.confidence_level.value,
                        "hiring_recommendation": c.hiring_recommendation.value,
                    })
                df = pd.DataFrame(data, columns=SUBMISSION_COLUMNS)
                df.to_excel(str(xlsx_path), index=False)
                logger.info(f"Successfully generated submission Excel file: {xlsx_path} ({len(candidates)} rows)")
            except Exception as ex:
                logger.warning(f"Could not automatically generate submission XLSX: {ex}")

        except Exception as e:
            logger.error(f"Failed to generate submission files: {e}")
            raise

    def validate(self, path: str) -> Tuple[bool, List[str]]:
        """
        Validate the generated submission CSV schema and data integrity constraints.

        Args:
            path: Path to the submission CSV file.

        Returns:
            Tuple of (is_valid boolean, list of error messages).
        """
        p = Path(path)
        if not p.exists():
            return False, ["File does not exist"]

        errors = []
        try:
            with p.open("r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                
                # 1. Header Validation
                if not header:
                    return False, ["CSV file is empty"]
                if header != SUBMISSION_COLUMNS:
                    errors.append(f"Invalid headers. Expected {SUBMISSION_COLUMNS}, got {header}")

                candidate_ids = set()
                last_rank = 0

                # 2. Row by Row Validation
                for idx, row in enumerate(reader, start=1):
                    if len(row) != len(SUBMISSION_COLUMNS):
                        errors.append(f"Row {idx}: Expected {len(SUBMISSION_COLUMNS)} values, got {len(row)}")
                        continue

                    cid, rank_str, score_str, conf, rec = row

                    # Candidate ID validation
                    if not cid:
                        errors.append(f"Row {idx}: Empty candidate ID")
                    if cid in candidate_ids:
                        errors.append(f"Row {idx}: Duplicate candidate ID '{cid}'")
                    candidate_ids.add(cid)

                    # Rank sequence validation
                    try:
                        rank = int(rank_str)
                        if rank != last_rank + 1:
                            errors.append(f"Row {idx}: Non-sequential rank. Expected {last_rank + 1}, got {rank}")
                        last_rank = rank
                    except ValueError:
                        errors.append(f"Row {idx}: Invalid rank integer '{rank_str}'")

                    # Score range validation
                    try:
                        score = float(score_str)
                        if not (0.0 <= score <= 1.0):
                            errors.append(f"Row {idx}: Score '{score}' is out of bounds [0, 1]")
                    except ValueError:
                        errors.append(f"Row {idx}: Invalid score float '{score_str}'")

                    # Enum validation
                    if conf not in ["High", "Medium", "Low"]:
                        errors.append(f"Row {idx}: Invalid confidence level '{conf}'")
                    
                    valid_recs = ["Strong Hire", "Hire", "Consider", "Pass", "Reject"]
                    if rec not in valid_recs:
                        errors.append(f"Row {idx}: Invalid hiring recommendation '{rec}'")

        except Exception as e:
            return False, [f"Failed to read file: {e}"]

        is_valid = len(errors) == 0
        return is_valid, errors
