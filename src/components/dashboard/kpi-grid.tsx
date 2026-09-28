import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendBadge } from "@/components/dashboard/trend-badge";
import type { KpiMetric } from "@/types/dashboard";

interface KpiGridProps {
  metrics: KpiMetric[];
}

const numberFormatter = new Intl.NumberFormat("ko-KR");

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
            <TrendBadge trend={metric.trend} delta={metric.delta} />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
