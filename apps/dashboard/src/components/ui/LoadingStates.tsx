import React from 'react';

interface LoadingSkeletonProps {
  className?: string;
  count?: number;
}

export const Skeleton: React.FC<{ className?: string }> = ({ className }) => (
  <div
    className={`animate-pulse bg-white/[0.06] rounded-lg ${className || ''}`}
  />
);

export const MetricCardSkeleton: React.FC = () => (
  <div className="metric-card">
    <div className="flex items-start justify-between mb-3">
      <div className="space-y-2">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-7 w-20" />
      </div>
      <Skeleton className="w-10 h-10 rounded-xl" />
    </div>
    <Skeleton className="h-1.5 w-full mt-3" />
    <Skeleton className="h-3 w-28 mt-2" />
  </div>
);

export const TableRowSkeleton: React.FC = () => (
  <tr>
    {Array.from({ length: 8 }).map((_, i) => (
      <td key={i} className="px-4 py-3 border-b border-white/5">
        <Skeleton className="h-4 w-full" />
      </td>
    ))}
  </tr>
);

export const CardSkeleton: React.FC<LoadingSkeletonProps> = ({ className }) => (
  <div className={`glass-card p-5 space-y-3 ${className || ''}`}>
    <Skeleton className="h-4 w-3/4" />
    <Skeleton className="h-4 w-1/2" />
    <Skeleton className="h-4 w-5/6" />
    <Skeleton className="h-4 w-2/3" />
  </div>
);

export const PageLoader: React.FC = () => (
  <div className="flex items-center justify-center h-64">
    <div className="flex items-center gap-3">
      <div className="w-5 h-5 rounded-full bg-accent animate-bounce [animation-delay:-0.3s]" />
      <div className="w-5 h-5 rounded-full bg-accent-violet animate-bounce [animation-delay:-0.15s]" />
      <div className="w-5 h-5 rounded-full bg-accent animate-bounce" />
    </div>
  </div>
);

export const EmptyState: React.FC<{
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}> = ({ icon, title, description, action }) => (
  <div className="flex flex-col items-center justify-center py-16 text-center">
    {icon && (
      <div className="mb-4 p-4 rounded-2xl bg-white/[0.04] border border-white/[0.08]">
        <span className="text-muted-foreground">{icon}</span>
      </div>
    )}
    <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
    {description && (
      <p className="text-sm text-muted-foreground max-w-sm mb-6">{description}</p>
    )}
    {action}
  </div>
);
