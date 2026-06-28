"""
TalentGraph AI — Career History Parser

Parses work history from raw JSON/text strings into structured
WorkExperience objects, and computes career analytics:
tenure, gaps, promotions, career age, and average tenure.

All date parsing handles multiple formats gracefully.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from typing import Any

from shared.logging_setup import get_logger
from shared.types.candidate import WorkExperience

logger = get_logger(__name__)

# Date formats to attempt for parsing
_DATE_FORMATS: list[str] = [
    "%Y-%m-%d",
    "%Y-%m",
    "%m/%Y",
    "%m-%Y",
    "%b %Y",
    "%B %Y",
    "%Y",
    "%d/%m/%Y",
    "%d-%m-%Y",
]

# Keywords indicating a current role
_CURRENT_KEYWORDS: set[str] = {
    "present",
    "current",
    "now",
    "ongoing",
    "till date",
    "till now",
    "to date",
    "today",
    "currently",
    "—",
    "-",
}

# Promotion indicators: lower title → higher title
_SENIORITY_ORDER: dict[str, int] = {
    "intern": 0,
    "trainee": 0,
    "fresher": 0,
    "junior": 1,
    "jr": 1,
    "associate": 1,
    "engineer": 2,
    "developer": 2,
    "analyst": 2,
    "consultant": 2,
    "specialist": 2,
    "programmer": 2,
    "senior": 3,
    "sr": 3,
    "lead": 3,
    "staff": 4,
    "principal": 4,
    "architect": 5,
    "manager": 5,
    "head": 5,
    "director": 6,
    "vp": 7,
    "vice president": 7,
    "cto": 8,
    "ceo": 8,
    "coo": 8,
    "chief": 8,
    "president": 8,
}


def _parse_date(date_str: str) -> date | None:
    """
    Attempt to parse a date string using multiple format patterns.

    Args:
        date_str: Raw date string.

    Returns:
        Parsed date object, or None if all formats fail.
    """
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()

    if date_str.lower() in _CURRENT_KEYWORDS:
        return None

    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    # Try extracting year only
    year_match = re.search(r"\b(19|20)\d{2}\b", date_str)
    if year_match:
        try:
            return date(int(year_match.group(0)), 1, 1)
        except ValueError:
            pass

    return None


def _get_seniority_score(title: str) -> int:
    """Get a seniority score for a job title (higher = more senior)."""
    title_lower = title.lower()
    max_score = 2  # default for unknown titles
    for keyword, score in _SENIORITY_ORDER.items():
        if keyword in title_lower:
            max_score = max(max_score, score)
    return max_score


class CareerParser:
    """
    Parses raw work history data into structured WorkExperience lists
    and computes career analytics.

    Handles multiple input formats:
    - JSON array of objects
    - JSON string
    - Semicolon-separated plain text entries

    Example:
        parser = CareerParser()
        experiences = parser.parse_work_history(row["work_history"])
        gaps = parser.find_career_gaps(experiences)
    """

    def __init__(self) -> None:
        """Initialise the career parser."""
        logger.debug("CareerParser initialised")

    def parse_work_history(self, raw: str | list) -> list[WorkExperience]:
        """
        Parse raw work history data into a list of WorkExperience objects.

        Handles JSON arrays, JSON strings, and plain text.
        Sorts results newest-first.

        Args:
            raw: Raw work history as string or list.

        Returns:
            List of WorkExperience objects, sorted newest-first.
        """
        if raw is None or raw == "":
            return []

        experiences: list[WorkExperience] = []

        # If already a list, process directly
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict):
                    exp = self._parse_experience_dict(item)
                    if exp:
                        experiences.append(exp)
            return self._sort_experiences(experiences)

        # Try JSON parsing
        raw_str = str(raw).strip()
        if raw_str in ("", "[]", "null", "None"):
            return []

        try:
            parsed = json.loads(raw_str)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        exp = self._parse_experience_dict(item)
                        if exp:
                            experiences.append(exp)
                return self._sort_experiences(experiences)
            elif isinstance(parsed, dict):
                exp = self._parse_experience_dict(parsed)
                return [exp] if exp else []
        except (json.JSONDecodeError, ValueError):
            pass

        # Try semicolon-separated plain text
        parts = [p.strip() for p in raw_str.split(";") if p.strip()]
        for part in parts:
            exp = self._parse_text_experience(part)
            if exp:
                experiences.append(exp)

        return self._sort_experiences(experiences)

    def compute_tenure_months(self, start: str, end: str) -> int:
        """
        Compute the number of months between start and end dates.

        Args:
            start: Start date string.
            end: End date string. Pass "present" or empty for current roles.

        Returns:
            Tenure in months. Returns 0 if dates cannot be parsed.
        """
        start_date = _parse_date(start)
        if start_date is None:
            return 0

        if not end or end.lower().strip() in _CURRENT_KEYWORDS:
            end_date = date.today()
        else:
            end_date = _parse_date(end)
            if end_date is None:
                end_date = date.today()

        if end_date < start_date:
            return 0

        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        return max(0, min(months, 600))

    def is_current_role(self, end_date: str) -> bool:
        """
        Determine if an end_date string indicates a current role.

        Args:
            end_date: End date string (may be "Present", empty, or a date).

        Returns:
            True if this is the current role.
        """
        if not end_date:
            return True
        return str(end_date).lower().strip() in _CURRENT_KEYWORDS

    def detect_promotions(self, experiences: list[WorkExperience]) -> int:
        """
        Count the number of clear promotions in the career history.

        A promotion is detected when consecutive roles at the same company
        show increasing seniority scores.

        Args:
            experiences: List of WorkExperience objects (newest-first).

        Returns:
            Integer count of detected promotions.
        """
        if len(experiences) < 2:
            return 0

        # Sort oldest-first for promotion detection
        sorted_exp = sorted(experiences, key=lambda e: _parse_date(e.start_date or "") or date.min)

        promotions = 0
        for i in range(1, len(sorted_exp)):
            prev = sorted_exp[i - 1]
            curr = sorted_exp[i]
            # Same company promotion
            if (
                prev.company
                and curr.company
                and prev.company.lower().strip() == curr.company.lower().strip()
            ):
                prev_score = _get_seniority_score(prev.title or "")
                curr_score = _get_seniority_score(curr.title or "")
                if curr_score > prev_score:
                    promotions += 1

        return promotions

    def find_career_gaps(self, experiences: list[WorkExperience]) -> list[tuple[str, str, int]]:
        """
        Find significant employment gaps between consecutive roles.

        Args:
            experiences: List of WorkExperience objects.

        Returns:
            List of (gap_start, gap_end, gap_months) tuples for gaps
            exceeding 3 months, sorted by size descending.
        """
        if len(experiences) < 2:
            return []

        # Sort oldest-first
        sorted_exp = sorted(
            [e for e in experiences if e.start_date],
            key=lambda e: _parse_date(e.start_date or "") or date.min,
        )

        gaps: list[tuple[str, str, int]] = []
        for i in range(1, len(sorted_exp)):
            prev = sorted_exp[i - 1]
            curr = sorted_exp[i]

            prev_end_str = prev.end_date or ""
            if self.is_current_role(prev_end_str):
                continue

            prev_end = _parse_date(prev_end_str)
            curr_start = _parse_date(curr.start_date or "")

            if prev_end and curr_start and curr_start > prev_end:
                gap_months = (curr_start.year - prev_end.year) * 12 + (
                    curr_start.month - prev_end.month
                )
                if gap_months >= 3:  # Only report gaps ≥ 3 months
                    gaps.append(
                        (
                            prev_end.isoformat(),
                            curr_start.isoformat(),
                            gap_months,
                        )
                    )

        return sorted(gaps, key=lambda g: g[2], reverse=True)

    def compute_career_age_months(self, experiences: list[WorkExperience]) -> int:
        """
        Compute total career age in months from first role to now.

        Args:
            experiences: List of WorkExperience objects.

        Returns:
            Career age in months. Returns 0 if no experiences.
        """
        if not experiences:
            return 0

        start_dates = [_parse_date(e.start_date or "") for e in experiences if e.start_date]
        start_dates = [d for d in start_dates if d is not None]

        if not start_dates:
            return 0

        earliest = min(start_dates)
        today = date.today()
        months = (today.year - earliest.year) * 12 + (today.month - earliest.month)
        return max(0, months)

    def compute_avg_tenure(self, experiences: list[WorkExperience]) -> float:
        """
        Compute the average tenure in months across all experiences.

        Args:
            experiences: List of WorkExperience objects.

        Returns:
            Average tenure in months as float. Returns 0.0 if no experiences.
        """
        if not experiences:
            return 0.0

        tenures = [
            e.duration_months
            for e in experiences
            if e.duration_months is not None and e.duration_months > 0
        ]

        if not tenures:
            return 0.0

        return sum(tenures) / len(tenures)

    def _parse_experience_dict(self, data: dict[str, Any]) -> WorkExperience | None:
        """Parse a single work experience dict."""
        try:
            company = str(
                data.get("company", data.get("employer", data.get("organization", "")))
            ).strip()
            title = str(
                data.get(
                    "title", data.get("position", data.get("designation", data.get("role", "")))
                ).strip()
                if data.get("title")
                or data.get("position")
                or data.get("designation")
                or data.get("role")
                else ""
            )
            start_date = str(
                data.get("start_date", data.get("start", data.get("from", "")))
            ).strip()
            end_date_raw = data.get("end_date", data.get("end", data.get("to", "")))
            end_date = str(end_date_raw).strip() if end_date_raw is not None else ""

            is_current = self.is_current_role(end_date)
            duration = self.compute_tenure_months(start_date, end_date)

            description = str(
                data.get("description", data.get("responsibilities", data.get("summary", "")))
            ).strip()
            description = (
                description
                if description and description.lower() not in ("none", "null", "")
                else None
            )

            # Parse skills_used from the experience
            skills_raw = data.get("skills", data.get("skills_used", data.get("technologies", [])))
            if isinstance(skills_raw, str):
                skills_used = [
                    s.strip().lower() for s in re.split(r"[,;|]+", skills_raw) if s.strip()
                ]
            elif isinstance(skills_raw, list):
                skills_used = [str(s).strip().lower() for s in skills_raw if s]
            else:
                skills_used = []

            location = str(data.get("location", "")).strip() or None
            industry = str(data.get("industry", "")).strip() or None
            company_size = str(data.get("company_size", data.get("size", ""))).strip() or None

            return WorkExperience(
                company=company,
                title=title,
                start_date=start_date or None,
                end_date=end_date if not is_current else None,
                is_current=is_current,
                duration_months=duration if duration > 0 else None,
                description=description,
                skills_used=skills_used[:20],
                location=location,
                company_size=company_size,
                industry=industry,
            )
        except Exception as exc:
            logger.debug("Experience dict parse error: %s — %s", data, exc)
            return None

    def _parse_text_experience(self, text: str) -> WorkExperience | None:
        """Parse a plain-text experience description (best-effort)."""
        if not text or len(text.strip()) < 3:
            return None

        # Try to extract year range: "Google, Engineer (2018-2021)"
        year_range = re.search(r"\((\d{4})\s*[-–]\s*(\d{4}|present|current)\)", text, re.IGNORECASE)
        start_date = None
        end_date = None
        duration = None

        if year_range:
            start_date = year_range.group(1)
            end_raw = year_range.group(2)
            is_current = end_raw.lower() in _CURRENT_KEYWORDS
            end_date = None if is_current else end_raw
            duration = self.compute_tenure_months(start_date, end_date or "present")

        return WorkExperience(
            company="",
            title="",
            start_date=start_date,
            end_date=end_date,
            is_current=(end_date is None and start_date is not None),
            duration_months=duration,
            description=text[:500],
        )

    def _sort_experiences(self, experiences: list[WorkExperience]) -> list[WorkExperience]:
        """Sort experiences newest-first by start_date."""

        def sort_key(e: WorkExperience) -> date:
            if e.is_current:
                return date.today()
            d = _parse_date(e.start_date or "")
            return d if d else date.min

        return sorted(experiences, key=sort_key, reverse=True)
