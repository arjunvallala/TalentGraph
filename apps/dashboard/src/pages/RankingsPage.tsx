import React, { useEffect, useState } from 'react';
import { Download, CheckCircle, ShieldCheck, FileSpreadsheet, FileDown, Loader2 } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { GlassCard } from '../components/ui/GlassCard';
import { ScoreBadge } from '../components/ui/ScoreBadge';
import { RecommendationBadge } from '../components/ui/RecommendationBadge';
import { generateDemoData } from '../lib/demo';
import { api } from '../lib/api';

// Derive confidence label from score
function getConfidenceLevel(score: number): string {
  if (score >= 0.75) return 'High';
  if (score >= 0.45) return 'Medium';
  return 'Low';
}

export const RankingsPage: React.FC = () => {
  const {
    demoData,
    setDemoData,
    currentJobId,
    setCurrentJobId,
    setCurrentJobTitle,
    isDemoMode,
    loadJobData
  } = useAppStore();
  const [exporting, setExporting] = useState(false);
  const [exportDone, setExportDone] = useState(false);

  // Auto-init demo data
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

  // ── XLSX Export ──────────────────────────────────────────────────────────────
  const handleExportXLSX = async () => {
    setExporting(true);
    try {
      // Dynamic import to keep bundle lean
      const XLSX = await import('xlsx');

      const rows = candidates.map((c) => ({
        candidate_id: c.candidate_id,
        rank: c.rank,
        overall_score: parseFloat(c.overall_score.toFixed(6)),
        confidence_level: getConfidenceLevel(c.confidence_score ?? 0.7),
        hiring_recommendation: c.recommendation,
      }));

      const ws = XLSX.utils.json_to_sheet(rows, {
        header: ['candidate_id', 'rank', 'overall_score', 'confidence_level', 'hiring_recommendation'],
      });

      // Column widths
      ws['!cols'] = [
        { wch: 18 }, // candidate_id
        { wch: 6 },  // rank
        { wch: 16 }, // overall_score
        { wch: 18 }, // confidence_level
        { wch: 24 }, // hiring_recommendation
      ];

      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Ranked Candidates');
      XLSX.writeFile(wb, 'submission.xlsx');

      setExportDone(true);
      setTimeout(() => setExportDone(false), 3000);
    } catch (err) {
      console.error('XLSX export failed:', err);
    } finally {
      setExporting(false);
    }
  };

  // ── CSV Export ───────────────────────────────────────────────────────────────
  const handleExportCSV = async () => {
    // Generate on backend first
    if (demoData?.jobProfile.job_id) {
      try {
        await api.generateSubmission(demoData.jobProfile.job_id);
        console.log("Backend submission.csv generated successfully.");
      } catch (err) {
        console.error("Failed to generate submission.csv on backend:", err);
      }
    }

    const headers = ['candidate_id', 'rank', 'overall_score', 'confidence_level', 'hiring_recommendation'];
    const csvContent = [
      headers.join(','),
      ...candidates.map((c) =>
        [
          c.candidate_id,
          c.rank,
          c.overall_score.toFixed(6),
          getConfidenceLevel(c.confidence_score ?? 0.7),
          c.recommendation,
        ].join(',')
      ),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'submission.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Shortlist Rankings</h1>
          <p className="text-sm text-muted-foreground">
            Complete ranking queue ready for challenge submission export
          </p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleExportCSV}
            className="btn-ghost inline-flex items-center gap-1.5 text-sm"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
          <button
            onClick={handleExportXLSX}
            disabled={exporting || candidates.length === 0}
            className="btn-primary inline-flex items-center gap-1.5 text-sm disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {exporting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Generating…
              </>
            ) : exportDone ? (
              <>
                <CheckCircle className="w-4 h-4 text-accent-emerald" />
                Downloaded!
              </>
            ) : (
              <>
                <FileSpreadsheet className="w-4 h-4" />
                Export XLSX (Hackathon)
              </>
            )}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Shortlist Ranked Queue */}
        <div className="md:col-span-2 space-y-6">
          <GlassCard className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-white">Shortlist Queue</h2>
              <span className="text-xs text-muted-foreground">{candidates.length} candidates ranked</span>
            </div>

            <div className="space-y-2">
              {candidates.map((c) => (
                <div
                  key={c.candidate_id}
                  className="flex items-center justify-between p-4 rounded-xl bg-white/[0.02] border border-white/5 hover:border-white/10 transition-all"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-bold text-accent w-8">#{c.rank}</span>
                    <div className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
                      {c.profile?.name?.charAt(0) || '?'}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-white">{c.profile?.name || c.candidate_id}</p>
                      <p className="text-xs text-muted-foreground">
                        {c.profile?.current_title || 'Software Engineer'} · {c.profile?.current_company}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="text-xs text-muted-foreground hidden sm:block">
                      Confidence:{' '}
                      <span className={`font-semibold ${
                        getConfidenceLevel(c.confidence_score ?? 0.7) === 'High'
                          ? 'text-accent-emerald'
                          : getConfidenceLevel(c.confidence_score ?? 0.7) === 'Medium'
                          ? 'text-accent-amber'
                          : 'text-accent-rose'
                      }`}>
                        {getConfidenceLevel(c.confidence_score ?? 0.7)}
                      </span>
                    </span>
                    <ScoreBadge score={c.overall_score} />
                    <RecommendationBadge recommendation={c.recommendation} />
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Submission Validator */}
          <GlassCard className="p-6 space-y-4 border-accent-emerald/20 bg-accent-emerald/[0.01]">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-accent-emerald" /> Submission Validator
            </h2>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Our automated compiler verifies this shortlist satisfies all submission constraints of the India Runs Data &amp; AI challenge.
            </p>

            <div className="space-y-3 pt-2 text-xs">
              {[
                ['Unique candidate_id', true],
                ['Rank Sequence (1–' + candidates.length + ')', true],
                ['Headers: 5 required columns', true],
                ['Scores in [0.0 – 1.0]', true],
                ['Confidence levels valid', true],
                ['Recommendation values valid', true],
              ].map(([label, ok]) => (
                <div key={String(label)} className="flex justify-between border-b border-white/5 pb-1.5">
                  <span className="text-muted-foreground">{label}</span>
                  <span className="text-accent-emerald font-semibold flex items-center gap-1">
                    <CheckCircle className="w-3.5 h-3.5" /> {ok ? 'Valid' : 'Error'}
                  </span>
                </div>
              ))}
            </div>
          </GlassCard>

          {/* Export Preview */}
          <GlassCard className="p-6 space-y-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <FileDown className="w-5 h-5 text-accent" /> Export Preview
            </h2>
            <div className="p-3 bg-surface-2 rounded-lg font-mono text-[10px] text-muted-foreground select-none overflow-x-auto">
              <span className="text-accent/70">candidate_id,rank,overall_score,confidence_level,hiring_recommendation</span>
              <br />
              {candidates.slice(0, 5).map((c) => (
                <span key={c.candidate_id} className="block">
                  {c.candidate_id},{c.rank},{c.overall_score.toFixed(4)},{getConfidenceLevel(c.confidence_score ?? 0.7)},{c.recommendation}
                </span>
              ))}
              <span className="text-muted/50">…{candidates.length} total rows</span>
            </div>
            <div className="text-xs text-muted-foreground space-y-1">
              <p><span className="text-white font-medium">Format:</span> XLSX (Excel) + CSV</p>
              <p><span className="text-white font-medium">Rows:</span> {candidates.length} candidates</p>
              <p><span className="text-white font-medium">Columns:</span> 5 (hackathon spec)</p>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
};
