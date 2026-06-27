import React from 'react';
import { motion } from 'framer-motion';
import { cn, getScoreBarColor } from '../../lib/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: number; // positive = up, negative = down, 0 = flat
  trendLabel?: string;
  subtitle?: string;
  color?: 'blue' | 'violet' | 'emerald' | 'amber' | 'rose';
  score?: number; // 0-1 for sparkline bar
  className?: string;
  delay?: number;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  icon,
  trend,
  trendLabel,
  subtitle,
  color = 'blue',
  score,
  className,
  delay = 0,
}) => {
  const colorMap = {
    blue: { bg: 'bg-accent/10', text: 'text-accent', glow: 'shadow-glow-blue' },
    violet: { bg: 'bg-accent-violet/10', text: 'text-accent-violet', glow: 'shadow-glow-violet' },
    emerald: { bg: 'bg-accent-emerald/10', text: 'text-accent-emerald', glow: '' },
    amber: { bg: 'bg-accent-amber/10', text: 'text-accent-amber', glow: '' },
    rose: { bg: 'bg-accent-rose/10', text: 'text-accent-rose', glow: '' },
  };

  const c = colorMap[color];

  const TrendIcon = trend !== undefined
    ? trend > 0 ? TrendingUp : trend < 0 ? TrendingDown : Minus
    : null;

  const trendColor = trend !== undefined
    ? trend > 0 ? 'text-accent-emerald' : trend < 0 ? 'text-accent-rose' : 'text-muted-foreground'
    : '';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className={cn(
        'metric-card group relative overflow-hidden',
        className
      )}
    >
      {/* Background glow */}
      <div className={cn('absolute -top-4 -right-4 w-20 h-20 rounded-full opacity-20 blur-2xl', c.bg)} />

      <div className="relative z-10">
        <div className="flex items-start justify-between mb-3">
          <div>
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
              {label}
            </p>
            <p className={cn('text-2xl font-bold', c.text)}>{value}</p>
          </div>
          {icon && (
            <div className={cn('p-2.5 rounded-xl', c.bg)}>
              <span className={cn('w-5 h-5 block', c.text)}>{icon}</span>
            </div>
          )}
        </div>

        {score !== undefined && (
          <div className="score-bar mt-3 mb-2">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${score * 100}%` }}
              transition={{ duration: 0.8, delay: delay + 0.2, ease: 'easeOut' }}
              className={cn('score-bar-fill', getScoreBarColor(score))}
            />
          </div>
        )}

        {(trend !== undefined || subtitle) && (
          <div className="flex items-center gap-2 mt-2">
            {TrendIcon && trend !== undefined && (
              <span className={cn('flex items-center gap-1 text-xs font-medium', trendColor)}>
                <TrendIcon className="w-3 h-3" />
                {Math.abs(trend)}%
              </span>
            )}
            {trendLabel && (
              <span className="text-xs text-muted-foreground">{trendLabel}</span>
            )}
            {subtitle && !trendLabel && (
              <span className="text-xs text-muted-foreground">{subtitle}</span>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
};
