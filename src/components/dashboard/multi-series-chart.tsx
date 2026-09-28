"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChartSection } from "@/types/page";

interface MultiSeriesChartProps {
  section: ChartSection;
}

// 카테고리 팔레트(--chart-1~5)를 시리즈 순서대로 고정 배정한다. 순서를 섞지 않는다.
const CHART_COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
];

const compactFormatter = new Intl.NumberFormat("ko-KR", { notation: "compact" });
const tooltipFormatter = new Intl.NumberFormat("ko-KR");

export function MultiSeriesChart({ section }: MultiSeriesChartProps) {
  const { kind, xKey, series, points, unit } = section;
  const isHorizontal = kind === "barH";
  const showLegend = series.length > 1;

  const axisProps = { stroke: "var(--muted-foreground)", fontSize: 12 };
  const tooltip = (
    <Tooltip
      formatter={(value) =>
        typeof value === "number" ? `${tooltipFormatter.format(value)}${unit ? ` ${unit}` : ""}` : "–"
      }
    />
  );
  // itemSorter={null}: Recharts 기본값은 범례를 이름순으로 정렬해 시리즈 순서(=색 배정 순서)와 어긋난다.
  const legend = showLegend ? <Legend itemSorter={null} /> : null;
  const grid = <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />;
  const valueTick = (value: number) => compactFormatter.format(value);

  return (
    <ResponsiveContainer width="100%" height={isHorizontal ? Math.max(240, points.length * 44 + 60) : 320}>
      {kind === "line" ? (
        <LineChart data={points}>
          {grid}
          <XAxis dataKey={xKey} {...axisProps} />
          <YAxis {...axisProps} tickFormatter={valueTick} />
          {tooltip}
          {legend}
          {series.map((s, index) => (
            <Line
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.label}
              stroke={CHART_COLORS[index % CHART_COLORS.length]}
              strokeWidth={2}
              dot={{ r: 4 }}
              connectNulls={false}
            />
          ))}
        </LineChart>
      ) : kind === "area" ? (
        <AreaChart data={points}>
          {grid}
          <XAxis dataKey={xKey} {...axisProps} />
          <YAxis {...axisProps} tickFormatter={valueTick} />
          {tooltip}
          {legend}
          {series.map((s, index) => {
            const color = CHART_COLORS[index % CHART_COLORS.length];
            return (
              <Area
                key={s.key}
                type="monotone"
                dataKey={s.key}
                name={s.label}
                stroke={color}
                fill={color}
                fillOpacity={0.15}
                connectNulls={false}
              />
            );
          })}
        </AreaChart>
      ) : (
        <BarChart data={points} layout={isHorizontal ? "vertical" : "horizontal"} margin={{ left: isHorizontal ? 24 : 0 }}>
          {grid}
          {isHorizontal ? (
            <>
              <XAxis type="number" {...axisProps} tickFormatter={valueTick} />
              <YAxis type="category" dataKey={xKey} width={110} {...axisProps} />
            </>
          ) : (
            <>
              <XAxis dataKey={xKey} {...axisProps} />
              <YAxis {...axisProps} tickFormatter={valueTick} />
            </>
          )}
          {tooltip}
          {legend}
          {series.map((s, index) => (
            <Bar
              key={s.key}
              dataKey={s.key}
              name={s.label}
              fill={CHART_COLORS[index % CHART_COLORS.length]}
              maxBarSize={28}
              radius={isHorizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]}
            />
          ))}
        </BarChart>
      )}
    </ResponsiveContainer>
  );
}
