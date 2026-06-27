import React, { useEffect, useRef } from 'react';
import type { WorkExperience } from '../../lib/api';
import { formatDuration } from '../../lib/utils';

interface CareerTimelineProps {
  workHistory?: WorkExperience[];
  experience?: WorkExperience[];
  candidateId?: string;
}

export const CareerTimeline: React.FC<CareerTimelineProps> = ({ workHistory, experience }) => {
  const history = workHistory || experience || [];

  if (!history || history.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-muted-foreground text-sm">
        No career history available
      </div>
    );
  }

  const sorted = [...history].sort((a, b) => {
    const aYear = parseInt(a.start_date?.split('-')[0] || '2000');
    const bYear = parseInt(b.start_date?.split('-')[0] || '2000');
    return aYear - bYear;
  });

  const maxDuration = Math.max(...sorted.map((w) => w.duration_months || 12));

  return (
    <div className="space-y-3">
      {sorted.map((job, i) => {
        const isCurrentRole = job.end_date === 'Present' || !job.end_date;
        const duration = job.duration_months || 12;
        const barWidth = (duration / maxDuration) * 100;
        const opacity = 0.4 + (i / sorted.length) * 0.6;

        return (
          <div key={i} className="group">
            <div className="flex items-start gap-4">
              {/* Timeline dot */}
              <div className="flex flex-col items-center mt-1.5">
                <div
                  className={`w-3 h-3 rounded-full border-2 flex-shrink-0 ${
                    isCurrentRole
                      ? 'bg-accent border-accent shadow-glow-blue'
                      : 'bg-surface-3 border-white/20'
                  }`}
                />
                {i < sorted.length - 1 && (
                  <div className="w-px h-full min-h-[40px] bg-white/10 mt-1" />
                )}
              </div>

              {/* Content */}
              <div className="flex-1 pb-4">
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <div>
                    <p className="font-semibold text-white text-sm">{job.title}</p>
                    <p className="text-xs text-accent">{job.company}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-xs text-muted-foreground">
                      {job.start_date?.slice(0, 7)} — {isCurrentRole ? 'Present' : job.end_date?.slice(0, 7)}
                    </p>
                    <p className="text-xs text-muted font-medium">
                      {formatDuration(duration)}
                    </p>
                  </div>
                </div>

                {/* Duration bar */}
                <div className="h-1.5 bg-surface-3 rounded-full overflow-hidden mb-2">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${barWidth}%`,
                      background: isCurrentRole
                        ? 'linear-gradient(90deg, #3b82f6, #8b5cf6)'
                        : `rgba(59, 130, 246, ${opacity})`,
                    }}
                  />
                </div>

                {/* Description */}
                {job.description && (
                  <p className="text-xs text-muted-foreground leading-relaxed">{job.description}</p>
                )}

                {/* Achievements */}
                {job.achievements && job.achievements.length > 0 && (
                  <ul className="mt-1.5 space-y-0.5">
                    {job.achievements.map((ach, j) => (
                      <li key={j} className="text-xs text-muted-foreground flex items-start gap-1.5">
                        <span className="text-accent mt-0.5">•</span>
                        {ach}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
