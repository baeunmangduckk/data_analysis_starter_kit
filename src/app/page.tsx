import fs from "node:fs/promises";
import path from "node:path";
import { DistributionChart } from "@/components/dashboard/distribution-chart";
import { InsightBox } from "@/components/dashboard/insight-box";
import { KpiGrid } from "@/components/dashboard/kpi-grid";
import { SentimentWordCloud } from "@/components/dashboard/sentiment-word-cloud";
import { TrendChart } from "@/components/dashboard/trend-chart";
import { ThemeToggle } from "@/components/theme-toggle";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type {
  DistributionData,
  InsightsData,
  MetricsData,
  TimeseriesData,
  WordCloudData,
} from "@/types/dashboard";

const DATA_DIR = path.join(process.cwd(), "public", "data");

async function readJson<T>(filename: string): Promise<T> {
  const raw = await fs.readFile(path.join(DATA_DIR, filename), "utf-8");
  return JSON.parse(raw) as T;
}

// 컴포넌트 함수 "안"에서 읽어야, 분석가가 npm run etl로 JSON을 새로 만들 때마다
// 새로고침만으로 바로 반영된다 (모듈 스코프에서 읽으면 최초 1회만 로드됨).
export default async function DashboardPage() {
  const [metrics, timeseries, distribution, insights, wordcloud] = await Promise.all([
    readJson<MetricsData>("metrics.json"),
    readJson<TimeseriesData>("timeseries.json"),
    readJson<DistributionData>("distribution.json"),
    readJson<InsightsData>("insights.json"),
    readJson<WordCloudData>("wordcloud.json"),
  ]);

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 p-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">데이터 분석 대시보드</h1>
          <p className="text-sm text-muted-foreground">
            마지막 갱신: {new Date(metrics.generatedAt).toLocaleString("ko-KR")}
          </p>
        </div>
        <ThemeToggle />
      </header>

      <KpiGrid metrics={metrics.metrics} />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>추이</CardTitle>
          </CardHeader>
          <CardContent>
            <TrendChart data={timeseries} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>{distribution.title}</CardTitle>
          </CardHeader>
          <CardContent>
            <DistributionChart data={distribution} />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <InsightBox insights={insights.insights} />
        <Card>
          <CardHeader>
            <CardTitle>워드클라우드</CardTitle>
          </CardHeader>
          <CardContent>
            <SentimentWordCloud data={wordcloud} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
