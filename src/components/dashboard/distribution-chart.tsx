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

// 판매량처럼 큰 수는 "1,600만"처럼 축약해 X축 눈금이 서로 겹치지 않게 한다.
const compactFormatter = new Intl.NumberFormat("ko-KR", { notation: "compact" });

export function DistributionChart({ data }: DistributionChartProps) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data.categories} layout="vertical" margin={{ left: 24 }}>
        <XAxis
          type="number"
          stroke="var(--muted-foreground)"
          fontSize={12}
          tickFormatter={(value: number) => compactFormatter.format(value)}
        />
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
