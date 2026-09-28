import { ArrowDown, ArrowUp, Minus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { TrendDirection } from "@/types/dashboard";

interface TrendBadgeProps {
  trend?: TrendDirection | null;
  delta?: number | null;
}

const TREND_CONFIG = {
  up: { variant: "positive" as const, Icon: ArrowUp },
  down: { variant: "negative" as const, Icon: ArrowDown },
  flat: { variant: "secondary" as const, Icon: Minus },
};

const deltaFormatter = new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 1 });
// 1 미만의 작은 증감(예: Gini -0.0073)이 "-0"으로 뭉개지지 않도록 소수 4자리까지 보여준다.
const smallDeltaFormatter = new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 4 });

export function TrendBadge({ trend, delta }: TrendBadgeProps) {
  if (!trend) return null;

  const { variant, Icon } = TREND_CONFIG[trend];
  const formatter = delta != null && Math.abs(delta) < 1 ? smallDeltaFormatter : deltaFormatter;
  const deltaText = delta != null ? `${delta > 0 ? "+" : ""}${formatter.format(delta)}` : null;

  return (
    <Badge variant={variant}>
      <Icon data-icon="inline-start" />
      {deltaText ?? trend}
    </Badge>
  );
}
