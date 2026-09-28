// pipeline/models.py(Pydantic)의 출력과 1:1로 대응하는 타입 정의.
// public/data/*.json 5개 파일의 형태를 그대로 옮긴 것이다.

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

export interface TimeseriesSeries {
  key: string;
  label: string;
}

export interface TimeseriesPoint {
  date: string;
  [seriesKey: string]: string | number;
}

export interface TimeseriesData {
  generatedAt: string;
  series: TimeseriesSeries[];
  points: TimeseriesPoint[];
}

export interface DistributionCategory {
  category: string;
  label: string;
  value: number;
}

export interface DistributionData {
  generatedAt: string;
  title: string;
  categories: DistributionCategory[];
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

export interface WordCloudData {
  generatedAt: string;
  words: WordCloudItem[];
}
