import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { CandidateResult, JobProfile, AnalyticsSummary } from '../lib/api';

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
