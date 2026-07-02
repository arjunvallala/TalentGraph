import React, { useEffect } from 'react';
import { Sliders, Award, BrainCircuit, Globe, Landmark } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { GlassCard } from '../components/ui/GlassCard';
import { generateDemoData } from '../lib/demo';

export const JobIntelligencePage: React.FC = () => {
  const {
    demoData,
    setDemoData,
    currentJobId,
    setCurrentJobId,
    setCurrentJobTitle,
    isDemoMode,
    loadJobData
  } = useAppStore();

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

  const profile = demoData?.jobProfile;

  if (!profile) {
    return (
      <div className="p-12 text-center text-muted-foreground">
        Loading job intelligence...
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Job Intelligence</h1>
        <p className="text-sm text-muted-foreground">
          AI breakdown of explicit requirements and weight configurations
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Core Metadata */}
        <div className="space-y-6">
          <GlassCard className="p-6 space-y-4">
            <h2 className="text-base font-bold text-white">Position Details</h2>
            <div className="space-y-3 text-sm">
              <div>
                <p className="text-xs text-muted-foreground">Role Title</p>
                <p className="font-semibold text-white">{profile.title}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Seniority Expectations</p>
                <p className="font-semibold text-accent capitalize">{profile.seniority_level}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Ideal Target Experience</p>
                <p className="font-semibold text-white">{profile.min_experience_years}+ Years</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Primary Domain</p>
                <p className="font-semibold text-white capitalize">{profile.primary_domain || 'Generalist'}</p>
              </div>
            </div>
          </GlassCard>

          <GlassCard className="p-6 space-y-4">
            <h2 className="text-base font-bold text-white">Hidden Expectations</h2>
            <div className="space-y-2">
              <div className="flex gap-2.5 items-start p-2.5 rounded-lg bg-accent/5 border border-accent/10">
                <BrainCircuit className="w-4 h-4 text-accent mt-0.5 flex-shrink-0" />
                <p className="text-xs text-muted-foreground">
                  Expected to lead systems architecture discussions and mentor junior developers.
                </p>
              </div>
              <div className="flex gap-2.5 items-start p-2.5 rounded-lg bg-accent-emerald/5 border border-accent-emerald/10">
                <Globe className="w-4 h-4 text-accent-emerald mt-0.5 flex-shrink-0" />
                <p className="text-xs text-muted-foreground">
                  High familiarity with distributed system designs and asynchronous message brokers.
                </p>
              </div>
            </div>
          </GlassCard>
        </div>

        {/* Feature weights sliders */}
        <div className="md:col-span-2 space-y-6">
          <GlassCard className="p-6 space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Sliders className="w-4 h-4 text-accent" /> Active Weight Distribution
              </h2>
              <span className="text-xs text-muted-foreground">Feature ranking sliders</span>
            </div>

            <div className="space-y-4">
              <div className="space-y-1">
                <div className="flex justify-between text-xs text-white">
                  <span>Skill Coverage</span>
                  <span className="font-semibold">35%</span>
                </div>
                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full bg-accent w-[35%]" />
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-xs text-white">
                  <span>Domain Match</span>
                  <span className="font-semibold">20%</span>
                </div>
                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full bg-accent w-[20%]" />
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-xs text-white">
                  <span>Relevant Experience Length</span>
                  <span className="font-semibold">15%</span>
                </div>
                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full bg-accent w-[15%]" />
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-xs text-white">
                  <span>Leadership Credentials</span>
                  <span className="font-semibold">15%</span>
                </div>
                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full bg-accent-violet w-[15%]" />
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-xs text-white">
                  <span>Career Stability (Tenure)</span>
                  <span className="font-semibold">15%</span>
                </div>
                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full bg-accent-emerald w-[15%]" />
                </div>
              </div>
            </div>
          </GlassCard>

          {/* Explicit Skills list */}
          <GlassCard className="p-6 space-y-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Award className="w-4 h-4 text-accent" /> Explicit Required Skills
            </h2>
            <div className="flex flex-wrap gap-2">
               {profile.required_skills?.map((s) => {
                const skillName = typeof s === 'string' ? s : s?.skill || '';
                return (
                  <span
                    key={skillName}
                    className="px-2.5 py-1 text-xs font-semibold rounded-full bg-white/5 border border-white/10 text-white"
                  >
                    {skillName}
                  </span>
                );
              }) || <span className="text-xs text-muted-foreground">No explicit skills listed.</span>}
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
};
