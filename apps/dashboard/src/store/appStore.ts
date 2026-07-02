import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { CandidateResult, JobProfile, AnalyticsSummary } from '../lib/api';
import { api } from '../lib/api';

export interface DemoData {
  jobProfile: JobProfile;
  rankedList: {
    job_id: string;
    candidates: CandidateResult[];
    total_processed: number;
    processing_time_seconds: number;
  };
  analytics: AnalyticsSummary;
}

interface AppState {
  currentJobId: string | null;
  setCurrentJobId: (id: string | null) => void;

  currentJobTitle: string | null;
  setCurrentJobTitle: (title: string | null) => void;

  selectedCandidateId: string | null;
  setSelectedCandidateId: (id: string | null) => void;

  isDemoMode: boolean;
  setDemoMode: (v: boolean) => void;

  demoData: DemoData | null;
  setDemoData: (data: DemoData) => void;

  loadJobData: (jobId: string) => Promise<void>;

  sidebarCollapsed: boolean;
  setSidebarCollapsed: (v: boolean) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      currentJobId: null,
      setCurrentJobId: (id) => set({ currentJobId: id }),

      currentJobTitle: null,
      setCurrentJobTitle: (title) => set({ currentJobTitle: title }),

      selectedCandidateId: null,
      setSelectedCandidateId: (id) => set({ selectedCandidateId: id }),

      isDemoMode: true, // Demo mode on by default
      setDemoMode: (v) => set({ isDemoMode: v }),

      demoData: null,
      setDemoData: (data) => set({ demoData: data }),

      loadJobData: async (jobId) => {
        try {
          const jobProfile = await api.getJob(jobId);
          const rankedRes = await api.getRankedCandidates(jobId, 1, 100);
          const analyticsRes = await api.getAnalytics(jobId);

          const mappedAnalytics: AnalyticsSummary = {
            job_id: analyticsRes.job_id,
            total_candidates: analyticsRes.total_candidates,
            avg_score: analyticsRes.avg_overall_score,
            top_score: rankedRes.candidates.length > 0 ? rankedRes.candidates[0].overall_score : 0,
            score_distribution: analyticsRes.score_distribution,
            recommendation_distribution: analyticsRes.recommendation_distribution,
            risk_distribution: analyticsRes.risk_distribution || {},
            confidence_distribution: analyticsRes.confidence_distribution,
            feature_importance: (analyticsRes.feature_importance || []).reduce((acc: any, curr: any) => {
              acc[curr.feature_name] = curr.importance_score;
              return acc;
            }, {}),
            top_skills: {},
            stage_distribution: {
              Stage1: analyticsRes.funnel?.stage1_count || 1000,
              Stage2: analyticsRes.funnel?.stage2_count || 200,
              Stage3: analyticsRes.funnel?.stage3_count || 100,
            }
          };

          const mappedCandidates: CandidateResult[] = (rankedRes.candidates || []).map((c: any) => ({
            ...c,
            recommendation: c.hiring_recommendation || c.recommendation,
            confidence_score: c.confidence_level === 'High' ? 0.95 : c.confidence_level === 'Medium' ? 0.75 : c.confidence_level === 'Low' ? 0.45 : (c.confidence_score ?? 0.88),
            risk_level: c.risk_level || c.risk_assessment?.risk_level || 'Low',
          }));

          const loadedData: DemoData = {
            jobProfile,
            rankedList: {
              job_id: jobId,
              candidates: mappedCandidates,
              total_processed: rankedRes.total,
              processing_time_seconds: 5.3
            },
            analytics: mappedAnalytics
          };

          set({
            demoData: loadedData,
            currentJobId: jobId,
            currentJobTitle: jobProfile.title,
            isDemoMode: false
          });
        } catch (err) {
          console.error("Failed to load job data from backend:", err);
          throw err;
        }
      },

      sidebarCollapsed: false,
      setSidebarCollapsed: (v) => set({ sidebarCollapsed: v }),
    }),
    {
      name: 'talentgraph-store',
      partialize: (state) => ({
        isDemoMode: state.isDemoMode,
        currentJobId: state.currentJobId,
        currentJobTitle: state.currentJobTitle,
      }),
    }
  )
);
