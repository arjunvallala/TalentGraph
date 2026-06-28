"""
TalentGraph AI — Demo Data Generator

Generates a realistic candidates.csv with 1,000 rows (including names, skills,
experience, education, and Redrob signals) and a sample job_description.txt.
"""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

# Sample lists for generation
FIRST_NAMES = [
    "Aarav",
    "Aditi",
    "Arjun",
    "Ananya",
    "Deepak",
    "Divya",
    "Ishaan",
    "Kavya",
    "Rahul",
    "Priya",
    "Sanjay",
    "Sneha",
    "Vikram",
    "Riya",
    "Vivek",
    "Neha",
]
LAST_NAMES = [
    "Sharma",
    "Patel",
    "Kumar",
    "Singh",
    "Nair",
    "Mehta",
    "Reddy",
    "Gupta",
    "Joshi",
    "Verma",
    "Iyer",
    "Sen",
    "Rao",
    "Bose",
    "Pillai",
    "Thakur",
]
DOMAINS = ["machine learning", "backend", "frontend", "devops", "data engineering"]

SKILL_POOL = {
    "machine learning": [
        "python",
        "pytorch",
        "tensorflow",
        "scikit-learn",
        "xgboost",
        "transformers",
        "pandas",
        "numpy",
        "keras",
        "hugging face",
    ],
    "backend": [
        "python",
        "fastapi",
        "django",
        "postgresql",
        "redis",
        "docker",
        "apis",
        "mongodb",
        "mysql",
        "node.js",
        "go",
        "java",
        "spring boot",
    ],
    "frontend": [
        "react",
        "typescript",
        "javascript",
        "tailwind",
        "next.js",
        "html",
        "css",
        "vue",
        "angular",
        "sass",
    ],
    "devops": [
        "aws",
        "docker",
        "kubernetes",
        "terraform",
        "ci/cd",
        "jenkins",
        "gcp",
        "azure",
        "ansible",
        "linux",
        "bash",
    ],
    "data engineering": [
        "python",
        "spark",
        "hadoop",
        "kafka",
        "etl",
        "airflow",
        "snowflake",
        "redshift",
        "sql",
        "hive",
    ],
}

COMPANIES = [
    "TCS",
    "Infosys",
    "Wipro",
    "Flipkart",
    "Swiggy",
    "Zomato",
    "CRED",
    "Razorpay",
    "Ola",
    "Paytm",
    "Freshworks",
    "Zoho",
]
UNIVERSITIES = [
    "IIT Bombay",
    "IIT Delhi",
    "IIT Madras",
    "BITS Pilani",
    "IIIT Hyderabad",
    "Delhi University",
    "Anna University",
    "VIT",
    "NIT Trichy",
]
DEGREES = [
    ("B.Tech", "Computer Science"),
    ("M.Tech", "Data Science"),
    ("B.Sc", "Information Technology"),
    ("MCA", "Computer Applications"),
    ("PhD", "Machine Learning"),
]

TITLES = {
    "machine learning": [
        "ML Engineer",
        "Data Scientist",
        "Computer Vision Engineer",
        "NLP Researcher",
        "AI Engineer",
    ],
    "backend": [
        "Backend Developer",
        "Software Engineer - Backend",
        "API Developer",
        "Systems Engineer",
    ],
    "frontend": ["Frontend Engineer", "UI Developer", "React Developer", "Web Developer"],
    "devops": [
        "DevOps Engineer",
        "Cloud Architect",
        "Site Reliability Engineer",
        "Platform Engineer",
    ],
    "data engineering": [
        "Data Engineer",
        "ETL Developer",
        "Data Platform Engineer",
        "Big Data Developer",
    ],
}


def generate_candidate(cid_num: int) -> dict:
    domain = random.choice(DOMAINS)
    skills = random.sample(SKILL_POOL[domain], k=random.randint(4, 7))
    # Add some common skills
    skills.extend(random.sample(["git", "sql", "agile", "communication"], k=2))

    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)

    yoe = round(random.uniform(1.0, 12.0), 1)

    # Title seniority based on yoe
    if yoe >= 8.0:
        title = f"Principal {random.choice(TITLES[domain])}"
    elif yoe >= 5.0:
        title = f"Senior {random.choice(TITLES[domain])}"
    else:
        title = random.choice(TITLES[domain])

    # Construct education
    edu_deg, edu_field = random.choice(DEGREES)
    education = [
        {
            "institution": random.choice(UNIVERSITIES),
            "degree": edu_deg,
            "field_of_study": edu_field,
            "level": "masters" if "M" in edu_deg else "phd" if "PhD" in edu_deg else "bachelors",
            "end_year": 2026 - random.randint(1, 10),
        }
    ]

    # Construct work history (newest first)
    work_history = []
    num_jobs = max(1, int(yoe / 2.5))
    current_year = 2026
    for i in range(num_jobs):
        duration = random.randint(12, 36)
        work_history.append(
            {
                "company": random.choice(COMPANIES),
                "title": (
                    f"Senior {random.choice(TITLES[domain])}"
                    if i == 0 and yoe >= 5.0
                    else random.choice(TITLES[domain])
                ),
                "duration_months": duration,
                "start_date": f"{current_year - int(duration/12)}-01",
                "end_date": f"{current_year}-01" if i > 0 else "Present",
                "is_current": i == 0,
            }
        )
        current_year -= int(duration / 12)

    return {
        "candidate_id": f"cand_{cid_num:04d}",
        "name": f"{first} {last}",
        "email": f"{first.lower()}.{last.lower()}@example.com",
        "phone": f"+91 {random.randint(7000000000, 9999999999)}",
        "current_title": title,
        "current_company": random.choice(COMPANIES),
        "years_of_experience": yoe,
        "skills": ",".join(skills),
        "education": json.dumps(education),
        "work_history": json.dumps(work_history),
        "profile_views": random.randint(5, 120),
        "application_count": random.randint(1, 15),
        "response_rate": round(random.uniform(0.3, 1.0), 2),
        "last_active_days": random.randint(0, 45),
        "availability_status": random.choice(
            ["immediately_available", "notice_period", "open_to_opportunities"]
        ),
        "notice_period_days": random.choice([0, 15, 30, 60]),
        "expected_salary": random.randint(6, 45) * 100000,  # INR
    }


def main():
    # 1. Generate Candidates CSV
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    csv_path = raw_dir / "candidates.csv"
    print(f"Generating 1,000 candidates in {csv_path}...")

    headers = [
        "candidate_id",
        "name",
        "email",
        "phone",
        "current_title",
        "current_company",
        "years_of_experience",
        "skills",
        "education",
        "work_history",
        "profile_views",
        "application_count",
        "response_rate",
        "last_active_days",
        "availability_status",
        "notice_period_days",
        "expected_salary",
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for idx in range(1, 1001):
            writer.writerow(generate_candidate(idx))

    # 2. Generate Sample Job Description
    jd_path = raw_dir / "job_description.txt"
    print(f"Generating sample job description in {jd_path}...")

    jd_content = """Position: Senior Machine Learning Engineer
Department: Core AI Platform
Location: Bengaluru, India (Hybrid)

About the Role:
We are looking for a Senior Machine Learning Engineer to join our core AI product team. You will lead the design, development, and deployment of scalable deep learning models. Our stack is primarily PyTorch, FastAPI, Docker, and PostgreSQL.

Requirements:
- Minimum 5 years of experience in machine learning or software engineering.
- Deep expertise in python, PyTorch or TensorFlow, and scikit-learn.
- Hands-on experience with FastAPI or Django backend microservices.
- Familiarity with containerization using Docker or Kubernetes.
- Solid understanding of databases (PostgreSQL or Redis).
- Strong track record of continuous learning or technical contributions.
"""

    jd_path.write_text(jd_content.strip(), encoding="utf-8")
    print("Demo generation complete!")


if __name__ == "__main__":
    main()
