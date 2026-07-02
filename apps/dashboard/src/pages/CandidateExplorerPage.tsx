import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, SlidersHorizontal, ChevronLeft, ChevronRight, Eye } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { ScoreBadge } from '../components/ui/ScoreBadge';
import { ConfidenceBadge } from '../components/ui/ConfidenceBadge';
import { RecommendationBadge } from '../components/ui/RecommendationBadge';
import { RiskBadge } from '../components/ui/RiskBadge';
import { GlassCard } from '../components/ui/GlassCard';
import { generateDemoData } from '../lib/demo';

export const CandidateExplorerPage: React.FC = () => {
  const {
    demoData,
    setDemoData,
    currentJobId,
    setCurrentJobId,
    setCurrentJobTitle,
    isDemoMode,
    loadJobData,
    setSelectedCandidateId
  } = useAppStore();
  const navigate = useNavigate();

  const [searchTerm, setSearchTerm] = useState('');
  const [filterRec, setFilterRec] = useState('all');
  const [filterRisk, setFilterRisk] = useState('all');

  // Auto-init demo data if not loaded
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

  const candidates = demoData?.rankedList.candidates || [];

  // Filter candidates
  const filtered = candidates.filter((c) => {
    const nameMatch = (c.profile?.name || '').toLowerCase().includes(searchTerm.toLowerCase());
    const titleMatch = (c.profile?.current_title || '').toLowerCase().includes(searchTerm.toLowerCase());
    const matchSearch = nameMatch || titleMatch;

    const matchRec = filterRec === 'all' || c.recommendation === filterRec;
    const matchRisk = filterRisk === 'all' || (c.risk_level || '').toLowerCase() === filterRisk.toLowerCase();

    return matchSearch && matchRec && matchRisk;
  });

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Candidate Explorer</h1>
          <p className="text-sm text-muted-foreground">Search and filter through the ranked shortlist</p>
        </div>
      </div>

      {/* Filters Bar */}
      <GlassCard className="p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search candidate name or title..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-sm bg-surface-2 border border-white/10 rounded-lg focus:outline-none focus:border-accent text-white"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Recommendation:</span>
            <select
              value={filterRec}
              onChange={(e) => setFilterRec(e.target.value)}
              className="bg-surface-2 border border-white/10 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-accent text-white"
            >
              <option value="all">All Recommendations</option>
              <option value="Strong Hire">Strong Hire</option>
              <option value="Hire">Hire</option>
              <option value="Consider">Consider</option>
              <option value="Pass">Pass</option>
              <option value="Reject">Reject</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Risk Level:</span>
            <select
              value={filterRisk}
              onChange={(e) => setFilterRisk(e.target.value)}
              className="bg-surface-2 border border-white/10 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-accent text-white"
            >
              <option value="all">All Risks</option>
              <option value="low">Low Risk</option>
              <option value="medium">Medium Risk</option>
              <option value="high">High Risk</option>
            </select>
          </div>
        </div>
      </GlassCard>

      {/* Table */}
      <GlassCard className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/5 bg-white/[0.02] text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                <th className="px-6 py-4">Rank</th>
                <th className="px-6 py-4">Candidate</th>
                <th className="px-6 py-4">Overall Score</th>
                <th className="px-6 py-4">Confidence</th>
                <th className="px-6 py-4">Recommendation</th>
                <th className="px-6 py-4">Risk Level</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-sm">
              {filtered.map((c) => (
                <tr key={c.candidate_id} className="hover:bg-white/[0.01] transition-colors">
                  <td className="px-6 py-4 font-bold text-accent">#{c.rank}</td>
                  <td className="px-6 py-4">
                    <div>
                      <p className="font-semibold text-white">{c.profile?.name || c.candidate_id}</p>
                      <p className="text-xs text-muted-foreground">
                        {c.profile?.current_title || 'Software Engineer'} at {c.profile?.current_company || 'Tech Corp'}
                      </p>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <ScoreBadge score={c.overall_score} />
                  </td>
                  <td className="px-6 py-4">
                    <ConfidenceBadge confidence={c.confidence_score ?? 0.7} />
                  </td>
                  <td className="px-6 py-4">
                    <RecommendationBadge recommendation={c.recommendation} />
                  </td>
                  <td className="px-6 py-4">
                    <RiskBadge risk={c.risk_level || (c.overall_score > 0.7 ? 'Low' : 'Medium')} />
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => {
                        setSelectedCandidateId(c.candidate_id);
                        navigate(`/candidates/${c.candidate_id}`);
                      }}
                      className="inline-flex items-center gap-1.5 text-xs text-accent hover:text-white bg-accent/10 border border-accent/20 px-3 py-1.5 rounded-lg transition-all"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      View Profile
                    </button>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-muted-foreground">
                    No candidates found matching the filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </GlassCard>
    </div>
  );
};
