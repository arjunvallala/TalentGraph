import React, { useEffect } from 'react';
import { BarChart3, PieChart, TrendingUp, Info } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { GlassCard } from '../components/ui/GlassCard';
import { FunnelChart } from '../components/charts/FunnelChart';
import { FeatureImportanceChart } from '../components/charts/FeatureImportanceChart';
import { RiskDonut } from '../components/charts/RiskDonut';
import { ScoreDistribution } from '../components/charts/ScoreDistribution';
import { generateDemoData } from '../lib/demo';

export const AnalyticsPage: React.FC = () => {
  const {
    demoData,
    setDemoData,
    currentJobId,
    setCurrentJobId,
    setCurrentJobTitle,
    isDemoMode,
    loadJobData
  } = useAppStore();

  // Auto-init demo data so Analytics always shows
  useEffect(() => {
    if (!demoData) {
      if (!isDemoMode && currentJobId) {
        loadJobData(currentJobId).catch((err) => {
          console.error("Failed to restore active job from backend:", err);
          const data = generateDemoData();
          setDemoData(data);
          setCurrentJobId(data.jobProfile.job_id);
          setCurrentJobTitle(data.jobProfile.title);
        });
      } else {
        const data = generateDemoData();
        setDemoData(data);
        setCurrentJobId(data.jobProfile.job_id);
        setCurrentJobTitle(data.jobProfile.title);
      }
    }
  }, [demoData, isDemoMode, currentJobId, loadJobData, setDemoData, setCurrentJobId, setCurrentJobTitle]);

  const analytics = demoData?.analytics;

  if (!analytics) {
    return (
      <div className="p-12 text-center text-muted-foreground">
        Loading analytics...
      </div>
    );
  }

  // Construct mock lists for display
  const topSkills = ['Python', 'Django', 'React', 'FastAPI', 'Docker', 'PostgreSQL'];
  const skillGaps = ['Kubernetes', 'Apache Kafka', 'Terraform', 'gRPC'];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">shortlist Analytics</h1>
        <p className="text-sm text-muted-foreground">
          Detailed metrics across the retrieved candidate pool
        </p>
      </div>

      {/* Grid Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Funnel Waterfall */}
        <GlassCard className="p-6 flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-white mb-1">Hiring Funnel Conversion</h2>
            <p className="text-xs text-muted-foreground mb-6">Drop-offs across Stage 1, 2, and 3 filter gates</p>
          </div>
          <div className="h-[250px] w-full flex items-center justify-center">
            <FunnelChart
              data={[
                { stage: 'Corpus Ingest', count: 10000 },
                { stage: 'Stage 1 Hybrid', count: 2000 },
                { stage: 'Stage 2 Feature', count: 200 },
                { stage: 'Stage 3 Council', count: 100 },
              ]}
            />
          </div>
        </GlassCard>

        {/* Feature Importance */}
        <GlassCard className="p-6 flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-white mb-1">Feature Contribution Weights</h2>
            <p className="text-xs text-muted-foreground mb-6">Relative contribution of features to ranking scores</p>
          </div>
          <div className="h-[250px] w-full flex items-center justify-center">
            <FeatureImportanceChart
              features={[
                { name: 'Skill Coverage', importance: 0.35 },
                { name: 'Domain Match', importance: 0.20 },
                { name: 'Relevant Experience', importance: 0.15 },
                { name: 'Stability', importance: 0.15 },
                { name: 'Availability', importance: 0.15 },
              ]}
            />
          </div>
        </GlassCard>

        {/* Score Distribution */}
        <GlassCard className="p-6 flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-white mb-1">Overall Score Distribution</h2>
            <p className="text-xs text-muted-foreground mb-6">Distribution histogram of candidate scores</p>
          </div>
          <div className="h-[250px] w-full flex items-center justify-center">
            <ScoreDistribution
              data={[
                { bucket: '90-100%', count: 4 },
                { bucket: '80-90%', count: 12 },
                { bucket: '70-80%', count: 25 },
                { bucket: '65-70%', count: 32 },
                { bucket: '60-65%', count: 27 },
              ]}
            />
          </div>
        </GlassCard>

        {/* Risk Breakdown */}
        <GlassCard className="p-6 flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-white mb-1">Hiring Risk Breakdown</h2>
            <p className="text-xs text-muted-foreground mb-6">Overall risk classification ratios</p>
          </div>
          <div className="h-[250px] w-full flex items-center justify-center">
            <RiskDonut
              data={[
                { label: 'Low Risk', value: 75, color: '#10b981' },
                { label: 'Medium Risk', value: 20, color: '#f59e0b' },
                { label: 'High Risk', value: 5, color: '#f43f5e' },
              ]}
            />
          </div>
        </GlassCard>
      </div>

      {/* Skills insights */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <GlassCard className="p-6 space-y-4">
          <h2 className="text-sm font-bold text-white">Dominant Skills (Top Shortlist)</h2>
          <div className="flex flex-wrap gap-2">
            {topSkills.map((s) => (
              <span key={s} className="px-2.5 py-1 text-xs rounded-full bg-accent/10 border border-accent/20 text-accent">
                {s}
              </span>
            ))}
          </div>
        </GlassCard>

        <GlassCard className="p-6 space-y-4">
          <h2 className="text-sm font-bold text-white">Identified Talent Gaps</h2>
          <div className="flex flex-wrap gap-2">
            {skillGaps.map((s) => (
              <span key={s} className="px-2.5 py-1 text-xs rounded-full bg-accent-rose/10 border border-accent-rose/20 text-accent-rose">
                {s}
              </span>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  );
};
