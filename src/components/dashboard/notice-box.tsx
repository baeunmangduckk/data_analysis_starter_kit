import { Info, TriangleAlert } from "lucide-react";
import type { NoticeSection } from "@/types/page";

interface NoticeBoxProps {
  section: NoticeSection;
}

// 색만으로 의미를 전달하지 않도록 아이콘을 함께 쓴다.
export function NoticeBox({ section }: NoticeBoxProps) {
  const isWarning = section.tone === "warning";
  const Icon = isWarning ? TriangleAlert : Info;

  return (
    <div
      role="note"
      className={
        isWarning
          ? "flex items-start gap-2 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-foreground"
          : "flex items-start gap-2 rounded-xl border bg-muted/40 p-3 text-sm text-foreground"
      }
    >
      <Icon className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
      <p>{section.message}</p>
    </div>
  );
}
