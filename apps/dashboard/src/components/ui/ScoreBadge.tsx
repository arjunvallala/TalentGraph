import React from 'react';
import { cn, getScoreBgColor } from '../../lib/utils';

interface ScoreBadgeProps {
  score: number;
  showPercent?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const ScoreBadge: React.FC<ScoreBadgeProps> = ({
  score,
  showPercent = true,
  size = 'md',
  className,
}) => {
  const colorClass = getScoreBgColor(score);
  const display = showPercent
    ? `${(score * 100).toFixed(1)}%`
    : score.toFixed(3);

  const sizeClass = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1',
    lg: 'text-base px-3 py-1.5',
  }[size];

  return (
    <span
      className={cn(
        'inline-flex items-center font-semibold rounded-full border',
        colorClass,
        sizeClass,
        className
      )}
    >
      {display}
    </span>
  );
};
