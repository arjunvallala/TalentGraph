import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  gradient?: boolean;
  onClick?: () => void;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  className,
  hover = false,
  gradient = false,
  onClick,
  padding = 'md',
}) => {
  const padClass = {
    none: '',
    sm: 'p-4',
    md: 'p-5',
    lg: 'p-6',
  }[padding];

  return (
    <motion.div
      className={cn(
        'rounded-xl border border-white/[0.08]',
        gradient
          ? 'bg-gradient-card'
          : 'bg-gradient-to-br from-white/[0.04] to-white/[0.01]',
        hover && 'cursor-pointer transition-all duration-300 hover:border-white/[0.15] hover:from-white/[0.06] hover:to-white/[0.02] hover:-translate-y-0.5 hover:shadow-glass',
        onClick && 'cursor-pointer',
        padClass,
        className
      )}
      onClick={onClick}
      whileHover={hover ? { scale: 1.005 } : undefined}
      transition={{ type: 'spring', stiffness: 400, damping: 25 }}
    >
      {children}
    </motion.div>
  );
};
