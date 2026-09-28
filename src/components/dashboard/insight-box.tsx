import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Insight, InsightSeverity } from "@/types/dashboard";

interface InsightBoxProps {
  insights: Insight[];
  title?: string;
}

const SEVERITY_VARIANT: Record<InsightSeverity, "secondary" | "positive" | "warning" | "negative"> = {
  info: "secondary",
  positive: "positive",
  warning: "warning",
  critical: "negative",
};

const SEVERITY_LABEL: Record<InsightSeverity, string> = {
  info: "정보",
  positive: "긍정",
  warning: "주의",
  critical: "위험",
};

export function InsightBox({ insights, title = "인사이트" }: InsightBoxProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {insights.map((insight) => (
          <div key={insight.id} className="flex items-start gap-2">
            <Badge variant={SEVERITY_VARIANT[insight.severity]}>{SEVERITY_LABEL[insight.severity]}</Badge>
            <p className="text-sm text-foreground">{insight.text}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
