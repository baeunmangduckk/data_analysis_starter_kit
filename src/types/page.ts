// pipeline/models.py의 페이지 계약(PageData, 섹션 블록, SourcesData)과 1:1로 대응하는 타입.
// 페이지 JSON = 섹션 배열이며, section.type으로 판별되는 유니온이다.

import type { Insight, KpiMetric, WordCloudItem } from "@/types/dashboard";

export type ChartKind = "line" | "area" | "column" | "barH";

export interface ChartSeries {
  key: string;
  label: string;
}

// 값이 null이면 결측(예: 2024년 수치 없음)이다.
export type ChartPoint = Record<string, string | number | null>;

export interface StatsSection {
  type: "stats";
  title?: string | null;
  stats: KpiMetric[];
}

export interface ChartSection {
  type: "chart";
  title: string;
  caption?: string | null;
  kind: ChartKind;
  xKey: string;
  series: ChartSeries[];
  points: ChartPoint[];
  unit?: string | null;
  sourceIds: string[];
}

export interface TableColumn {
  key: string;
  label: string;
  align: "left" | "right";
}

export interface TableSection {
  type: "table";
  title: string;
  caption?: string | null;
  columns: TableColumn[];
  rows: Record<string, string | number | null>[];
  sourceIds: string[];
}

export interface CaseMetric {
  label: string;
  value: string;
}

export interface CaseCard {
  id: string;
  title: string;
  subtitle?: string | null;
  body: string;
  badge?: string | null;
  metrics: CaseMetric[];
  sourceId?: string | null;
}

export interface CasesSection {
  type: "cases";
  title: string;
  cards: CaseCard[];
}

export interface InsightsSection {
  type: "insights";
  title?: string | null;
  insights: Insight[];
}

export interface WordCloudSection {
  type: "wordcloud";
  title: string;
  words: WordCloudItem[];
}

export interface NoticeSection {
  type: "notice";
  tone: "info" | "warning";
  message: string;
}

export type Section =
  | StatsSection
  | ChartSection
  | TableSection
  | CasesSection
  | InsightsSection
  | WordCloudSection
  | NoticeSection;

export interface PageData {
  generatedAt: string;
  title: string;
  summary?: string | null;
  sections: Section[];
}

export interface Source {
  id: string;
  org: string;
  title: string;
  url?: string | null;
  year?: number | null;
  note?: string | null;
  usedBy: string[];
}

export interface SourcesData {
  generatedAt: string;
  sources: Source[];
}
