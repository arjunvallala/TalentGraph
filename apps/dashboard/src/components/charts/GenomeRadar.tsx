import React from 'react';
import {
  RadarChart as RechartsRadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

interface GenomeRadarProps {
  scores?: {
    technical: number;
    career: number;
    domain: number;
    leadership: number;
    learning: number;
    stability: number;
    behavioral: number;
    readiness: number;
  } | number[];
  color?: string;
  candidateId?: string;
}

const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: { value: number; payload: { subject: string } }[] }) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card px-3 py-2 text-xs">
        <p className="font-medium text-white">{payload[0].payload.subject}</p>
        <p className="text-accent">{(payload[0].value * 100).toFixed(1)}%</p>
      </div>
    );
  }
  return null;
};

export const GenomeRadar: React.FC<GenomeRadarProps> = ({
  scores,
  color = '#3b82f6',
}) => {
  let technical = 0;
  let career = 0;
  let domain = 0;
  let leadership = 0;
  let learning = 0;
  let stability = 0;
  let behavioral = 0;
  let readiness = 0;

  if (Array.isArray(scores)) {
    [technical, career, domain, leadership, learning, stability, behavioral, readiness] = scores;
  } else if (scores) {
    ({ technical, career, domain, leadership, learning, stability, behavioral, readiness } = scores);
  }

  const data = [
    { subject: 'Technical', value: technical },
    { subject: 'Career', value: career },
    { subject: 'Domain', value: domain },
    { subject: 'Leadership', value: leadership },
    { subject: 'Learning', value: learning },
    { subject: 'Stability', value: stability },
    { subject: 'Behavioral', value: behavioral },
    { subject: 'Readiness', value: readiness },
  ];

  return (
    <ResponsiveContainer width="100%" height={280}>
      <RechartsRadarChart data={data} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
        <PolarGrid stroke="rgba(255,255,255,0.08)" />
        <PolarAngleAxis
          dataKey="subject"
          tick={{ fill: '#9ca3af', fontSize: 11, fontWeight: 500 }}
        />
        <Radar
          name="Score"
          dataKey="value"
          stroke={color}
          fill={color}
          fillOpacity={0.15}
          strokeWidth={2}
          dot={{ fill: color, r: 3 }}
        />
        <Tooltip content={<CustomTooltip />} />
      </RechartsRadarChart>
    </ResponsiveContainer>
  );
};
