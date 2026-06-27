import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  LabelList,
} from 'recharts';

interface FunnelChartProps {
  totalProcessed?: number;
  stage1?: number;
  stage2?: number;
  stage3?: number;
  data?: { stage: string; count: number; color?: string; retention?: string }[];
}

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: { value: number }[]; label?: string }) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card px-3 py-2 text-xs">
        <p className="font-semibold text-white">{label}</p>
        <p className="text-muted-foreground">{payload[0].value.toLocaleString()} candidates</p>
      </div>
    );
  }
  return null;
};

export const FunnelChart: React.FC<FunnelChartProps> = ({
  totalProcessed = 100000,
  stage1 = 6,
  stage2 = 8,
  stage3 = 6,
  data: dataProp,
}) => {
  const defaultColors = ['#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#c084fc', '#10b981'];
  const data = dataProp
    ? dataProp.map((item, i) => ({
        stage: item.stage,
        count: item.count,
        retention: item.retention || '',
        color: item.color || defaultColors[i % defaultColors.length],
      }))
    : [
        {
          stage: 'Total Pool',
          count: totalProcessed,
          retention: '100%',
          color: '#3b82f6',
        },
        {
          stage: 'After Filtering',
          count: Math.round(totalProcessed * 0.02),
          retention: '2%',
          color: '#6366f1',
        },
        {
          stage: 'AI Ranked',
          count: Math.round(totalProcessed * 0.002),
          retention: '0.2%',
          color: '#8b5cf6',
        },
        {
          stage: 'Stage 1',
          count: stage1,
          retention: '',
          color: '#a855f7',
        },
        {
          stage: 'Stage 2',
          count: stage2,
          retention: '',
          color: '#c084fc',
        },
        {
          stage: 'Final Pool',
          count: stage3,
          retention: '',
          color: '#10b981',
        },
      ];

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 20, right: 30, bottom: 5, left: 10 }}>
        <XAxis
          dataKey="stage"
          tick={{ fill: '#6b7280', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: '#6b7280', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v) => v >= 1000 ? `${(v / 1000).toFixed(0)}K` : v}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          <LabelList
            dataKey="count"
            position="top"
            formatter={(v: number) => v >= 1000 ? `${(v / 1000).toFixed(0)}K` : v}
            style={{ fill: '#9ca3af', fontSize: 10 }}
          />
          {data.map((entry, index) => (
            <Cell key={index} fill={entry.color} fillOpacity={0.8} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};
