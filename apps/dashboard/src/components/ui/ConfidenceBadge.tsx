import React from 'react';
import { cn, getConfidenceLabel } from '../../lib/utils';

interface ConfidenceBadgeProps {
  confidence: number;
  size?: 'sm' | 'md';
  className?: string;
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({
  confidence,
  size = 'md',
  className,
}) => {
  const label = getConfidenceLabel(confidence);
  const dotColor =
    confidence >= 0.75
      ? 'bg-accent-emerald'
      : confidence >= 0.5
      ? 'bg-accent-amber'
      : 'bg-accent-rose';
  const textColor =
    confidence >= 0.75
      ? 'text-accent-emerald'
      : confidence >= 0.5
      ? 'text-accent-amber'
      : 'text-accent-rose';

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 font-medium',
        size === 'sm' ? 'text-xs' : 'text-sm',
        textColor,
        className
      )}
    >
      <span className={cn('w-1.5 h-1.5 rounded-full', dotColor)} />
      {label}
    </span>
  );
};
