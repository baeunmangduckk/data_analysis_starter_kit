"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TimeseriesData } from "@/types/dashboard";

interface TrendChartProps {
  data: TimeseriesData;
}

const CHART_COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
];

export function TrendChart({ data }: TrendChartProps) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <AreaChart data={data.points}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis dataKey="date" stroke="var(--muted-foreground)" fontSize={12} />
        <YAxis stroke="var(--muted-foreground)" fontSize={12} />
        <Tooltip />
        <Legend />
        {data.series.map((series, index) => {
          const color = CHART_COLORS[index % CHART_COLORS.length];
          return (
            <Area
              key={series.key}
              type="monotone"
              dataKey={series.key}
              name={series.label}
              stroke={color}
              fill={color}
              fillOpacity={0.15}
            />
          );
        })}
      </AreaChart>
    </ResponsiveContainer>
  );
}
