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

export function TrendBadge({ trend, delta }: TrendBadgeProps) {
  if (!trend) return null;

  const { variant, Icon } = TREND_CONFIG[trend];
  const deltaText = delta != null ? `${delta > 0 ? "+" : ""}${deltaFormatter.format(delta)}` : null;

  return (
    <Badge variant={variant}>
      <Icon data-icon="inline-start" />
      {deltaText ?? trend}
    </Badge>
  );
}
