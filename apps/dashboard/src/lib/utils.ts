import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatScore(score: number): string {
  return (score * 100).toFixed(1) + '%';
}

export function formatScoreRaw(score: number): string {
  return score.toFixed(3);
}

export function getScoreColor(score: number): string {
  if (score >= 0.85) return 'text-accent-emerald';
  if (score >= 0.70) return 'text-accent';
  if (score >= 0.55) return 'text-accent-violet';
  if (score >= 0.40) return 'text-accent-amber';
  return 'text-muted-foreground';
}

export function getScoreBgColor(score: number): string {
  if (score >= 0.85) return 'bg-accent-emerald/20 text-accent-emerald border-accent-emerald/30';
  if (score >= 0.70) return 'bg-accent/20 text-accent border-accent/30';
  if (score >= 0.55) return 'bg-accent-violet/20 text-accent-violet border-accent-violet/30';
  if (score >= 0.40) return 'bg-accent-amber/20 text-accent-amber border-accent-amber/30';
  return 'bg-white/5 text-muted-foreground border-white/10';
}

export function getScoreBarColor(score: number): string {
  if (score >= 0.85) return 'bg-accent-emerald';
  if (score >= 0.70) return 'bg-accent';
  if (score >= 0.55) return 'bg-accent-violet';
  if (score >= 0.40) return 'bg-accent-amber';
  return 'bg-muted';
}

export function getRecommendationColor(rec: string): string {
  const r = rec?.toLowerCase() || '';
  if (r.includes('strong hire')) return 'bg-accent-emerald/20 text-accent-emerald border-accent-emerald/30';
  if (r.includes('hire')) return 'bg-accent/20 text-accent border-accent/30';
  if (r.includes('consider')) return 'bg-accent-violet/20 text-accent-violet border-accent-violet/30';
  if (r.includes('pass')) return 'bg-accent-amber/20 text-accent-amber border-accent-amber/30';
  if (r.includes('reject')) return 'bg-accent-rose/20 text-accent-rose border-accent-rose/30';
  return 'bg-white/5 text-muted-foreground border-white/10';
}

export function getRiskColor(risk: string): string {
  const r = risk?.toLowerCase() || '';
  if (r === 'low') return 'bg-accent-emerald/20 text-accent-emerald border-accent-emerald/30';
  if (r === 'medium') return 'bg-accent-amber/20 text-accent-amber border-accent-amber/30';
  if (r === 'high') return 'bg-accent-rose/20 text-accent-rose border-accent-rose/30';
  return 'bg-white/5 text-muted-foreground border-white/10';
}

export function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.75) return 'text-accent-emerald';
  if (confidence >= 0.5) return 'text-accent-amber';
  return 'text-accent-rose';
}

export function getConfidenceLabel(confidence: number): string {
  if (confidence >= 0.75) return 'High';
  if (confidence >= 0.5) return 'Medium';
  return 'Low';
}

export function truncate(str: string, maxLen: number): string {
  if (!str) return '';
  if (str.length <= maxLen) return str;
  return str.slice(0, maxLen) + '…';
}

export function formatDuration(months: number): string {
  if (!months) return '';
  const y = Math.floor(months / 12);
  const m = months % 12;
  if (y === 0) return `${m}mo`;
  if (m === 0) return `${y}yr`;
  return `${y}yr ${m}mo`;
}
