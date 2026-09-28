import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendBadge } from "@/components/dashboard/trend-badge";
import type { Confidence, KpiMetric } from "@/types/dashboard";

interface KpiGridProps {
  metrics: KpiMetric[];
}

const numberFormatter = new Intl.NumberFormat("ko-KR");

// 확인된 수치(verified)는 배지를 생략하고, 추정/미검증 수치만 눈에 띄게 표시한다.
const CONFIDENCE_LABEL: Record<Exclude<Confidence, "verified">, string> = {
  estimated: "추정치",
  legacy_unverified: "미검증",
};

export function KpiGrid({ metrics }: KpiGridProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {metrics.map((metric) => (
        <Card key={metric.id}>
          <CardHeader>
            <CardTitle>{metric.label}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            <div className="text-2xl font-semibold">
              {numberFormatter.format(metric.value)}
              {metric.unit ? (
                <span className="ml-1 text-sm font-normal text-muted-foreground">{metric.unit}</span>
              ) : null}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <TrendBadge trend={metric.trend} delta={metric.delta} goodDirection={metric.goodDirection} />
              {metric.confidence && metric.confidence !== "verified" ? (
                <Badge variant="warning">{CONFIDENCE_LABEL[metric.confidence]}</Badge>
              ) : null}
              {metric.asOf ? (
                <span className="text-xs text-muted-foreground">기준 {metric.asOf}</span>
              ) : null}
            </div>
            {metric.note ? <p className="text-xs text-muted-foreground">{metric.note}</p> : null}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
