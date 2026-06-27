import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface ScoreDistributionProps {
  distribution?: Record<string, number>;
  data?: { bucket?: string; range?: string; count: number }[];
}

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: { value: number }[]; label?: string }) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card px-3 py-2 text-xs">
        <p className="text-muted-foreground">{label}</p>
        <p className="font-semibold text-white">{payload[0].value} candidates</p>
      </div>
    );
  }
  return null;
};

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#f43f5e'];

export const ScoreDistribution: React.FC<ScoreDistributionProps> = ({
  distribution,
  data: dataProp,
}) => {
  let chartData: { range: string; count: number; color: string }[] = [];

  if (dataProp && Array.isArray(dataProp)) {
    chartData = dataProp.map((item, i) => ({
      range: item.range || item.bucket || '',
      count: item.count,
      color: COLORS[i % COLORS.length],
    }));
  } else if (distribution) {
    chartData = Object.entries(distribution).map(([range, count], i) => ({
      range,
      count,
      color: COLORS[i % COLORS.length],
    }));
  }

  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: -20 }}>
        <XAxis
          dataKey="range"
          tick={{ fill: '#6b7280', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: '#6b7280', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {chartData.map((entry, index) => (
            <Cell key={index} fill={entry.color} fillOpacity={0.8} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};
