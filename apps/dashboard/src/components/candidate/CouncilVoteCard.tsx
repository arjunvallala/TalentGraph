import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronUp } from 'lucide-react';
import type { CouncilVote } from '../../lib/api';
import { cn, getScoreBarColor, getConfidenceLabel, getConfidenceColor } from '../../lib/utils';

interface CouncilVoteCardProps {
  vote: CouncilVote;
  delay?: number;
}

const COUNCIL_ICONS: Record<string, string> = {
  'Technical Depth Council': '🔬',
  'Career Trajectory Council': '📈',
  'Domain Expertise Council': '🎯',
  'Leadership & Impact Council': '🚀',
  'Culture Fit Council': '🤝',
};

export const CouncilVoteCard: React.FC<CouncilVoteCardProps> = ({ vote, delay = 0 }) => {
  const [expanded, setExpanded] = useState(false);
  const icon = COUNCIL_ICONS[vote.council_name] || '⚖️';
  const barColor = getScoreBarColor(vote.score);
  const confColor = getConfidenceColor(vote.confidence);
  const confLabel = getConfidenceLabel(vote.confidence);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className="glass-card p-4 hover:border-white/[0.15] transition-all duration-300"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <span className="text-xl">{icon}</span>
          <div>
            <p className="text-sm font-semibold text-white">{vote.council_name}</p>
            <p className={cn('text-xs font-medium flex items-center gap-1', confColor)}>
              <span className={cn('w-1.5 h-1.5 rounded-full', 
                vote.confidence >= 0.75 ? 'bg-accent-emerald' : 
                vote.confidence >= 0.5 ? 'bg-accent-amber' : 'bg-accent-rose'
              )} />
              {confLabel} Confidence
            </p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-lg font-bold text-white">{(vote.score * 100).toFixed(0)}</p>
          <p className="text-xs text-muted-foreground">/ 100</p>
        </div>
      </div>

      {/* Score bar */}
      <div className="score-bar mb-3">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${vote.score * 100}%` }}
          transition={{ duration: 0.7, delay: delay + 0.1, ease: 'easeOut' }}
          className={cn('score-bar-fill', barColor)}
        />
      </div>

      {/* Expand toggle */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-xs text-muted-foreground hover:text-white transition-colors"
      >
        {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        {expanded ? 'Hide details' : 'Show details'}
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="mt-3 space-y-3 pt-3 border-t border-white/[0.06]">
              {vote.strengths && vote.strengths.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-accent-emerald mb-1.5 uppercase tracking-wider">
                    Strengths
                  </p>
                  <ul className="space-y-1">
                    {vote.strengths.map((s, i) => (
                      <li key={i} className="text-xs text-muted-foreground flex items-start gap-1.5">
                        <span className="text-accent-emerald mt-0.5">✓</span>
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {vote.concerns && vote.concerns.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-accent-amber mb-1.5 uppercase tracking-wider">
                    Concerns
                  </p>
                  <ul className="space-y-1">
                    {vote.concerns.map((c, i) => (
                      <li key={i} className="text-xs text-muted-foreground flex items-start gap-1.5">
                        <span className="text-accent-amber mt-0.5">!</span>
                        {c}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {vote.reasoning && (
                <p className="text-xs text-muted-foreground leading-relaxed italic">
                  "{vote.reasoning}"
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};
