import { DataMissing } from "@/components/dashboard/data-missing";
import { InsightBox } from "@/components/dashboard/insight-box";
import { KpiGrid } from "@/components/dashboard/kpi-grid";
import { PageHeader } from "@/components/dashboard/page-header";
import { TopicLinks } from "@/components/dashboard/topic-links";
import { readData } from "@/lib/data";
import type { InsightsData, MetricsData } from "@/types/dashboard";

// 컴포넌트 함수 "안"에서 읽어야, 분석가가 npm run etl로 JSON을 새로 만들 때마다
// 새로고침만으로 바로 반영된다 (readData가 요청 시점 읽기를 보장한다).
export default async function DashboardPage() {
  const [metrics, insights] = await Promise.all([
    readData<MetricsData>("metrics.json"),
    readData<InsightsData>("insights.json"),
  ]);

  if (!metrics || !insights) {
    return <DataMissing file={!metrics ? "metrics.json" : "insights.json"} />;
  }

  return (
    <>
      <PageHeader
        title="K-Pop 산업 대시보드"
        summary="핵심 지표와 인사이트 요약 — 자세한 내용은 아래 주제별 페이지에서 확인하세요"
        generatedAt={metrics.generatedAt}
      />
      <KpiGrid metrics={metrics.metrics} />
      <InsightBox insights={insights.insights} />
      <TopicLinks />
    </>
  );
}
