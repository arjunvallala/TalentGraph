"""
TalentGraph AI — System-wide Constants

Centralises every magic number and string used across the codebase.
Nothing should be hardcoded in service files; reference these constants instead.
"""

from __future__ import annotations

# ── Application ───────────────────────────────────────────────────────────────
APP_NAME = "TalentGraph AI"
APP_VERSION = "0.1.0"
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# ── Embedding ─────────────────────────────────────────────────────────────────
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384
MAX_EMBEDDING_SEQ_LENGTH = 256
EMBEDDING_BATCH_SIZE = 64

# ── Ranking Pipeline ─────────────────────────────────────────────────────────
STAGE1_TOP_K = 2000  # Hybrid retrieval output
STAGE2_TOP_K = 200  # Feature ranking output
STAGE3_TOP_K = 100  # Hiring Council output
FINAL_TOP_K = 100  # Submission size

SEMANTIC_TOP_K = 1500  # FAISS retrieval
BM25_TOP_K = 1500  # BM25 retrieval
RRF_K = 60  # Reciprocal Rank Fusion constant

# ── Confidence Thresholds ────────────────────────────────────────────────────
CONFIDENCE_HIGH = 0.75
CONFIDENCE_MEDIUM = 0.45
# below CONFIDENCE_MEDIUM = LOW

# ── Feature Engineering ───────────────────────────────────────────────────────
MAX_EXPERIENCE_YEARS = 30.0
MIN_TENURE_MONTHS_STABLE = 12  # below = job hopping
CAREER_GAP_THRESHOLD_MONTHS = 6  # above = notable gap
EPSILON = 1e-8  # prevent division by zero

# ── Profile Completeness Fields ───────────────────────────────────────────────
REQUIRED_PROFILE_FIELDS = [
    "name",
    "current_title",
    "work_experience",
    "skills",
    "education",
    "summary",
]
OPTIONAL_PROFILE_FIELDS = [
    "email",
    "phone",
    "location",
    "certifications",
    "languages",
    "redrob_signals",
]

# ── Seniority Mappings ────────────────────────────────────────────────────────
SENIORITY_KEYWORDS: dict[str, list[str]] = {
    "executive": [
        "CEO",
        "CTO",
        "CIO",
        "CFO",
        "COO",
        "CISO",
        "CPO",
        "President",
        "EVP",
        "SVP",
        "C-Suite",
    ],
    "principal": [
        "Principal",
        "Distinguished",
        "Fellow",
        "Staff",
        "VP",
        "Vice President",
        "Director",
    ],
    "senior": ["Senior", "Sr.", "Lead", "Architect", "Head of", "Manager"],
    "mid": ["Engineer", "Developer", "Analyst", "Specialist", "Consultant"],
    "junior": ["Junior", "Jr.", "Associate"],
    "entry": ["Intern", "Trainee", "Graduate", "Fresher", "Entry Level"],
}

# ── Leadership Keywords ───────────────────────────────────────────────────────
LEADERSHIP_STRONG_KEYWORDS = [
    "managed",
    "led",
    "directed",
    "headed",
    "supervised",
    "mentored",
    "built team",
    "hired",
    "reporting to me",
    "team of",
    "team size",
]
LEADERSHIP_MODERATE_KEYWORDS = [
    "collaborated",
    "coordinated",
    "guided",
    "facilitated",
    "cross-functional",
    "stakeholder",
]

# ── Research Keywords ─────────────────────────────────────────────────────────
RESEARCH_KEYWORDS = [
    "published",
    "paper",
    "research",
    "journal",
    "conference",
    "IEEE",
    "ACM",
    "arxiv",
    "patent",
    "patented",
    "inventor",
    "github.com",
    "open source",
    "contributor",
    "maintainer",
]

# ── Hiring Recommendation Labels ─────────────────────────────────────────────
RECOMMENDATION_STRONG_HIRE = "Strong Hire"
RECOMMENDATION_HIRE = "Hire"
RECOMMENDATION_CONSIDER = "Consider"
RECOMMENDATION_PASS = "Pass"
RECOMMENDATION_REJECT = "Reject"

RECOMMENDATION_THRESHOLDS = {
    RECOMMENDATION_STRONG_HIRE: 0.82,
    RECOMMENDATION_HIRE: 0.68,
    RECOMMENDATION_CONSIDER: 0.52,
    RECOMMENDATION_PASS: 0.38,
    # below 0.38 = REJECT
}

# ── Risk Levels ───────────────────────────────────────────────────────────────
RISK_CRITICAL = "Critical"
RISK_HIGH = "High"
RISK_MEDIUM = "Medium"
RISK_LOW = "Low"
RISK_MINIMAL = "Minimal"

RISK_THRESHOLDS = {
    RISK_CRITICAL: 0.80,
    RISK_HIGH: 0.60,
    RISK_MEDIUM: 0.40,
    RISK_LOW: 0.20,
    # below 0.20 = MINIMAL
}

# ── Score Band Labels ─────────────────────────────────────────────────────────
SCORE_BAND_EXCEPTIONAL = "Exceptional Match"
SCORE_BAND_STRONG = "Strong Match"
SCORE_BAND_GOOD = "Good Match"
SCORE_BAND_FAIR = "Potential Match"
SCORE_BAND_WEAK = "Weak Match"

SCORE_BANDS = [
    (0.85, SCORE_BAND_EXCEPTIONAL),
    (0.70, SCORE_BAND_STRONG),
    (0.55, SCORE_BAND_GOOD),
    (0.40, SCORE_BAND_FAIR),
    (0.00, SCORE_BAND_WEAK),
]

# ── File Paths ────────────────────────────────────────────────────────────────
SUBMISSION_FILENAME = "submission.csv"
SUBMISSION_COLUMNS = [
    "candidate_id",
    "rank",
    "overall_score",
    "confidence_level",
    "hiring_recommendation",
]

# ── DuckDB ────────────────────────────────────────────────────────────────────
DUCKDB_CANDIDATE_TABLE = "candidates"
DUCKDB_FEATURES_TABLE = "candidate_features"
DUCKDB_EVIDENCE_TABLE = "candidate_evidence"
DUCKDB_JOBS_TABLE = "jobs"
DUCKDB_RANKINGS_TABLE = "rankings"
DUCKDB_CONFIG_TABLE = "pipeline_config"

# ── Preprocessing ─────────────────────────────────────────────────────────────
CHECKPOINT_EXTENSION = ".ckpt.json"
DEFAULT_BATCH_SIZE = 1000
MAX_SKILLS_PER_CANDIDATE = 100

# ── HTTP ──────────────────────────────────────────────────────────────────────
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_400_BAD_REQUEST = 400
HTTP_404_NOT_FOUND = 404
HTTP_422_UNPROCESSABLE = 422
HTTP_500_INTERNAL_ERROR = 500
