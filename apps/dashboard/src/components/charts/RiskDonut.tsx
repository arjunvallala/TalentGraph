import React from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface RiskDonutProps {
  distribution?: Record<string, number>;
  data?: { label?: string; name?: string; value: number; color?: string }[];
}

const COLORS: Record<string, string> = {
  Low: '#10b981',
  'Low Risk': '#10b981',
  Medium: '#f59e0b',
  'Medium Risk': '#f59e0b',
  High: '#f43f5e',
  'High Risk': '#f43f5e',
};

const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: { name: string; value: number }[] }) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card px-3 py-2 text-xs">
        <p className="font-semibold text-white">{payload[0].name}</p>
        <p className="text-muted-foreground">{payload[0].value} candidates</p>
      </div>
    );
  }
  return null;
};

export const RiskDonut: React.FC<RiskDonutProps> = ({ distribution, data: dataProp }) => {
  const chartData = dataProp
    ? dataProp.map((item) => ({
        name: item.name || item.label || '',
        value: item.value,
        color: item.color || COLORS[item.name || item.label || ''] || '#6b7280',
      }))
    : Object.entries(distribution || {}).map(([name, value]) => ({
        name,
        value,
        color: COLORS[name] || '#6b7280',
      }));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={55}
          outerRadius={80}
          paddingAngle={3}
          dataKey="value"
        >
          {chartData.map((entry, index) => (
            <Cell key={index} fill={entry.color} fillOpacity={0.85} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend
          iconType="circle"
          iconSize={8}
          formatter={(value) => (
            <span className="text-xs text-muted-foreground">{value}</span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
};
