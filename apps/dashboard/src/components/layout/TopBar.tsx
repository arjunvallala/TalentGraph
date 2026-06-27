import React from 'react';
import { Zap, Search, Bell } from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { cn } from '../../lib/utils';

export const TopBar: React.FC = () => {
  const { currentJobTitle, isDemoMode } = useAppStore();

  return (
    <header className="h-[60px] flex-shrink-0 flex items-center justify-between px-6 border-b border-white/[0.06] bg-surface/80 backdrop-blur-sm">
      {/* Left: Job context */}
      <div className="flex items-center gap-3">
        {currentJobTitle ? (
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Active Job:</span>
            <span className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/20 text-xs font-medium text-accent">
              {currentJobTitle}
            </span>
          </div>
        ) : (
          <span className="text-xs text-muted-foreground">No active job — load a job to get started</span>
        )}
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-3">
        {isDemoMode && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-accent-violet/10 border border-accent-violet/20">
            <span className="w-1.5 h-1.5 rounded-full bg-accent-violet animate-pulse" />
            <span className="text-xs font-medium text-accent-violet">Demo</span>
          </div>
        )}
        <button className="w-8 h-8 rounded-lg hover:bg-white/5 flex items-center justify-center text-muted-foreground hover:text-white transition-colors">
          <Search className="w-4 h-4" />
        </button>
        <button className="w-8 h-8 rounded-lg hover:bg-white/5 flex items-center justify-center text-muted-foreground hover:text-white transition-colors relative">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-accent-rose" />
        </button>
        <div className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center text-xs font-bold text-white">
          R
        </div>
      </div>
    </header>
  );
};
