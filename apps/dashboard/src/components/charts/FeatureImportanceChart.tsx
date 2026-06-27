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

interface FeatureImportanceChartProps {
  features?: Record<string, number> | { name?: string; feature?: string; value?: number; importance?: number }[];
  data?: { name?: string; feature?: string; value?: number; importance?: number }[];
  maxItems?: number;
}

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: { value: number }[]; label?: string }) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card px-3 py-2 text-xs">
        <p className="font-medium text-white">{label}</p>
        <p className="text-accent">{(payload[0].value * 100).toFixed(1)}% importance</p>
      </div>
    );
  }
  return null;
};

function formatFeatureName(key: string): string {
  return key
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

export const FeatureImportanceChart: React.FC<FeatureImportanceChartProps> = ({
  features,
  data: dataProp,
  maxItems = 10,
}) => {
  const rawFeatures = features || dataProp || [];
  let chartData: { name: string; value: number }[] = [];

  if (Array.isArray(rawFeatures)) {
    chartData = rawFeatures.map((item) => ({
      name: item.name || item.feature || '',
      value: item.importance !== undefined ? item.importance : (item.value || 0),
    }));
  } else if (rawFeatures && typeof rawFeatures === 'object') {
    chartData = Object.entries(rawFeatures).map(([key, value]) => ({
      name: formatFeatureName(key),
      value,
    }));
  }

  const data = chartData
    .sort((a, b) => b.value - a.value)
    .slice(0, maxItems);

  return (
    <ResponsiveContainer width="100%" height={Math.max(200, data.length * 32)}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 5, right: 20, bottom: 5, left: 10 }}
      >
        <XAxis
          type="number"
          domain={[0, 1]}
          tick={{ fill: '#6b7280', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
        />
        <YAxis
          type="category"
          dataKey="name"
          width={110}
          tick={{ fill: '#9ca3af', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
        <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={18}>
          {data.map((_, index) => (
            <Cell
              key={index}
              fill={`hsl(${220 + index * 12}, 80%, ${65 - index * 2}%)`}
              fillOpacity={0.85}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};
