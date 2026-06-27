import React from 'react';
import { Settings, Info, ShieldAlert, ToggleLeft, ToggleRight } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { GlassCard } from '../components/ui/GlassCard';

export const SettingsPage: React.FC = () => {
  const { isDemoMode, setDemoMode } = useAppStore();

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">System Settings</h1>
        <p className="text-sm text-muted-foreground">Configure thresholds, features, and model configurations</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Core settings toggle */}
        <div className="space-y-6">
          <GlassCard className="p-6 space-y-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Settings className="w-4 h-4 text-accent" /> Environment Settings
            </h2>

            <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5">
              <div>
                <p className="text-sm font-semibold text-white">Demo Mode</p>
                <p className="text-[10px] text-muted-foreground">Load pre-generated Indian tech shortlists instantly</p>
              </div>
              <button
                onClick={() => setDemoMode(!isDemoMode)}
                className="text-accent hover:text-white transition-colors"
              >
                {isDemoMode ? (
                  <ToggleRight className="w-9 h-9 text-accent" />
                ) : (
                  <ToggleLeft className="w-9 h-9 text-muted" />
                )}
              </button>
            </div>
          </GlassCard>
        </div>

        {/* Weights and limits */}
        <div className="md:col-span-2 space-y-6">
          <GlassCard className="p-6 space-y-6">
            <h2 className="text-base font-bold text-white">Consensus recommendation Thresholds</h2>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                <div>
                  <p className="font-semibold text-white">Strong Hire</p>
                  <p className="text-[10px] text-muted-foreground">Recommended for immediate hire status</p>
                </div>
                <span className="font-bold text-accent-emerald">Score ≥ 82%</span>
              </div>

              <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                <div>
                  <p className="font-semibold text-white">Hire</p>
                  <p className="text-[10px] text-muted-foreground">Candidate matches all core competencies</p>
                </div>
                <span className="font-bold text-accent animate-pulse">Score ≥ 68%</span>
              </div>

              <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                <div>
                  <p className="font-semibold text-white">Consider</p>
                  <p className="text-[10px] text-muted-foreground">Further interview panel checks advised</p>
                </div>
                <span className="font-bold text-accent-violet">Score ≥ 52%</span>
              </div>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
};
