"use client";

import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DistributionData } from "@/types/dashboard";

interface DistributionChartProps {
  data: DistributionData;
}

const CHART_COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
];

export function DistributionChart({ data }: DistributionChartProps) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data.categories} layout="vertical" margin={{ left: 24 }}>
        <XAxis type="number" stroke="var(--muted-foreground)" fontSize={12} />
        <YAxis type="category" dataKey="label" stroke="var(--muted-foreground)" fontSize={12} width={90} />
        <Tooltip />
        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
          {data.categories.map((category, index) => (
            <Cell key={category.category} fill={CHART_COLORS[index % CHART_COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
