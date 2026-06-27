import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, User, ShieldAlert, Award, FileText, CheckCircle } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { ScoreBadge } from '../components/ui/ScoreBadge';
import { ConfidenceBadge } from '../components/ui/ConfidenceBadge';
import { RecommendationBadge } from '../components/ui/RecommendationBadge';
import { RiskBadge } from '../components/ui/RiskBadge';
import { GlassCard } from '../components/ui/GlassCard';
import { EvidenceLedger } from '../components/candidate/EvidenceLedger';
import { CouncilVoteCard } from '../components/candidate/CouncilVoteCard';
import { CareerTimeline } from '../components/charts/CareerTimeline';
import { GenomeRadar } from '../components/charts/GenomeRadar';
import { generateDemoData } from '../lib/demo';

export const CandidateDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { demoData, setDemoData, setCurrentJobId, setCurrentJobTitle } = useAppStore();

  const [activeTab, setActiveTab] = useState<'overview' | 'timeline' | 'genome' | 'evidence' | 'votes'>('overview');

  // Auto-init demo data so direct URL access works
  useEffect(() => {
    if (!demoData) {
      const data = generateDemoData();
      setDemoData(data);
      setCurrentJobId(data.jobProfile.job_id);
      setCurrentJobTitle(data.jobProfile.title);
    }
  }, [demoData, setDemoData, setCurrentJobId, setCurrentJobTitle]);

  const candidates = demoData?.rankedList.candidates || [];
  const candidate = candidates.find((c) => c.candidate_id === id);

  if (!candidate) {
    return (
      <div className="p-12 text-center">
        <h2 className="text-xl font-bold text-white">Candidate not found</h2>
        <button onClick={() => navigate('/candidates')} className="mt-4 btn-primary">
          Back to Explorer
        </button>
      </div>
    );
  }

  // Construct mock data for votes if not fully present
  const hasExplanation = !!(candidate.explanation?.strengths || candidate.explanation?.top_strengths);
  const votes = hasExplanation ? [
    { council_name: 'Technical Committee', score: candidate.overall_score * 1.05, confidence: 0.95, strengths: ['Exceptional coding capabilities', 'High tech alignment'], concerns: [] },
    { council_name: 'Career & Tenure', score: candidate.overall_score * 0.98, confidence: 0.9, strengths: ['Consistent job advancement', 'Stable career path'], concerns: ['Minor gap warning'] },
    { council_name: 'Hiring Committee', score: candidate.overall_score, confidence: 0.88, strengths: ['Strong overall profile matches ideal requirements'], concerns: [] },
  ] : [];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header Actions */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/candidates')}
          className="p-2 bg-white/5 border border-white/10 rounded-lg text-muted-foreground hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div>
          <span className="text-xs text-muted-foreground">Shortlist Context / Rank #{candidate.rank}</span>
          <h1 className="text-2xl font-bold tracking-tight text-white">{candidate.profile?.name || candidate.candidate_id}</h1>
        </div>
      </div>

      {/* Hero card */}
      <GlassCard className="p-6 grid grid-cols-1 md:grid-cols-4 gap-6 items-center">
        <div className="flex items-center gap-4 md:col-span-2">
          <div className="w-16 h-16 rounded-xl bg-gradient-primary flex items-center justify-center text-white text-2xl font-bold flex-shrink-0">
            {candidate.profile?.name ? candidate.profile.name.charAt(0) : 'U'}
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">{candidate.profile?.current_title || 'Software Engineer'}</h2>
            <p className="text-sm text-muted-foreground">{candidate.profile?.current_company || 'Tech Corp'} — {candidate.profile?.location || 'India'}</p>
            <p className="text-xs text-muted-foreground mt-1">{candidate.profile?.years_of_experience || 4} Years Experience</p>
          </div>
        </div>

        <div className="flex flex-col gap-2 md:border-l md:border-white/5 md:pl-6">
          <span className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Evaluation Score</span>
          <div className="flex items-center gap-2">
            <ScoreBadge score={candidate.overall_score} size="lg" />
            <ConfidenceBadge confidence={0.88} />
          </div>
        </div>

        <div className="flex flex-col gap-2 md:border-l md:border-white/5 md:pl-6">
          <span className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Shortlist Status</span>
          <div className="flex flex-wrap gap-2">
            <RecommendationBadge recommendation={candidate.recommendation || 'Pass'} />
            <RiskBadge risk={candidate.risk_level || 'Low'} />
          </div>
        </div>
      </GlassCard>

      {/* Tabs */}
      <div className="flex border-b border-white/10 gap-6">
        {(['overview', 'timeline', 'genome', 'evidence', 'votes'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3 text-sm font-semibold capitalize border-b-2 transition-all ${
              activeTab === tab
                ? 'border-accent text-accent'
                : 'border-transparent text-muted-foreground hover:text-white'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Panels */}
      <div className="space-y-6">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2 space-y-6">
              <GlassCard className="p-6 space-y-4">
                <h3 className="text-base font-bold text-white">Recruiter Narrative Summary</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {candidate.explanation?.hiring_narrative || 'Candidate matches core job requirements and presents a stable career timeline.'}
                </p>
              </GlassCard>

              <GlassCard className="p-6 space-y-4">
                <h3 className="text-base font-bold text-white">Strengths & Gaps</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 rounded-xl bg-accent-emerald/5 border border-accent-emerald/10 space-y-2">
                    <h4 className="text-sm font-semibold text-accent-emerald flex items-center gap-1.5">
                      <CheckCircle className="w-4 h-4" /> Top Strengths
                    </h4>
                    <ul className="text-xs text-muted-foreground space-y-2 list-disc pl-4">
                      {Array.isArray(candidate.explanation?.top_strengths) && candidate.explanation.top_strengths.length > 0
                        ? candidate.explanation.top_strengths.map((s, i) => <li key={i}>{s}</li>)
                        : <li>Strong technical expertise</li>
                      }
                    </ul>
                  </div>

                  <div className="p-4 rounded-xl bg-accent-rose/5 border border-accent-rose/10 space-y-2">
                    <h4 className="text-sm font-semibold text-accent-rose flex items-center gap-1.5">
                      <ShieldAlert className="w-4 h-4" /> Identified Gaps
                    </h4>
                    <ul className="text-xs text-muted-foreground space-y-2 list-disc pl-4">
                      {Array.isArray(candidate.explanation?.top_concerns) && candidate.explanation.top_concerns.length > 0
                        ? candidate.explanation.top_concerns.map((w, i) => <li key={i}>{w}</li>)
                        : <li>None identified</li>
                      }
                    </ul>
                  </div>
                </div>
              </GlassCard>
            </div>

            <div className="space-y-6">
              <GlassCard className="p-6 space-y-4">
                <h3 className="text-base font-bold text-white">Decision Guidelines</h3>
                <div className="text-xs text-muted-foreground space-y-3">
                  <p><strong>Rationale:</strong> {candidate.explanation?.narrative || candidate.explanation?.counterfactual || '—'}</p>
                  <p><strong>Risk Summary:</strong> {candidate.risk_level || 'Low'}</p>
                  <p><strong>Confidence:</strong> {((candidate.confidence_score ?? 0.88) * 100).toFixed(0)}%</p>
                </div>
              </GlassCard>
            </div>
          </div>
        )}

        {activeTab === 'timeline' && (
          <GlassCard className="p-6">
            <h3 className="text-base font-bold text-white mb-6">Career Timeline History</h3>
            <CareerTimeline
              candidateId={candidate.candidate_id}
              experience={candidate.profile?.work_experience || []}
            />
          </GlassCard>
        )}

        {activeTab === 'genome' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <GlassCard className="p-6 md:col-span-2 flex flex-col items-center justify-center">
              <h3 className="text-base font-bold text-white mb-6 w-full text-left">Multidimensional DNA Genome</h3>
              <div className="w-[300px] h-[300px]">
                <GenomeRadar
                  candidateId={candidate.candidate_id}
                  scores={[
                    candidate.features?.skill_coverage ?? candidate.genome_scores?.technical ?? 0.5,
                    candidate.features?.experience_score ?? candidate.genome_scores?.career ?? 0.5,
                    candidate.features?.domain_match ?? candidate.genome_scores?.domain ?? 0.5,
                    candidate.features?.leadership_score ?? candidate.genome_scores?.leadership ?? 0.5,
                    candidate.genome_scores?.learning ?? 0.5,
                    candidate.features?.stability_score ?? candidate.genome_scores?.stability ?? 0.5,
                    candidate.genome_scores?.behavioral ?? 0.5,
                    candidate.genome_scores?.readiness ?? 0.8,
                  ]}
                />
              </div>
            </GlassCard>

            <GlassCard className="p-6 space-y-4">
              <h3 className="text-base font-bold text-white">Genome Axes</h3>
                <div className="text-xs text-muted-foreground space-y-3">
                  <div className="flex justify-between border-b border-white/5 pb-1">
                    <span>Technical Capability</span>
                    <span className="font-semibold text-white">{((candidate.features?.skill_coverage ?? candidate.genome_scores?.technical ?? 0.5) * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between border-b border-white/5 pb-1">
                    <span>Career Progression</span>
                    <span className="font-semibold text-white">{((candidate.features?.experience_score ?? candidate.genome_scores?.career ?? 0.5) * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between border-b border-white/5 pb-1">
                    <span>Domain Expertise</span>
                    <span className="font-semibold text-white">{((candidate.features?.domain_match ?? candidate.genome_scores?.domain ?? 0.5) * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between border-b border-white/5 pb-1">
                    <span>Leadership Impact</span>
                    <span className="font-semibold text-white">{((candidate.features?.leadership_score ?? candidate.genome_scores?.leadership ?? 0.5) * 100).toFixed(0)}%</span>
                  </div>
                </div>
            </GlassCard>
          </div>
        )}

        {activeTab === 'evidence' && (
          <EvidenceLedger
            candidateId={candidate.candidate_id}
            evidence={
              candidate.explanation?.strengths ? {
                experience_evidence: candidate.explanation.strengths.map(s => s.description),
                skill_evidence: { 'Core Stack': candidate.profile?.skills || [] },
                learning_evidence: [],
                stability_evidence: [],
                leadership_evidence: [],
                behavior_evidence: [],
                risk_evidence: [],
                evidence_strength: 0.9,
              } : {
                experience_evidence: [],
                skill_evidence: {},
                learning_evidence: [],
                stability_evidence: [],
                leadership_evidence: [],
                behavior_evidence: [],
                risk_evidence: [],
                evidence_strength: 0.5,
              }
            }
          />
        )}

        {activeTab === 'votes' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {votes.map((vote, i) => (
              <CouncilVoteCard key={i} vote={vote} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
