"""
TalentGraph AI — Candidate Parser

Converts raw CSV rows (as dicts) into structured CandidateProfile instances.
Handles skill parsing, education parsing, signal extraction, and seniority inference.

Each parse_* method is independently robust — a failure in one field
does not abort the whole candidate parse.
"""

from __future__ import annotations

import json
import re
from typing import Any

from shared.logging_setup import get_logger
from shared.types.candidate import (
    AvailabilityStatus,
    CandidateProfile,
    EducationEntry,
    EducationLevel,
    RedrobSignals,
)
from services.preprocessing.career_parser import CareerParser
from shared.utils.text_utils import extract_years_of_experience

logger = get_logger(__name__)

# ── Education Level Inference ─────────────────────────────────────────────────
_EDU_LEVEL_PATTERNS: list[tuple[EducationLevel, re.Pattern]] = [
    (EducationLevel.PHD, re.compile(r"\b(ph\.?d|d\.phil|doctor(?:ate)?|phd)\b", re.IGNORECASE)),
    (
        EducationLevel.MBA,
        re.compile(r"\b(mba|master\s+of\s+business\s+administration)\b", re.IGNORECASE),
    ),
    (
        EducationLevel.MASTERS,
        re.compile(
            r"\b(m\.?s\.?|m\.?e\.?|m\.?tech|master(?:s)?|msc|m\.?a\.?|mphil)\b", re.IGNORECASE
        ),
    ),
    (
        EducationLevel.BACHELORS,
        re.compile(
            r"\b(b\.?s\.?|b\.?e\.?|b\.?tech|bachelor(?:s)?|b\.?sc|b\.?a\.?|"
            r"be|btech|bsc|ba|bs)\b",
            re.IGNORECASE,
        ),
    ),
    (
        EducationLevel.DIPLOMA,
        re.compile(r"\b(diploma|certificate|certification|associate)\b", re.IGNORECASE),
    ),
    (
        EducationLevel.HIGH_SCHOOL,
        re.compile(
            r"\b(high\s+school|12th|10\+2|hsc|ssc|secondary|matriculation|"
            r"ged|a\s+level|o\s+level)\b",
            re.IGNORECASE,
        ),
    ),
]

# ── Common degree field keywords → field_of_study ────────────────────────────
_FIELD_KEYWORDS: dict[str, list[str]] = {
    "computer science": ["computer science", "cs", "cse", "computing"],
    "software engineering": ["software engineering", "software", "se"],
    "information technology": ["information technology", "it", "information systems"],
    "electronics": ["electronics", "ece", "electrical", "eee", "vlsi"],
    "mechanical engineering": ["mechanical", "me", "mech"],
    "civil engineering": ["civil", "ce"],
    "mathematics": ["mathematics", "math", "maths", "applied math", "statistics"],
    "data science": ["data science", "machine learning", "ai", "analytics"],
    "business": ["business", "commerce", "management", "mba", "finance", "economics"],
    "physics": ["physics"],
    "chemistry": ["chemistry"],
    "biology": ["biology", "bioinformatics", "biotech"],
}


def _infer_field_of_study(text: str) -> str | None:
    """Infer field of study from free-form text."""
    text_lower = text.lower()
    for field, keywords in _FIELD_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return field
    return None


class CandidateParser:
    """
    Converts raw CSV row dicts into structured CandidateProfile instances.

    Tolerates malformed or missing fields gracefully. Invalid values
    are replaced with safe defaults rather than raising exceptions.

    Example:
        parser = CandidateParser()
        profile = parser.parse_row(row_dict)
    """

    def __init__(self) -> None:
        """Initialise the parser."""
        logger.debug("CandidateParser initialised")

    def parse_row(self, row: dict[str, Any]) -> CandidateProfile:
        """
        Parse a single raw CSV row dictionary into a CandidateProfile.

        Args:
            row: Dictionary representing one CSV row.

        Returns:
            Structured CandidateProfile instance.

        Raises:
            ValueError: If candidate_id is missing from the row.
        """
        candidate_id = str(row.get("candidate_id", "")).strip()
        if not candidate_id:
            raise ValueError("candidate_id is required and cannot be empty")

        # Parse experience: use explicit column or extract from text
        years_exp = 0.0
        raw_exp = row.get("years_of_experience", 0)
        try:
            years_exp = float(raw_exp) if raw_exp is not None else 0.0
        except (TypeError, ValueError):
            # Try to extract from summary or other text
            text_sources = [
                str(row.get("summary", "")),
                str(row.get("current_title", "")),
            ]
            for src in text_sources:
                extracted = extract_years_of_experience(src)
                if extracted > 0:
                    years_exp = extracted
                    break

        years_exp = max(0.0, min(float(years_exp), 50.0))

        # Parse skills
        skills = self.parse_skills(str(row.get("skills", "") or ""))

        # Parse education
        education = self.parse_education(str(row.get("education", "") or ""))

        # Parse Redrob signals
        redrob_signals = self._parse_redrob_signals(row)

        # Build certifications list
        certs_raw = row.get("certifications", "") or ""
        certifications = self._parse_comma_list(str(certs_raw))

        # Build languages list
        langs_raw = row.get("languages", "") or ""
        languages = self._parse_comma_list(str(langs_raw))

        profile = CandidateProfile(
            candidate_id=candidate_id,
            name=self._safe_str(row.get("name")),
            email=self._safe_str(row.get("email")),
            phone=self._safe_str(row.get("phone")),
            location=self._safe_str(row.get("location")),
            current_title=self._safe_str(row.get("current_title")),
            current_company=self._safe_str(row.get("current_company")),
            years_of_experience=years_exp,
            skills=skills,
            education=education,
            work_experience=CareerParser().parse_work_history(row.get("work_history", row.get("work_experience", ""))),
            certifications=certifications,
            languages=languages,
            summary=self._safe_str(row.get("summary")),
            redrob_signals=redrob_signals,
            raw_data=dict(row),
        )

        return profile

    def parse_skills(self, skills_str: str) -> list[str]:
        """
        Parse a comma-separated skills string into a clean list.

        Handles multiple delimiters: comma, semicolon, pipe, newline.

        Args:
            skills_str: Raw skills string from CSV.

        Returns:
            Normalised, deduplicated list of skill strings.
        """
        if not skills_str or not isinstance(skills_str, str):
            return []

        # Split on multiple delimiters
        parts = re.split(r"[,;|\n\r]+", skills_str)
        result: list[str] = []
        seen: set[str] = set()

        for part in parts:
            clean = part.strip().lower()
            clean = re.sub(r"\s+", " ", clean)
            if clean and len(clean) >= 1 and clean not in seen:
                result.append(clean)
                seen.add(clean)

        return result[:100]

    def parse_education(self, education_str: str) -> list[EducationEntry]:
        """
        Parse free-form education text into structured EducationEntry objects.

        Handles:
        - JSON arrays of objects
        - Semicolon-separated strings
        - Free-form text (single education entry)

        Args:
            education_str: Raw education string from CSV.

        Returns:
            List of EducationEntry objects. Empty list if parsing fails.
        """
        if not education_str or education_str.strip() in ("", "[]", "{}"):
            return []

        # Try JSON parsing first
        try:
            parsed = json.loads(education_str)
            if isinstance(parsed, list):
                entries = []
                for item in parsed:
                    if isinstance(item, dict):
                        entry = self._parse_education_dict(item)
                        if entry:
                            entries.append(entry)
                return entries
            elif isinstance(parsed, dict):
                entry = self._parse_education_dict(parsed)
                return [entry] if entry else []
        except (json.JSONDecodeError, ValueError):
            pass

        # Try semicolon-separated
        parts = [p.strip() for p in education_str.split(";") if p.strip()]
        entries = []
        for part in parts:
            level = self.infer_education_level(part)
            field = _infer_field_of_study(part)
            entry = EducationEntry(
                institution="",
                degree=part[:100],
                field_of_study=field,
                level=level,
            )
            entries.append(entry)

        if not entries and education_str.strip():
            level = self.infer_education_level(education_str)
            field = _infer_field_of_study(education_str)
            entries.append(
                EducationEntry(
                    institution="",
                    degree=education_str[:100],
                    field_of_study=field,
                    level=level,
                )
            )

        return entries

    def infer_education_level(self, degree: str) -> EducationLevel:
        """
        Infer the EducationLevel enum value from a degree string.

        Args:
            degree: Degree or qualification text.

        Returns:
            Best-matching EducationLevel enum value.
            Defaults to EducationLevel.UNKNOWN.
        """
        if not degree or not isinstance(degree, str):
            return EducationLevel.UNKNOWN

        for level, pattern in _EDU_LEVEL_PATTERNS:
            if pattern.search(degree):
                return level

        return EducationLevel.UNKNOWN

    def _parse_education_dict(self, data: dict) -> EducationEntry | None:
        """Parse a single education dict into an EducationEntry."""
        try:
            degree = str(data.get("degree", data.get("qualification", ""))).strip()
            institution = str(
                data.get("institution", data.get("school", data.get("university", "")))
            ).strip()
            field = (
                str(data.get("field_of_study", data.get("major", data.get("stream", "")))).strip()
                or None
            )

            if not degree and not institution:
                return None

            level = self.infer_education_level(f"{degree} {field or ''}")
            if level == EducationLevel.UNKNOWN and field:
                level = self.infer_education_level(field)

            start_year = None
            end_year = None
            try:
                if "start_year" in data:
                    start_year = int(data["start_year"])
                elif "from" in data:
                    start_year = int(str(data["from"])[:4])
            except (ValueError, TypeError):
                pass
            try:
                if "end_year" in data:
                    end_year = int(data["end_year"])
                elif "to" in data and str(data["to"]).lower() not in ("present", "current", ""):
                    end_year = int(str(data["to"])[:4])
            except (ValueError, TypeError):
                pass

            gpa = None
            try:
                if "gpa" in data:
                    gpa = float(data["gpa"])
            except (ValueError, TypeError):
                pass

            return EducationEntry(
                institution=institution,
                degree=degree,
                field_of_study=field or _infer_field_of_study(f"{degree} {institution}"),
                level=level,
                start_year=start_year,
                end_year=end_year,
                gpa=gpa,
                is_current=end_year is None and start_year is not None,
            )
        except Exception as exc:
            logger.debug("Education dict parse error: %s — %s", data, exc)
            return None

    def _parse_redrob_signals(self, row: dict[str, Any]) -> RedrobSignals:
        """Extract and validate RedrobSignals from a raw row dict."""

        def safe_int(val: Any, default: int = 0) -> int:
            try:
                return int(float(str(val))) if val is not None else default
            except (ValueError, TypeError):
                return default

        def safe_float(val: Any, default: float = 0.0) -> float:
            try:
                return float(str(val)) if val is not None else default
            except (ValueError, TypeError):
                return default

        def safe_bool(val: Any, default: bool = False) -> bool:
            if val is None:
                return default
            if isinstance(val, bool):
                return val
            return str(val).lower() in ("true", "1", "yes", "y")

        profile_views = safe_int(row.get("profile_views"), 0)
        application_count = safe_int(row.get("application_count"), 0)
        response_rate = min(1.0, max(0.0, safe_float(row.get("response_rate"), 0.0)))
        last_active_days_raw = row.get("last_active_days")
        last_active_days = (
            safe_int(last_active_days_raw) if last_active_days_raw is not None else None
        )
        notice_period_raw = row.get("notice_period_days")
        notice_period_days = safe_int(notice_period_raw) if notice_period_raw is not None else None
        if notice_period_days is not None:
            notice_period_days = min(365, max(0, notice_period_days))
        expected_salary_raw = row.get("expected_salary")
        expected_salary = (
            safe_float(expected_salary_raw) if expected_salary_raw is not None else None
        )
        open_to_remote = safe_bool(row.get("open_to_remote"), False)

        # Parse availability status
        raw_status = str(row.get("availability_status", "unknown") or "unknown").lower().strip()
        availability_map = {
            "immediately_available": AvailabilityStatus.IMMEDIATELY_AVAILABLE,
            "immediately available": AvailabilityStatus.IMMEDIATELY_AVAILABLE,
            "notice_period": AvailabilityStatus.NOTICE_PERIOD,
            "notice period": AvailabilityStatus.NOTICE_PERIOD,
            "not_looking": AvailabilityStatus.NOT_LOOKING,
            "not looking": AvailabilityStatus.NOT_LOOKING,
            "open_to_opportunities": AvailabilityStatus.OPEN_TO_OPPORTUNITIES,
            "open to opportunities": AvailabilityStatus.OPEN_TO_OPPORTUNITIES,
            "open": AvailabilityStatus.OPEN_TO_OPPORTUNITIES,
            "active": AvailabilityStatus.IMMEDIATELY_AVAILABLE,
        }
        availability = availability_map.get(raw_status, AvailabilityStatus.UNKNOWN)

        return RedrobSignals(
            profile_views=max(0, profile_views),
            application_count=max(0, application_count),
            response_rate=response_rate,
            last_active_days=last_active_days,
            availability_status=availability,
            notice_period_days=notice_period_days,
            expected_salary=expected_salary,
            open_to_remote=open_to_remote,
        )

    def _parse_comma_list(self, raw: str) -> list[str]:
        """Parse a comma-separated string into a deduplicated list."""
        if not raw or not raw.strip():
            return []
        parts = re.split(r"[,;|\n\r]+", raw)
        result = []
        seen: set[str] = set()
        for p in parts:
            clean = p.strip()
            if clean and clean.lower() not in seen:
                result.append(clean)
                seen.add(clean.lower())
        return result

    def _safe_str(self, val: Any) -> str | None:
        """Safely convert a value to string, returning None for empty."""
        if val is None:
            return None
        s = str(val).strip()
        return s if s else None
