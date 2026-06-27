import React from 'react';
import { HelpCircle, ShieldCheck, HelpCircle as HelpIcon, ArrowUpRight, CheckCircle2 } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';

export const ExplainabilityPage: React.FC = () => {
  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">AI Explainability Engine</h1>
        <p className="text-sm text-muted-foreground">
          Traceable decision criteria and committee guidelines
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* How it works */}
        <div className="md:col-span-2 space-y-6">
          <GlassCard className="p-6 space-y-6">
            <h2 className="text-base font-bold text-white">How Candidates Are Ranked</h2>
            
            <div className="relative border-l-2 border-white/5 pl-6 ml-3 space-y-8">
              <div className="relative">
                <span className="absolute -left-[31px] top-0.5 w-4 h-4 rounded-full bg-accent border-2 border-background" />
                <h3 className="text-sm font-bold text-white">Stage 1: Hybrid Retrieval Ingestion</h3>
                <p className="text-xs text-muted-foreground mt-1">
                  Combines FAISS dense semantic vector matches and BM25 sparse keyword searches. Fuses rankings via Reciprocal Rank Fusion (RRF) to filter down the entire 100K candidates corpus to the top 2,000.
                </p>
              </div>

              <div className="relative">
                <span className="absolute -left-[31px] top-0.5 w-4 h-4 rounded-full bg-accent-violet border-2 border-background" />
                <h3 className="text-sm font-bold text-white">Stage 2: Multi-Dimensional Feature Sorting</h3>
                <p className="text-xs text-muted-foreground mt-1">
                  Loads 15 precomputed features (experience, velocity, gaps, stability) from DuckDB. Applies custom job description weight matrices to calculate overall fit, narrowing queue to top 200.
                </p>
              </div>

              <div className="relative">
                <span className="absolute -left-[31px] top-0.5 w-4 h-4 rounded-full bg-accent-emerald border-2 border-background" />
                <h3 className="text-sm font-bold text-white">Stage 3: Hiring Council consensus</h3>
                <p className="text-xs text-muted-foreground mt-1">
                  Simulates a parallel committee vote. Technical, Career Growth, Behavior, and Risk evaluators independently vote. Consensus is calculated with safety penalties subtracted for gaps or job-hopping risk.
                </p>
              </div>
            </div>
          </GlassCard>
        </div>

        {/* Committee FAQ */}
        <div className="space-y-6">
          <GlassCard className="p-6 space-y-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-accent-emerald" /> Recruiter Trust Checklist
            </h2>
            <div className="space-y-3 text-xs text-muted-foreground">
              <div className="p-2.5 rounded-lg bg-white/5 border border-white/5">
                <p className="font-semibold text-white">No Hallucinations</p>
                <p className="mt-0.5">Narrative explanations are assembled deterministically from raw profile facts. No generative LLM is used.</p>
              </div>
              <div className="p-2.5 rounded-lg bg-white/5 border border-white/5">
                <p className="font-semibold text-white">Offline Inference</p>
                <p className="mt-0.5">All indexing and retrieval runs locally. Candidate resumes never leave your secure system.</p>
              </div>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
};
