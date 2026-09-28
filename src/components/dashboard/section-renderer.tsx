import { CaseCards } from "@/components/dashboard/case-cards";
import { ChartCard } from "@/components/dashboard/chart-card";
import { InsightBox } from "@/components/dashboard/insight-box";
import { KpiGrid } from "@/components/dashboard/kpi-grid";
import { NoticeBox } from "@/components/dashboard/notice-box";
import { SentimentWordCloud } from "@/components/dashboard/sentiment-word-cloud";
import { TableCard } from "@/components/dashboard/table-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Section } from "@/types/page";

interface SectionRendererProps {
  sections: Section[];
}

function renderSection(section: Section) {
  switch (section.type) {
    case "stats":
      return (
        <div className="flex flex-col gap-3">
          {section.title ? <h2 className="text-base font-semibold">{section.title}</h2> : null}
          <KpiGrid metrics={section.stats} />
        </div>
      );
    case "chart":
      return <ChartCard section={section} />;
    case "table":
      return <TableCard section={section} />;
    case "cases":
      return <CaseCards section={section} />;
    case "insights":
      return <InsightBox insights={section.insights} title={section.title ?? undefined} />;
    case "wordcloud":
      return (
        <Card>
          <CardHeader>
            <CardTitle>{section.title}</CardTitle>
          </CardHeader>
          <CardContent>
            <SentimentWordCloud data={{ generatedAt: "", words: section.words }} />
          </CardContent>
        </Card>
      );
    case "notice":
      return <NoticeBox section={section} />;
    default: {
      // 새 섹션 타입을 추가하고 여기를 빠뜨리면 컴파일 단계에서 오류가 난다.
      const unhandled: never = section;
      throw new Error(`처리되지 않은 섹션 타입입니다: ${JSON.stringify(unhandled)}`);
    }
  }
}

export function SectionRenderer({ sections }: SectionRendererProps) {
  return (
    <>
      {sections.map((section, index) => (
        <div key={index}>{renderSection(section)}</div>
      ))}
    </>
  );
}
