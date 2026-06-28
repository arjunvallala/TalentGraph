"""
TalentGraph AI — Text Utilities

Provides all text processing functions used across the pipeline:
normalisation, skill extraction, experience parsing, BM25 tokenisation,
candidate text building, and seniority detection.

All functions are deterministic and do not rely on any LLM or random component.
"""

from __future__ import annotations

import re

from shared.logging_setup import get_logger

logger = get_logger(__name__)

# ── Skill extraction uses a large canonical skill list ────────────────────────
# 250+ skills across ML, Software, Data, Cloud, Business domains
CANONICAL_SKILLS: list[str] = [
    # Programming Languages
    "python",
    "java",
    "javascript",
    "typescript",
    "c++",
    "c#",
    "c",
    "go",
    "golang",
    "rust",
    "swift",
    "kotlin",
    "scala",
    "ruby",
    "php",
    "r",
    "matlab",
    "julia",
    "perl",
    "lua",
    "haskell",
    "erlang",
    "elixir",
    "clojure",
    "dart",
    "groovy",
    "fortran",
    "cobol",
    "assembly",
    "vba",
    "bash",
    "powershell",
    "shell script",
    # Web Frameworks
    "react",
    "angular",
    "vue",
    "next.js",
    "nuxt.js",
    "svelte",
    "ember",
    "backbone",
    "django",
    "flask",
    "fastapi",
    "spring",
    "spring boot",
    "express",
    "nest.js",
    "rails",
    "laravel",
    "asp.net",
    "blazor",
    "htmx",
    "tailwind",
    "bootstrap",
    # Data & ML Frameworks
    "tensorflow",
    "pytorch",
    "keras",
    "scikit-learn",
    "xgboost",
    "lightgbm",
    "catboost",
    "hugging face",
    "transformers",
    "langchain",
    "llama",
    "openai",
    "anthropic",
    "pandas",
    "numpy",
    "scipy",
    "matplotlib",
    "seaborn",
    "plotly",
    "polars",
    "dask",
    "ray",
    "spark",
    "pyspark",
    "hadoop",
    "hive",
    "flink",
    # Databases
    "postgresql",
    "mysql",
    "sqlite",
    "oracle",
    "sql server",
    "mongodb",
    "redis",
    "elasticsearch",
    "cassandra",
    "dynamodb",
    "neo4j",
    "influxdb",
    "clickhouse",
    "snowflake",
    "bigquery",
    "redshift",
    "databricks",
    "duckdb",
    "pinecone",
    "weaviate",
    "chroma",
    "qdrant",
    "milvus",
    # Cloud & DevOps
    "aws",
    "azure",
    "gcp",
    "google cloud",
    "kubernetes",
    "docker",
    "terraform",
    "ansible",
    "puppet",
    "chef",
    "jenkins",
    "github actions",
    "gitlab ci",
    "circleci",
    "argocd",
    "helm",
    "prometheus",
    "grafana",
    "datadog",
    "splunk",
    "nginx",
    "apache",
    "istio",
    "envoy",
    "vault",
    # MLOps & Data Engineering
    "mlflow",
    "kubeflow",
    "airflow",
    "prefect",
    "dagster",
    "dbt",
    "great expectations",
    "feast",
    "bentoml",
    "seldon",
    "triton",
    "sagemaker",
    "vertex ai",
    "azure ml",
    "wandb",
    "neptune",
    "comet",
    "label studio",
    "dvc",
    # AI / ML Concepts
    "machine learning",
    "deep learning",
    "natural language processing",
    "nlp",
    "computer vision",
    "reinforcement learning",
    "generative ai",
    "llm",
    "large language model",
    "retrieval augmented generation",
    "rag",
    "transfer learning",
    "fine-tuning",
    "prompt engineering",
    "embeddings",
    "vector database",
    "semantic search",
    "object detection",
    "image segmentation",
    "speech recognition",
    "recommendation systems",
    "time series",
    "anomaly detection",
    "graph neural networks",
    "gnn",
    "transformers",
    "bert",
    "gpt",
    "attention",
    "convolutional neural network",
    "cnn",
    "recurrent neural network",
    "rnn",
    "lstm",
    "gan",
    "variational autoencoder",
    "diffusion models",
    "stable diffusion",
    "feature engineering",
    "hyperparameter tuning",
    "cross-validation",
    "a/b testing",
    "statistical modeling",
    "bayesian inference",
    # Software Engineering
    "microservices",
    "rest api",
    "graphql",
    "grpc",
    "websocket",
    "kafka",
    "rabbitmq",
    "sqs",
    "event-driven architecture",
    "cqrs",
    "domain driven design",
    "ddd",
    "clean architecture",
    "solid principles",
    "design patterns",
    "test-driven development",
    "tdd",
    "bdd",
    "agile",
    "scrum",
    "kanban",
    "ci/cd",
    "devops",
    "sre",
    "system design",
    "distributed systems",
    "high availability",
    "load balancing",
    "caching",
    "cdn",
    "api gateway",
    "oauth",
    "jwt",
    "saml",
    "openid",
    "cryptography",
    "security",
    # Data Science
    "data analysis",
    "data visualization",
    "business intelligence",
    "tableau",
    "power bi",
    "looker",
    "metabase",
    "data warehousing",
    "etl",
    "elt",
    "data pipeline",
    "data modeling",
    "statistics",
    "probability",
    "regression",
    "classification",
    "clustering",
    "dimensionality reduction",
    "pca",
    "tsne",
    "umap",
    "feature selection",
    "data cleaning",
    "eda",
    # Business & Soft Skills
    "product management",
    "project management",
    "stakeholder management",
    "technical writing",
    "documentation",
    "communication",
    "leadership",
    "team management",
    "mentoring",
    "hiring",
    "recruitment",
    "budget management",
    "roadmap planning",
    "okr",
    "kpi",
    # Version Control & Tools
    "git",
    "github",
    "gitlab",
    "bitbucket",
    "jira",
    "confluence",
    "slack",
    "linear",
    "notion",
    "figma",
    "postman",
    "swagger",
    "openapi",
    # Mobile
    "android",
    "ios",
    "react native",
    "flutter",
    "xamarin",
    "ionic",
    # Emerging
    "blockchain",
    "web3",
    "solidity",
    "smart contracts",
    "nft",
    "ar/vr",
    "unity",
    "unreal engine",
    "edge computing",
    "iot",
    "quantum computing",
    "robotics",
    "ros",
]

# ── Stopwords for BM25 tokenisation ──────────────────────────────────────────
_STOPWORDS: set[str] = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "must",
    "shall",
    "can",
    "need",
    "it",
    "its",
    "this",
    "that",
    "these",
    "those",
    "i",
    "we",
    "you",
    "he",
    "she",
    "they",
    "us",
    "our",
    "their",
    "my",
    "your",
    "his",
    "her",
    "not",
    "no",
    "so",
    "if",
    "as",
    "up",
    "out",
    "about",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "between",
    "more",
    "most",
    "other",
    "some",
    "such",
    "than",
    "then",
    "there",
    "when",
    "where",
    "who",
    "which",
    "what",
    "how",
    "all",
    "each",
    "both",
    "few",
    "over",
    "under",
    "again",
    "further",
    "also",
    "just",
    "very",
    "too",
    "well",
}

# ── Seniority detection patterns ─────────────────────────────────────────────
_SENIORITY_PATTERNS = [
    (
        "executive",
        re.compile(
            r"\b(ceo|cto|coo|cfo|cio|cpo|ciso|president|evp|svp|"
            r"chief\s+\w+\s+officer|vp\s+of|vice\s+president)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "principal",
        re.compile(
            r"\b(principal|distinguished|staff|fellow|director|" r"vice\s+president|vp)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "senior",
        re.compile(
            r"\b(senior|sr\.|lead|head\s+of|architect|manager|" r"engineering\s+manager|em)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "junior",
        re.compile(r"\b(junior|jr\.|associate\s+(?:engineer|developer|analyst))\b", re.IGNORECASE),
    ),
    (
        "entry",
        re.compile(
            r"\b(intern|trainee|graduate|fresher|entry[\s-]level|" r"entry\s+level)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "mid",
        re.compile(
            r"\b(engineer|developer|analyst|specialist|consultant|" r"programmer|scientist)\b",
            re.IGNORECASE,
        ),
    ),
]

# ── Experience parsing patterns ───────────────────────────────────────────────
_EXP_PATTERNS = [
    # "10+ years", "10+ yrs"
    re.compile(r"(\d+)\s*\+\s*(?:years?|yrs?)\s*(?:of\s+)?(?:exp(?:erience)?)?", re.IGNORECASE),
    # "10-15 years"
    re.compile(r"(\d+)\s*[-–]\s*(\d+)\s*(?:years?|yrs?)", re.IGNORECASE),
    # "10 years of experience"
    re.compile(
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s*(?:of\s+)?(?:exp(?:erience)?)?", re.IGNORECASE
    ),
    # "experience of 10 years"
    re.compile(r"exp(?:erience)?\s+of\s+(\d+(?:\.\d+)?)\s*(?:years?|yrs?)", re.IGNORECASE),
]


def normalize_text(text: str) -> str:
    """
    Normalize text to lowercase, stripped, with special characters removed.

    Args:
        text: Raw input text.

    Returns:
        Normalized string: lowercase, stripped, punctuation replaced by space,
        multiple spaces collapsed.
    """
    if not text or not isinstance(text, str):
        return ""
    text = text.lower().strip()
    # Replace punctuation (except hyphens in compound words) with space
    text = re.sub(r"[^\w\s\-\+\#\.]", " ", text)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_skills_from_text(text: str, skill_list: list[str] | None = None) -> list[str]:
    """
    Find skills present in the given text using substring matching.

    Matching is case-insensitive and uses word-boundary awareness
    to avoid false positives (e.g. 'c' matching 'catch').

    Args:
        text: Profile or JD text to scan.
        skill_list: Custom skill list to match against. Defaults to CANONICAL_SKILLS.

    Returns:
        Deduplicated list of matched skill strings (normalized to lowercase).
    """
    if not text:
        return []

    skills_to_check = skill_list if skill_list is not None else CANONICAL_SKILLS
    normalized = normalize_text(text)
    found: list[str] = []
    seen: set[str] = set()

    for skill in skills_to_check:
        skill_lower = skill.lower()
        if skill_lower in seen:
            continue
        # Build regex with word boundaries, handling special chars like c++, c#
        escaped = re.escape(skill_lower)
        pattern = rf"(?<!\w){escaped}(?!\w)"
        try:
            if re.search(pattern, normalized):
                found.append(skill_lower)
                seen.add(skill_lower)
        except re.error:
            # Fallback to simple substring match for problematic patterns
            if skill_lower in normalized:
                found.append(skill_lower)
                seen.add(skill_lower)

    return found


def extract_years_of_experience(text: str) -> float:
    """
    Parse years of experience from a text string.

    Handles formats like:
        "5 years", "5+ years", "5-10 years" (returns midpoint),
        "experience of 5 years", "5 yrs", "5.5 years"

    Args:
        text: Raw text that may contain experience information.

    Returns:
        Parsed years as float. Returns 0.0 if no match found.
        Clamped to [0.0, 50.0].
    """
    if not text or not isinstance(text, str):
        return 0.0

    text_lower = text.lower()

    # Range pattern: "10-15 years" → take midpoint
    range_pattern = re.compile(
        r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
        re.IGNORECASE,
    )
    range_match = range_pattern.search(text_lower)
    if range_match:
        low = float(range_match.group(1))
        high = float(range_match.group(2))
        return min(max((low + high) / 2.0, 0.0), 50.0)

    # Plus pattern: "5+ years"
    plus_pattern = re.compile(
        r"(\d+(?:\.\d+)?)\s*\+\s*(?:years?|yrs?)",
        re.IGNORECASE,
    )
    plus_match = plus_pattern.search(text_lower)
    if plus_match:
        val = float(plus_match.group(1))
        return min(max(val, 0.0), 50.0)

    # Standard pattern: "5 years"
    std_pattern = re.compile(
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
        re.IGNORECASE,
    )
    std_match = std_pattern.search(text_lower)
    if std_match:
        val = float(std_match.group(1))
        return min(max(val, 0.0), 50.0)

    return 0.0


def tokenize_for_bm25(text: str) -> list[str]:
    """
    Tokenise text for BM25 indexing.

    Applies lowercase normalisation, removes punctuation, splits on whitespace,
    filters stopwords, and removes tokens shorter than 2 characters.

    Args:
        text: Raw input text.

    Returns:
        List of cleaned tokens suitable for BM25 indexing.
    """
    if not text or not isinstance(text, str):
        return []

    text_lower = text.lower()
    # Remove punctuation except hyphens and + and #
    text_clean = re.sub(r"[^\w\s\-\+\#]", " ", text_lower)
    # Split on whitespace
    tokens = text_clean.split()
    # Filter: remove stopwords, short tokens
    result = [t for t in tokens if len(t) >= 2 and t not in _STOPWORDS]
    return result


def build_candidate_text(profile: CandidateProfile) -> str:  # type: ignore[name-defined]
    """
    Build a rich text representation of a candidate profile for embedding.

    Concatenates title, company, skills, education, work history summary,
    and certifications into a single coherent text block.

    Args:
        profile: Parsed CandidateProfile instance.

    Returns:
        Combined text string optimised for semantic embedding.
    """
    parts: list[str] = []

    if profile.current_title:
        parts.append(f"Title: {profile.current_title}")
    if profile.current_company:
        parts.append(f"Company: {profile.current_company}")

    if profile.skills:
        parts.append("Skills: " + ", ".join(profile.skills[:50]))

    if profile.summary:
        parts.append(f"Summary: {profile.summary}")

    # Work experience: title + company + description
    for exp in profile.work_experience[:5]:
        exp_parts = []
        if exp.title:
            exp_parts.append(exp.title)
        if exp.company:
            exp_parts.append(f"at {exp.company}")
        if exp.description:
            # Truncate long descriptions
            desc = exp.description[:200]
            exp_parts.append(f"- {desc}")
        if exp_parts:
            parts.append("Experience: " + " ".join(exp_parts))

    # Education
    for edu in profile.education[:3]:
        edu_parts = []
        if edu.degree:
            edu_parts.append(edu.degree)
        if edu.field_of_study:
            edu_parts.append(f"in {edu.field_of_study}")
        if edu.institution:
            edu_parts.append(f"from {edu.institution}")
        if edu_parts:
            parts.append("Education: " + " ".join(edu_parts))

    if profile.certifications:
        parts.append("Certifications: " + ", ".join(profile.certifications[:10]))

    if profile.years_of_experience > 0:
        parts.append(f"Experience: {profile.years_of_experience:.1f} years")

    return " | ".join(parts)


def detect_seniority_from_title(title: str) -> str:
    """
    Detect the seniority level from a job title string.

    Uses regex pattern matching against SENIORITY_PATTERNS.
    Returns the first matched level.

    Args:
        title: Job title string (e.g., "Senior Machine Learning Engineer").

    Returns:
        Seniority level string: one of
        'executive', 'principal', 'senior', 'mid', 'junior', 'entry'.
        Defaults to 'mid' if no pattern matches.
    """
    if not title or not isinstance(title, str):
        return "mid"

    for level, pattern in _SENIORITY_PATTERNS:
        if pattern.search(title):
            return level

    return "mid"
