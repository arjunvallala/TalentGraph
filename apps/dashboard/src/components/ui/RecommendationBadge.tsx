import React from 'react';
import { cn, getRecommendationColor } from '../../lib/utils';

interface RecommendationBadgeProps {
  recommendation: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const RecommendationBadge: React.FC<RecommendationBadgeProps> = ({
  recommendation,
  size = 'md',
  className,
}) => {
  const colorClass = getRecommendationColor(recommendation);

  const sizeClass = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
    lg: 'text-sm px-3 py-1.5',
  }[size];

  return (
    <span
      className={cn(
        'inline-flex items-center font-semibold rounded-full border whitespace-nowrap',
        colorClass,
        sizeClass,
        className
      )}
    >
      {recommendation}
    </span>
  );
};
