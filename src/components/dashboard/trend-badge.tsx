import { ArrowDown, ArrowUp, Minus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { GoodDirection, TrendDirection } from "@/types/dashboard";

interface TrendBadgeProps {
  trend?: TrendDirection | null;
  delta?: number | null;
  // 증가/감소 중 무엇이 좋은 변화인지. 없으면 증가=긍정으로 본다.
  goodDirection?: GoodDirection | null;
}

const TREND_ICON = {
  up: ArrowUp,
  down: ArrowDown,
  flat: Minus,
};

const deltaFormatter = new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 1 });
// 1 미만의 작은 증감(예: Gini -0.0073)이 "-0"으로 뭉개지지 않도록 소수 4자리까지 보여준다.
const smallDeltaFormatter = new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 4 });

function pickVariant(trend: TrendDirection, goodDirection: GoodDirection) {
  if (trend === "flat") return "secondary" as const;
  return trend === goodDirection ? ("positive" as const) : ("negative" as const);
}

export function TrendBadge({ trend, delta, goodDirection }: TrendBadgeProps) {
  if (!trend) return null;

  const Icon = TREND_ICON[trend];
  const variant = pickVariant(trend, goodDirection ?? "up");
  const formatter = delta != null && Math.abs(delta) < 1 ? smallDeltaFormatter : deltaFormatter;
  const deltaText = delta != null ? `${delta > 0 ? "+" : ""}${formatter.format(delta)}` : null;

  return (
    <Badge variant={variant}>
      <Icon data-icon="inline-start" />
      {deltaText ?? trend}
    </Badge>
  );
}
