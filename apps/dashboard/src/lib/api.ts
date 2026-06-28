// ─── TypeScript interfaces matching backend Pydantic models ─────────────────

export interface CandidateProfile {
  candidate_id: string;
  name?: string;
  current_title?: string;
  current_company?: string;
  location?: string;
  email?: string;
  phone?: string;
  linkedin?: string;
  years_of_experience?: number;
  education?: EducationItem[];
  work_experience?: WorkExperience[];
  skills?: string[];
  certifications?: string[];
  raw_text?: string;
  embedding?: number[];
}

export interface EducationItem {
  degree?: string;
  institution?: string;
  field?: string;
  year?: number;
  gpa?: number;
}

export interface WorkExperience {
  company?: string;
  title?: string;
  start_date?: string;
  end_date?: string;
  duration_months?: number;
  description?: string;
  achievements?: string[];
}

export interface FeatureScores {
  skill_coverage: number;
  semantic_similarity: number;
  experience_score: number;
  domain_match: number;
  career_velocity: number;
  leadership_score: number;
  education_score: number;
  stability_score: number;
  certifications_score: number;
  location_match: number;
  availability_score: number;
}

export interface CandidateFeatures {
  candidate_id: string;
  experience_score: number;
  skill_coverage: number;
  semantic_similarity: number;
  domain_match: number;
  career_velocity: number;
  leadership_score: number;
  education_score: number;
  stability_score: number;
  certifications_score: number;
  location_match: number;
  availability_score: number;
  feature_scores?: FeatureScores;
}

export interface CouncilVote {
  council_name: string;
  score: number;
  confidence: number;
  strengths: string[];
  concerns: string[];
  reasoning?: string;
}

export interface ExplanationData {
  narrative?: string;
  hiring_narrative?: string;
  summary?: string;
  top_strengths?: string[];
  strengths?: Array<{ title: string; description?: string; evidence?: string[] }>;
  top_concerns?: string[];
  weaknesses?: Array<{ title: string; description?: string }>;
  counterfactual?: string;
  evidence?: Record<string, string[]>;
  feature_contributions?: Record<string, number>;
  risk_summary?: string;
  confidence_reason?: string;
}

export interface RiskFlags {
  employment_gaps?: boolean;
  frequent_job_changes?: boolean;
  overqualified?: boolean;
  location_mismatch?: boolean;
  salary_expectation_mismatch?: boolean;
  visa_required?: boolean;
}

export interface CandidateResult {
  candidate_id: string;
  rank: number;
  overall_score: number;
  confidence_score: number;
  recommendation: string;
  risk_level: string;
  features?: CandidateFeatures;
  council_votes?: CouncilVote[];
  explanation?: ExplanationData;
  profile?: CandidateProfile;
  stage?: number;
  percentile?: number;
  genome_scores?: {
    technical: number;
    career: number;
    domain: number;
    leadership: number;
    learning: number;
    stability: number;
    behavioral: number;
    readiness: number;
  };
  risk_flags?: RiskFlags;
}

export interface RankedList {
  job_id: string;
  candidates: CandidateResult[];
  total_processed: number;
  processing_time_seconds: number;
  metadata?: Record<string, unknown>;
}

export interface SkillRequirement {
  skill: string;
  weight?: number;
  required?: boolean;
}

export interface JobProfile {
  job_id: string;
  title: string;
  description: string;
  required_skills?: SkillRequirement[] | string[];
  nice_to_have_skills?: string[];
  must_have?: string[];
  implicit_expectations?: string[];
  red_flags?: string[];
  ideal_persona?: string;
  domain?: string;
  primary_domain?: string;
  seniority_level?: string;
  min_experience_years?: number;
  embedding?: number[];
  genome_weights?: Record<string, number>;
}

export interface AnalyticsSummary {
  job_id: string;
  total_candidates: number;
  avg_score: number;
  top_score: number;
  score_distribution: Record<string, number>;
  recommendation_distribution: Record<string, number>;
  risk_distribution: Record<string, number>;
  confidence_distribution: Record<string, number>;
  feature_importance: Record<string, number>;
  top_skills: Record<string, number>;
  stage_distribution?: Record<string, number>;
}

// ─── API functions ───────────────────────────────────────────────────────────

const BASE = '/api/v1';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => 'Unknown error');
    throw new Error(`API Error ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  analyzeJob: (description: string, title: string): Promise<JobProfile> =>
    request('/jobs/analyze', {
      method: 'POST',
      body: JSON.stringify({ description, title }),
    }),

  getRankedCandidates: (
    jobId: string,
    page = 1,
    pageSize = 20
  ): Promise<RankedList> =>
    request(`/jobs/${jobId}/rankings?page=${page}&page_size=${pageSize}`),

  getCandidateDetail: (
    jobId: string,
    candidateId: string
  ): Promise<CandidateResult> =>
    request(`/jobs/${jobId}/candidates/${candidateId}`),

  getAnalytics: (jobId: string): Promise<AnalyticsSummary> =>
    request(`/jobs/${jobId}/analytics`),

  getHealth: (): Promise<{ status: string; version: string }> =>
    request('/health'),

  generateSubmission: (
    jobId: string
  ): Promise<{ path: string; row_count: number }> =>
    request(`/jobs/${jobId}/submission/generate`, { method: 'POST' }),

  validateSubmission: (
    jobId: string
  ): Promise<{ valid: boolean; errors: string[] }> =>
    request(`/jobs/${jobId}/submission/validate`),
};
