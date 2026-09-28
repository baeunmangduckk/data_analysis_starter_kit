// pipeline/models.py(Pydantic)의 출력과 1:1로 대응하는 타입 정의.
// 홈이 읽는 public/data/metrics.json, insights.json의 형태를 옮긴 것이다.
// 페이지 JSON(섹션 배열)은 src/types/page.ts에 있다.

export type TrendDirection = "up" | "down" | "flat";
export type InsightSeverity = "info" | "positive" | "warning" | "critical";
export type SentimentLabel = "positive" | "negative" | "neutral";

export type GoodDirection = "up" | "down";
export type Confidence = "verified" | "estimated" | "legacy_unverified";

export interface KpiMetric {
  id: string;
  label: string;
  value: number;
  unit?: string | null;
  delta?: number | null;
  trend?: TrendDirection | null;
  // 아래는 페이지 stats 섹션에서 쓰는 선택 필드 (홈 metrics.json은 생략 가능)
  note?: string | null;
  sourceId?: string | null;
  asOf?: string | null;
  goodDirection?: GoodDirection | null;
  confidence?: Confidence | null;
}

export interface MetricsData {
  generatedAt: string;
  metrics: KpiMetric[];
}

export interface Insight {
  id: string;
  severity: InsightSeverity;
  text: string;
  relatedMetricId?: string | null;
}

export interface InsightsData {
  generatedAt: string;
  insights: Insight[];
}

export interface WordCloudItem {
  text: string;
  weight: number;
  sentiment: SentimentLabel;
}
