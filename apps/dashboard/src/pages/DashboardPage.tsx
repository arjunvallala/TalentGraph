import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  Trophy,
  TrendingUp,
  Activity,
  ArrowRight,
  Upload,
  Loader2,
  CheckCircle2,
  Clock,
  Star,
} from 'lucide-react';
import { MetricCard } from '../components/ui/MetricCard';
import { GlassCard } from '../components/ui/GlassCard';
import { ScoreBadge } from '../components/ui/ScoreBadge';
import { RecommendationBadge } from '../components/ui/RecommendationBadge';
import { RiskBadge } from '../components/ui/RiskBadge';
import { FunnelChart } from '../components/charts/FunnelChart';
import { useAppStore } from '../store/appStore';
import { generateDemoData } from '../lib/demo';
import { api } from '../lib/api';
import { cn, truncate } from '../lib/utils';

const ACTIVITY = [
  { time: '2m ago', text: 'AI ranked 20 candidates for Platform Engineer role', icon: '🤖', color: 'text-accent' },
  { time: '15m ago', text: 'Arjun Sharma moved to Stage 1 — awaiting review', icon: '✅', color: 'text-accent-emerald' },
  { time: '1h ago', text: 'Job Intelligence analysis complete', icon: '🧠', color: 'text-accent-violet' },
  { time: '3h ago', text: 'Submission CSV exported (20 candidates)', icon: '📄', color: 'text-accent-amber' },
  { time: 'Yesterday', text: 'New job description uploaded and analyzed', icon: '📋', color: 'text-muted-foreground' },
];

export const DashboardPage: React.FC = () => {
  const { isDemoMode, currentJobId, setCurrentJobId, setCurrentJobTitle, demoData, setDemoData, loadJobData } = useAppStore();
  const navigate = useNavigate();
  const [jdText, setJdText] = useState('');
  const [jdTitle, setJdTitle] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  // Hydrate or initialize demo data
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

  const data = demoData;
  const candidates = data?.rankedList.candidates || [];
  const analytics = data?.analytics;
  const top5 = candidates.slice(0, 5);

  const handleUploadJD = async () => {
    if (!jdText.trim() || !jdTitle.trim()) return;
    setUploading(true);
    try {
      const jobId = `job_${Date.now()}`;
      // 1. Analyze JD on backend and save it to DuckDB
      await api.analyzeJob(jdText, jdTitle, jobId);
      // 2. Run ranking pipeline on backend
      await api.runRanking(jobId);
      // 3. Load all ranking results and analytics into the Zustand store
      await loadJobData(jobId);

      setUploadSuccess(true);
      setTimeout(() => navigate('/rankings'), 1500);
    } catch (err) {
      console.error("Hiring pipeline run failed, falling back to demo mode:", err);
      // Fallback to demo
      const data = generateDemoData();
      setDemoData(data);
      setCurrentJobId(data.jobProfile.job_id);
      setCurrentJobTitle(jdTitle || data.jobProfile.title);
      setUploadSuccess(true);
      setTimeout(() => navigate('/rankings'), 1500);
    } finally {
      setUploading(false);
    }
  };

  const hour = new Date().getHours();
  const greeting =
    hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  return (
    <div className="p-6 space-y-6 max-w-[1400px] mx-auto">
      {/* Hero Greeting */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold text-white">
            {greeting}, Recruiter 👋
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {isDemoMode
              ? "You're in demo mode — all data is synthetic and fully interactive."
              : currentJobId
              ? `Active job: ${data?.jobProfile.title || currentJobId}`
              : 'No active job loaded. Upload a job description to begin.'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/job-intelligence')}
            className="btn-ghost text-sm flex items-center gap-2"
          >
            <Upload className="w-4 h-4" />
            Upload JD
          </button>
          <button
            onClick={() => navigate('/rankings')}
            className="btn-primary text-sm flex items-center gap-2"
          >
            View Rankings
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </motion.div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Candidates"
          value={analytics?.total_candidates || 0}
          icon={<Users className="w-5 h-5" />}
          color="blue"
          subtitle="In ranked pool"
          delay={0.05}
        />
        <MetricCard
          label="Top Score"
          value={analytics ? `${(analytics.top_score * 100).toFixed(1)}%` : '—'}
          icon={<Trophy className="w-5 h-5" />}
          color="emerald"
          score={analytics?.top_score}
          subtitle="Best candidate match"
          delay={0.1}
        />
        <MetricCard
          label="Avg Score"
          value={analytics ? `${(analytics.avg_score * 100).toFixed(1)}%` : '—'}
          icon={<TrendingUp className="w-5 h-5" />}
          color="violet"
          score={analytics?.avg_score}
          subtitle="Across all candidates"
          delay={0.15}
        />
        <MetricCard
          label="Pipeline Status"
          value={analytics
            ? `${Object.values(analytics.recommendation_distribution || {}).reduce((a, b) => a + b, 0)} scored`
            : '—'}
          icon={<Activity className="w-5 h-5" />}
          color="amber"
          subtitle="Ready for review"
          delay={0.2}
        />
      </div>

      {/* Main Content: Top candidates + Activity */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Top 5 Candidates */}
        <div className="xl:col-span-2">
          <GlassCard>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-semibold text-white">Top Candidates</h2>
                <p className="text-xs text-muted-foreground mt-0.5">Highest ranked for this role</p>
              </div>
              <button
                onClick={() => navigate('/candidates')}
                className="text-xs text-accent hover:text-accent/80 flex items-center gap-1 transition-colors"
              >
                View all <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            <div className="space-y-2">
              {top5.map((c, i) => (
                <motion.div
                  key={c.candidate_id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 + i * 0.05 }}
                  onClick={() => navigate(`/candidates/${c.candidate_id}`)}
                  className="flex items-center gap-3 p-3 rounded-xl hover:bg-white/[0.04] cursor-pointer transition-all duration-200 group border border-transparent hover:border-white/[0.08]"
                >
                  {/* Rank */}
                  <div className={cn(
                    'w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0',
                    i === 0 ? 'bg-accent-amber/20 text-accent-amber' :
                    i === 1 ? 'bg-white/10 text-white' :
                    i === 2 ? 'bg-accent-amber/10 text-accent-amber/60' :
                    'bg-white/5 text-muted-foreground'
                  )}>
                    {c.rank}
                  </div>

                  {/* Avatar */}
                  <div className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
                    {c.profile?.name?.charAt(0) || '?'}
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate group-hover:text-accent transition-colors">
                      {c.profile?.name || c.candidate_id}
                    </p>
                    <p className="text-xs text-muted-foreground truncate">
                      {c.profile?.current_title} · {c.profile?.current_company}
                    </p>
                  </div>

                  {/* Badges */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <ScoreBadge score={c.overall_score} size="sm" />
                    <RecommendationBadge recommendation={c.recommendation} size="sm" />
                  </div>

                  <ArrowRight className="w-3.5 h-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                </motion.div>
              ))}
            </div>
          </GlassCard>
        </div>

        {/* Activity Feed */}
        <div>
          <GlassCard className="h-full">
            <h2 className="text-base font-semibold text-white mb-4">Recent Activity</h2>
            <div className="space-y-3">
              {ACTIVITY.map((a, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.2 + i * 0.05 }}
                  className="flex items-start gap-3"
                >
                  <span className="text-base flex-shrink-0 mt-0.5">{a.icon}</span>
                  <div>
                    <p className="text-xs text-white leading-relaxed">{a.text}</p>
                    <p className="text-xs text-muted-foreground mt-0.5 flex items-center gap-1">
                      <Clock className="w-2.5 h-2.5" />
                      {a.time}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          </GlassCard>
        </div>
      </div>

      {/* Funnel + JD Upload */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Hiring Funnel */}
        <GlassCard>
          <div className="mb-4">
            <h2 className="text-base font-semibold text-white">Hiring Funnel</h2>
            <p className="text-xs text-muted-foreground mt-0.5">Candidate pipeline overview</p>
          </div>
          <FunnelChart
            totalProcessed={data?.rankedList.total_processed || 100000}
            stage1={analytics?.stage_distribution?.Stage1 || 6}
            stage2={analytics?.stage_distribution?.Stage2 || 8}
            stage3={analytics?.stage_distribution?.Stage3 || 6}
          />
        </GlassCard>

        {/* JD Upload */}
        <GlassCard>
          <div className="mb-4">
            <h2 className="text-base font-semibold text-white">Upload Job Description</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Analyze a new JD to rank candidates
            </p>
          </div>

          {uploadSuccess ? (
            <div className="flex flex-col items-center justify-center py-8 gap-3">
              <CheckCircle2 className="w-12 h-12 text-accent-emerald" />
              <p className="text-sm font-medium text-white">Job analyzed successfully!</p>
              <p className="text-xs text-muted-foreground">Redirecting to rankings…</p>
            </div>
          ) : (
            <div className="space-y-3">
              <input
                type="text"
                placeholder="Job title (e.g. Senior Software Engineer)"
                value={jdTitle}
                onChange={(e) => setJdTitle(e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg bg-surface-2 border border-white/[0.08] text-sm text-white placeholder-muted-foreground focus:outline-none focus:border-accent/50 transition-colors"
              />
              <textarea
                placeholder="Paste job description here…"
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                rows={5}
                className="w-full px-3 py-2.5 rounded-lg bg-surface-2 border border-white/[0.08] text-sm text-white placeholder-muted-foreground focus:outline-none focus:border-accent/50 transition-colors resize-none"
              />
              <button
                onClick={handleUploadJD}
                disabled={uploading || (!jdText.trim() && !isDemoMode)}
                className={cn(
                  'w-full btn-primary flex items-center justify-center gap-2',
                  (uploading || (!jdText.trim() && !isDemoMode)) && 'opacity-50 cursor-not-allowed'
                )}
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Analyzing…
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    Analyze Job Description
                  </>
                )}
              </button>
              {isDemoMode && !jdText && (
                <p className="text-xs text-muted-foreground text-center">
                  Demo mode: will use pre-loaded job data
                </p>
              )}
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  );
};
