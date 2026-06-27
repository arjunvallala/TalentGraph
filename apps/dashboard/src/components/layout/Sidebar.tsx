import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  Users,
  Brain,
  Trophy,
  BarChart3,
  Lightbulb,
  Settings,
  Zap,
  ChevronRight,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useAppStore } from '../../store/appStore';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/candidates', icon: Users, label: 'Candidates' },
  { path: '/job-intelligence', icon: Brain, label: 'Job Intelligence' },
  { path: '/rankings', icon: Trophy, label: 'Rankings' },
  { path: '/analytics', icon: BarChart3, label: 'Analytics' },
  { path: '/explainability', icon: Lightbulb, label: 'Explainability' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

export const Sidebar: React.FC = () => {
  const { isDemoMode } = useAppStore();
  const location = useLocation();

  return (
    <aside className="w-[240px] flex-shrink-0 h-full flex flex-col border-r border-white/[0.06] bg-surface">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-white/[0.06]">
        <div className="w-8 h-8 rounded-lg bg-gradient-primary flex items-center justify-center shadow-glow-blue flex-shrink-0">
          <Zap className="w-4 h-4 text-white" />
        </div>
        <div>
          <p className="text-sm font-bold text-white leading-none">TalentGraph</p>
          <p className="text-xs text-accent leading-none mt-0.5">AI Recruiter</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-0.5">
        {navItems.map((item) => {
          const isActive = item.path === '/'
            ? location.pathname === '/'
            : location.pathname.startsWith(item.path);

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={cn(
                'nav-item',
                isActive && 'nav-item-active'
              )}
            >
              <item.icon className={cn('w-4 h-4 flex-shrink-0', isActive ? 'text-accent' : '')} />
              <span>{item.label}</span>
              {isActive && (
                <ChevronRight className="w-3 h-3 ml-auto text-accent/60" />
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Demo mode badge */}
      {isDemoMode && (
        <div className="mx-3 mb-4 p-3 rounded-xl bg-accent-violet/10 border border-accent-violet/20">
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full bg-accent-violet animate-pulse-slow" />
            <p className="text-xs font-semibold text-accent-violet">Demo Mode</p>
          </div>
          <p className="text-xs text-muted-foreground">
            Using synthetic data. Connect your backend to go live.
          </p>
        </div>
      )}

      {/* Version footer */}
      <div className="px-5 py-3 border-t border-white/[0.06]">
        <p className="text-xs text-muted">TalentGraph AI v1.0.0</p>
      </div>
    </aside>
  );
};
