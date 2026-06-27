"""
TalentGraph AI — Fix & Re-Rank Script
Fixes broken feature extraction and re-runs ranking to produce correct submission.
"""
import sys, os, json, re, time
sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

from services.preprocessing.feature_store import FeatureStore
from services.preprocessing.parser import CandidateParser
from services.preprocessing.career_parser import CareerParser
from services.preprocessing.feature_extractor import FeatureExtractor
from services.analytics.submission_generator import SubmissionGenerator
from shared.config import settings
from shared.types.candidate import CandidateProfile, WorkExperience, EducationEntry, EducationLevel, RedrobSignals, AvailabilityStatus
from shared.types.ranking import CandidateResult, HiringRecommendation, ConfidenceLevel
from shared.constants import SUBMISSION_COLUMNS
import polars as pl

print("=" * 60)
print("TalentGraph AI — Fix & Re-Rank")
print("=" * 60)

# ── Step 1: Load raw CSV ──────────────────────────────────────────────────────
print("\n[1/5] Loading raw candidates CSV...")
df = pl.read_csv(
    'data/raw/candidates.csv',
    infer_schema_length=2000,
    ignore_errors=True,
    null_values=["", "NULL", "null", "NA", "N/A", "nan", "NaN"],
)
print(f"  Loaded {df.height} candidates")

# ── Step 2: Parse & extract features properly ─────────────────────────────────
print("\n[2/5] Parsing profiles and extracting features...")
parser = CandidateParser()
career_parser = CareerParser()
extractor = FeatureExtractor()
db = FeatureStore(settings.duckdb_path)
db.connect()

profiles = {}
features_map = {}

rows = df.to_dicts()
for i, row in enumerate(rows):
    try:
        cid = str(row.get('candidate_id', '')).strip()
        if not cid:
            continue

        # Parse work history from JSON string in work_history column
        work_exp = []
        wh_raw = row.get('work_history', '')
        if wh_raw and isinstance(wh_raw, str) and wh_raw.strip().startswith('['):
            try:
                wh_data = json.loads(wh_raw)
                for job in wh_data:
                    we = WorkExperience(
                        company=job.get('company', ''),
                        title=job.get('title', ''),
                        duration_months=int(job.get('duration_months', 12)),
                        start_date=job.get('start_date', ''),
                        end_date=job.get('end_date', ''),
                        is_current=bool(job.get('is_current', False)),
                        description='',
                        achievements=[],
                    )
                    work_exp.append(we)
            except Exception:
                pass

        # Parse education from JSON string
        edu_entries = []
        edu_raw = row.get('education', '')
        if edu_raw and isinstance(edu_raw, str) and edu_raw.strip().startswith('['):
            try:
                edu_data = json.loads(edu_raw)
                for edu in edu_data:
                    degree_str = edu.get('degree', '').lower()
                    level = EducationLevel.UNKNOWN
                    if 'phd' in degree_str or 'doctor' in degree_str:
                        level = EducationLevel.PHD
                    elif 'mca' in degree_str or 'msc' in degree_str or 'm.tech' in degree_str or 'master' in degree_str:
                        level = EducationLevel.MASTERS
                    elif 'mba' in degree_str:
                        level = EducationLevel.MBA
                    elif 'b.tech' in degree_str or 'b.sc' in degree_str or 'be' in degree_str or 'btech' in degree_str or 'bachelor' in degree_str:
                        level = EducationLevel.BACHELORS
                    ee = EducationEntry(
                        institution=edu.get('institution', ''),
                        degree=edu.get('degree', ''),
                        field_of_study=edu.get('field_of_study', ''),
                        level=level,
                        end_year=edu.get('end_year'),
                    )
                    edu_entries.append(ee)
            except Exception:
                pass

        # Build redrob signals from behavioral columns
        availability_str = str(row.get('availability_status', 'unknown')).lower()
        avail_status = AvailabilityStatus.UNKNOWN
        if 'immediately' in availability_str:
            avail_status = AvailabilityStatus.IMMEDIATELY_AVAILABLE
        elif 'notice' in availability_str:
            avail_status = AvailabilityStatus.NOTICE_PERIOD
        elif 'passive' in availability_str:
            avail_status = AvailabilityStatus.PASSIVE
        elif 'not_looking' in availability_str:
            avail_status = AvailabilityStatus.NOT_LOOKING

        try:
            notice = int(float(row.get('notice_period_days', 0) or 0))
        except:
            notice = 0

        redrob = RedrobSignals(
            profile_views=int(row.get('profile_views', 0) or 0),
            application_count=int(row.get('application_count', 0) or 0),
            response_rate=float(row.get('response_rate', 0.5) or 0.5),
            last_active_days=int(row.get('last_active_days', 30) or 30),
            availability_status=avail_status,
            notice_period_days=notice,
        )

        # Parse skills
        skills = parser.parse_skills(str(row.get('skills', '') or ''))

        # Build profile
        profile = CandidateProfile(
            candidate_id=cid,
            name=str(row.get('name', '') or ''),
            email=str(row.get('email', '') or ''),
            phone=str(row.get('phone', '') or ''),
            current_title=str(row.get('current_title', '') or ''),
            current_company=str(row.get('current_company', '') or ''),
            years_of_experience=float(row.get('years_of_experience', 0) or 0),
            skills=skills,
            education=edu_entries,
            work_experience=work_exp,
            certifications=[],
            languages=[],
            summary='',
            redrob_signals=redrob,
            raw_data={},
        )

        # Extract features
        feats = extractor.extract_all(profile)
        profiles[cid] = profile
        features_map[cid] = feats

        if (i + 1) % 100 == 0:
            print(f"  Parsed {i+1}/{len(rows)} candidates...", end='\r')

    except Exception as e:
        pass

print(f"\n  Successfully parsed {len(profiles)} profiles")

# ── Step 3: Save updated features to store ────────────────────────────────────
print("\n[3/5] Saving updated features to feature store...")
saved = 0
conn = db.connect()
for cid, feats in features_map.items():
    try:
        # Upsert directly into DuckDB
        conn.execute("""
            INSERT OR REPLACE INTO candidate_features
            (candidate_id, experience_score, skill_coverage, semantic_similarity, domain_match,
             career_velocity, leadership_score, education_score, stability_score, certifications_score,
             location_match, availability_score, research_score, behavior_score, profile_completeness,
             gap_risk, job_hop_risk, skill_consistency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            feats.candidate_id,
            feats.experience_score,
            feats.skill_coverage,
            0.0,  # semantic_similarity computed at rank time
            feats.domain_match,
            feats.career_velocity,
            feats.leadership_score,
            feats.education_level_score,
            feats.career_stability,
            0.0,  # certifications
            0.5,  # location_match default
            feats.hiring_availability,
            feats.research_score,
            feats.behavior_score,
            feats.profile_completeness,
            feats.gap_risk,
            feats.job_hop_risk,
            feats.skill_consistency,
        ])
        saved += 1
    except Exception as e:
        pass
print(f"  Saved {saved} feature vectors")

# Verify
conn = db.connect()
sample = conn.execute(
    "SELECT candidate_id, experience_score, leadership_score, stability_score, career_velocity FROM candidate_features LIMIT 3"
).fetchall()
print("  Sample features after fix:")
for r in sample:
    print(f"    {r[0]}: exp={r[1]:.3f}, lead={r[2]:.3f}, stab={r[3]:.3f}, vel={r[4]:.3f}")

# ── Step 4: Score with improved skill matching ────────────────────────────────
print("\n[4/5] Running ranking with improved scoring...")

# Job skills - use broader synonyms
JD_SKILLS = {
    'python', 'pytorch', 'tensorflow', 'scikit-learn', 'sklearn',
    'fastapi', 'django', 'flask', 'microservices', 'docker', 'kubernetes',
    'postgresql', 'postgres', 'redis', 'ml', 'machine learning',
    'deep learning', 'transformers', 'hugging face', 'nlp', 'xgboost',
    'lightgbm', 'neural', 'cv', 'computer vision', 'bert', 'gpt',
    'sql', 'mysql', 'mongodb', 'api', 'apis', 'git', 'linux', 'spark',
    'airflow', 'aws', 'gcp', 'azure', 'celery', 'kafka', 'go', 'java',
    'spring', 'tensorflow', 'keras', 'numpy', 'pandas', 'scipy',
}

# Soft scoring - broader group for ML/backend roles
ML_SKILLS = {'pytorch', 'tensorflow', 'scikit-learn', 'sklearn', 'xgboost', 'lightgbm',
              'ml', 'machine learning', 'deep learning', 'nlp', 'transformers', 'hugging face',
              'computer vision', 'bert', 'gpt', 'neural', 'keras', 'numpy', 'pandas',
              'scipy', 'statsmodels'}

results = []
feature_rows = conn.execute("SELECT * FROM candidate_features").fetchall()
feat_cols = [d[0] for d in conn.execute("SELECT * FROM candidate_features LIMIT 0").description]

for feat_row in feature_rows:
    feat_dict = dict(zip(feat_cols, feat_row))
    cid = feat_dict['candidate_id']
    profile = profiles.get(cid)
    if not profile:
        continue

    candidate_skills = set(s.lower().strip() for s in profile.skills)

    # Broad skill coverage: count any overlap with JD-related skills (normalized)
    jd_overlap = len(candidate_skills.intersection(JD_SKILLS))
    ml_overlap = len(candidate_skills.intersection(ML_SKILLS))

    # Normalized skill score - count partial matches too
    skill_coverage = min(1.0, (jd_overlap / 6.0 + ml_overlap / 4.0) / 2.0)

    # Experience score (already computed)
    exp_score = float(feat_dict.get('experience_score', 0.0))

    # Experience fit for Senior ML Engineer (5+ years = ideal)
    yoe = profile.years_of_experience
    if yoe >= 5:
        exp_fit = min(1.0, 0.6 + (yoe - 5) * 0.04)
    elif yoe >= 3:
        exp_fit = 0.4 + (yoe - 3) * 0.1
    else:
        exp_fit = max(0.1, yoe * 0.13)

    # Leadership score
    lead_score = float(feat_dict.get('leadership_score', 0.0))
    
    # Stability
    stab_score = float(feat_dict.get('stability_score', 0.5))
    if stab_score == 0.0:
        # Default to moderate if no data
        stab_score = 0.5

    # Career velocity
    vel_score = float(feat_dict.get('career_velocity', 0.0))
    if vel_score == 0.0:
        vel_score = 0.4  # Default

    # Availability bonus
    avail_score = float(feat_dict.get('availability_score', 0.7))

    # Education score
    edu_score = float(feat_dict.get('education_score', 0.5))

    # Behavior/platform signal
    behavior_score = float(feat_dict.get('behavior_score', 0.5))

    # Weighted composite score
    # Weights tuned for "Senior ML Engineer" role
    final_score = (
        skill_coverage   * 0.30 +   # Skill match (most important)
        exp_fit          * 0.20 +   # Experience fit 
        exp_score        * 0.12 +   # General experience
        edu_score        * 0.08 +   # Education
        stab_score       * 0.10 +   # Stability
        lead_score       * 0.07 +   # Leadership
        avail_score      * 0.07 +   # Availability
        behavior_score   * 0.06     # Platform signals
    )

    # Clamp to [0, 1]
    final_score = min(1.0, max(0.0, final_score))

    # Confidence
    evidence_count = jd_overlap + (1 if yoe >= 3 else 0) + (1 if edu_score > 0.5 else 0) + (1 if len(profile.work_experience) > 1 else 0)
    if evidence_count >= 4:
        conf = ConfidenceLevel.HIGH
    elif evidence_count >= 2:
        conf = ConfidenceLevel.MEDIUM
    else:
        conf = ConfidenceLevel.LOW

    results.append({
        'candidate_id': cid,
        'score': final_score,
        'confidence': conf,
        'profile': profile,
        'features': features_map.get(cid),
    })

# Sort descending by score
results.sort(key=lambda x: x['score'], reverse=True)

# Take top 100 and assign percentile-based recommendations
top100_raw = results[:100]
all_scores = [r['score'] for r in top100_raw]
max_s, min_s = max(all_scores), min(all_scores)

top100 = []
for i, r in enumerate(top100_raw):
    # Percentile rank within the top 100 (0 = best, 99 = worst)
    pct = i / 100.0  # 0.0 = rank 1, 0.99 = rank 100

    # Realistic tier assignment based on rank position
    if pct < 0.12:       # Top 12 = Strong Hire
        rec = HiringRecommendation.STRONG_HIRE
    elif pct < 0.45:     # Next 33 = Hire
        rec = HiringRecommendation.HIRE
    elif pct < 0.75:     # Next 30 = Consider
        rec = HiringRecommendation.CONSIDER
    else:                # Bottom 25 = Pass
        rec = HiringRecommendation.PASS

    cr = CandidateResult(
        candidate_id=r['candidate_id'],
        rank=i + 1,
        overall_score=r['score'],
        confidence_level=r['confidence'],
        hiring_recommendation=rec,
        profile=r['profile'],
        features=r['features'],
    )
    top100.append(cr)

print(f"  Scored {len(results)} candidates")
print(f"  Top 100 selected")
print()
print("  Score distribution of top 100:")
buckets = {'Strong Hire': 0, 'Hire': 0, 'Consider': 0, 'Pass': 0, 'Reject': 0}
for r in top100:
    buckets[r.hiring_recommendation.value] = buckets.get(r.hiring_recommendation.value, 0) + 1
for k, v in buckets.items():
    if v > 0:
        print(f"    {k}: {v}")

print("\n  Top 10 candidates:")
for r in top100[:10]:
    print(f"    #{r.rank} {r.candidate_id} | Score: {r.overall_score:.4f} | {r.hiring_recommendation.value} | {r.confidence_level.value}")

# ── Step 5: Generate submission ───────────────────────────────────────────────
print("\n[5/5] Generating submission files...")

# CSV
import csv
from pathlib import Path

csv_path = 'data/submission.csv'
xlsx_path = 'data/submission.xlsx'

p = Path(csv_path)
with p.open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(SUBMISSION_COLUMNS)
    for r in top100:
        writer.writerow([
            r.candidate_id,
            r.rank,
            f"{r.overall_score:.6f}",
            r.confidence_level.value,
            r.hiring_recommendation.value,
        ])

print(f"  CSV written: {csv_path}")

# XLSX
try:
    import pandas as pd
    data = [{
        'candidate_id': r.candidate_id,
        'rank': r.rank,
        'overall_score': float(f"{r.overall_score:.6f}"),
        'confidence_level': r.confidence_level.value,
        'hiring_recommendation': r.hiring_recommendation.value,
    } for r in top100]
    pd.DataFrame(data, columns=SUBMISSION_COLUMNS).to_excel(xlsx_path, index=False)
    print(f"  XLSX written: {xlsx_path}")
except ImportError:
    print("  (pandas/openpyxl not available, XLSX skipped)")

# Validate
from services.analytics.submission_generator import SubmissionGenerator
gen = SubmissionGenerator()
valid, errors = gen.validate(csv_path)
print(f"\n  Submission valid: {valid}")
if errors:
    for e in errors[:5]:
        print(f"  ERROR: {e}")

db.close()
print("\n" + "=" * 60)
print("Re-ranking complete!")
print("=" * 60)
