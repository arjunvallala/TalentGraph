# TalentGraph AI

> **The AI Hiring Intelligence Platform that thinks like a hiring committee, not a search engine.**

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178c6.svg)](https://typescriptlang.org)
[![FAISS](https://img.shields.io/badge/FAISS-CPU-orange.svg)](https://faiss.ai)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![INDIA RUNS](https://img.shields.io/badge/INDIA%20RUNS-Data%20%26%20AI%20Challenge-purple.svg)]()

---

## 🧠 What is TalentGraph AI?

TalentGraph AI is an **offline, explainable, recruiter-grade AI Hiring Intelligence Platform** built for the INDIA RUNS Data & AI Challenge.

Unlike traditional Applicant Tracking Systems that rely on keyword matching, TalentGraph AI evaluates candidates the way experienced recruiters do — by combining technical expertise, career progression, behavioral signals, hiring risk assessment, and evidence-backed reasoning.

**The system doesn't return a ranked list. It returns a complete hiring decision.**

```
Job Description
     ↓
Job Intelligence Engine          →  Ideal Candidate Persona + Job Genome
     ↓
Hybrid Retrieval (FAISS + BM25)  →  Top 2,000 candidates
     ↓
Feature Ranking (15 features)    →  Top 200 candidates
     ↓
Hiring Council (5 evaluators)    →  Top 100 candidates
     ↓
Explainability Engine            →  Evidence + Narrative + Confidence
     ↓
Recruiter Dashboard              →  Transparent, actionable recommendations
```

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🔍 **Hybrid Retrieval** | BM25 + FAISS + Reciprocal Rank Fusion for maximum candidate recall |
| 🧬 **Candidate Genome** | Multidimensional capability profile across 8 axes |
| 👥 **Hiring Council** | 5 specialized parallel evaluators (Technical, Career, Behavior, Growth, Risk) |
| 📊 **15 Engineered Features** | Experience, Stability, Leadership, Learning, Behavior, Risk, and more |
| 💡 **Full Explainability** | Every recommendation backed by traceable evidence — no black boxes |
| 🎯 **Confidence Scoring** | High/Medium/Low confidence per recommendation |
| ⚠️ **Risk Assessment** | Job hopping, career gaps, profile completeness, engagement risk |
| 📈 **Analytics Dashboard** | Hiring funnel, feature importance, score distributions |
| 🔌 **Fully Offline** | No external API calls. CPU-only inference. |
| ⚡ **Fast** | < 5 minutes for 100,000 candidates on CPU |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Presentation Layer                          │
│              React + TypeScript + Tailwind + shadcn/ui          │
└──────────────────────────────┬──────────────────────────────────┘
                               │ REST API
┌──────────────────────────────▼──────────────────────────────────┐
│                     Application Layer                           │
│                    FastAPI /api/v1/*                             │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                    Intelligence Layer                            │
│   Job Engine │ Candidate Engine │ Career │ Behavior │ Risk      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                     Ranking Layer                                │
│   Stage 1: Hybrid Retrieval  →  Stage 2: Feature  →  Stage 3:  │
│   (FAISS + BM25 + RRF)           Ranking             Council    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                     Storage Layer                                │
│            DuckDB (Features)  +  FAISS (Embeddings)             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- 8GB RAM minimum (16GB recommended for 100K candidates)
- 10GB disk space (models + indexes)

### 1. Clone & Install

```bash
git clone https://github.com/your-org/talentgraph-ai.git
cd talentgraph-ai

# Python environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your paths (defaults work for local development)
```

### 3. Preprocessing (one-time setup)

```bash
# Place your candidates CSV in data/raw/candidates.csv
python -m scripts.preprocess --input data/raw/candidates.csv

# This will:
# - Parse all candidate profiles
# - Extract 15 features per candidate
# - Generate FAISS embeddings index
# - Build BM25 sparse index
# - Populate DuckDB feature store
```

### 4. Start the API

```bash
uvicorn apps.api.main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

### 5. Start the Dashboard

```bash
cd apps/dashboard
npm install
npm run dev
# Dashboard: http://localhost:5173
```

### 6. Run Ranking

```bash
# Via CLI
python -m scripts.rank --jd data/raw/job_description.txt --title "Senior ML Engineer"

# Via API
curl -X POST "http://localhost:8000/api/v1/jobs/analyze" \
  -H "Content-Type: application/json" \
  -d '{"title": "Senior ML Engineer", "description": "..."}'
```

---

## 🐳 Docker

```bash
# Start full stack
docker-compose up

# Run preprocessing
docker-compose --profile preprocessing run --rm preprocessing \
  --input /app/data/raw/candidates.csv

# Rebuild and restart
docker-compose up --build

# Demo mode (no preprocessing required)
DEMO_MODE=true docker-compose up
```

---

## 🎭 Demo Mode

For presentations and demos without a full dataset:

```bash
# In .env
DEMO_MODE=true

# Or via environment variable
DEMO_MODE=true uvicorn apps.api.main:app --reload
```

Demo mode loads pre-generated fixture data instantly — no preprocessing required.

```bash
# Generate demo data
python -m scripts.generate_demo
```

---

## 📊 Expected CSV Format

Your `data/raw/candidates.csv` should contain columns:

| Column | Required | Description |
|--------|----------|-------------|
| `candidate_id` | ✅ | Unique identifier |
| `name` | | Full name |
| `current_title` | | Current job title |
| `current_company` | | Current employer |
| `years_of_experience` | | Total years |
| `skills` | | Comma-separated skill list |
| `work_history` | | JSON or text of work history |
| `education` | | Education details |
| `certifications` | | Comma-separated list |
| `summary` | | Professional summary |
| `location` | | Current location |
| `profile_views` | | Platform views |
| `response_rate` | | Recruiter response rate (0–1) |
| `notice_period_days` | | Notice period |
| `availability_status` | | One of: immediately_available, notice_period, open_to_opportunities, not_looking |

Missing columns are handled gracefully — the system assigns default values and reduces the completeness score.

---

## 🏆 Submission Format

The generated `submission.csv` follows this format:

```csv
candidate_id,rank,overall_score,confidence_level,hiring_recommendation
C001,1,0.9234,High,Strong Hire
C047,2,0.8891,High,Strong Hire
C023,3,0.8734,High,Hire
...
```

Validate your submission:
```bash
python -m scripts.validate_submission
```

---

## 🧪 Running Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requires app to be importable)
pytest tests/integration/ -v

# All tests with coverage
pytest --cov=. --cov-report=html

# Performance benchmark
python -m scripts.benchmark --candidates 10000
```

---

## 📁 Project Structure

```
talentgraph-ai/
├── apps/
│   ├── api/            # FastAPI backend
│   └── dashboard/      # React + Vite frontend
├── services/
│   ├── preprocessing/  # Offline data pipeline
│   ├── intelligence/   # AI reasoning engines
│   ├── retrieval/      # Hybrid search
│   ├── ranking/        # 3-stage ranking + council
│   ├── explainability/ # Evidence + narratives
│   └── analytics/      # Dashboard data
├── shared/
│   ├── types/          # Pydantic models
│   ├── utils/          # Utilities
│   ├── config.py       # Settings
│   ├── constants.py    # System constants
│   └── exceptions.py   # Exception hierarchy
├── configs/            # YAML configurations
├── data/               # Data files (gitignored)
├── models/             # ML models (gitignored)
├── scripts/            # CLI tools
├── tests/              # Test suite
├── docker/             # Dockerfiles
└── docs/               # Documentation
```

---

## ⚙️ Configuration

All behavior is configurable via YAML files in `configs/`:

- `configs/features.yaml` — Feature weights and formulas
- `configs/ranking.yaml` — Stage weights and thresholds
- `configs/council.yaml` — Council evaluator weights
- `configs/app.yaml` — Application settings

Or via environment variables in `.env`.

---

## 🔬 Technical Details

### Embedding Model
- **Model**: `all-MiniLM-L6-v2` (22M parameters)
- **Dimension**: 384
- **Speed**: ~64 candidates/second on CPU
- **Memory**: ~100MB

### FAISS Index
- **Type**: `IndexFlatIP` (Inner Product with L2-normalized vectors = cosine similarity)
- **Search speed**: ~1,500 candidates in < 100ms

### Feature Store
- **Database**: DuckDB (columnar, in-process)
- **Tables**: candidates, features, evidence, jobs, rankings

### Ranking Performance (100K candidates, CPU only)
| Stage | Input | Output | Target Time |
|-------|-------|--------|-------------|
| Stage 1: Hybrid Retrieval | 100,000 | 2,000 | ~15s |
| Stage 2: Feature Ranking | 2,000 | 200 | ~30s |
| Stage 3: Hiring Council | 200 | 100 | ~60s |
| Stage 4: Explainability | 100 | 100 | ~30s |
| **Total** | **100,000** | **100** | **< 5 min** |

---

## 🤝 Contributing

See [docs/developer-guide.md](docs/developer-guide.md) for development setup and contribution guidelines.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🏆 Built for INDIA RUNS — Data & AI Challenge

TalentGraph AI was designed and built as a submission for the INDIA RUNS Data & AI Challenge, demonstrating that production-grade AI systems can be built offline, explainably, and at scale.

---

*Made with 🧠 by the TalentGraph AI Engineering Team*
