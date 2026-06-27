import React from 'react';
import { cn, getRiskColor } from '../../lib/utils';
import { ShieldAlert, ShieldCheck, ShieldX } from 'lucide-react';

interface RiskBadgeProps {
  risk: string;
  size?: 'sm' | 'md';
  showIcon?: boolean;
  className?: string;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({
  risk,
  size = 'md',
  showIcon = true,
  className,
}) => {
  const colorClass = getRiskColor(risk);
  const Icon =
    risk?.toLowerCase() === 'low'
      ? ShieldCheck
      : risk?.toLowerCase() === 'medium'
      ? ShieldAlert
      : ShieldX;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 font-semibold rounded-full border',
        size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-xs px-2.5 py-1',
        colorClass,
        className
      )}
    >
      {showIcon && <Icon className="w-3 h-3" />}
      {risk}
    </span>
  );
};
