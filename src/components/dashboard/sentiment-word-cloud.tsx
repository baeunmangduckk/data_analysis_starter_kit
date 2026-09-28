"use client";

import { cn } from "@/lib/utils";
import type { SentimentLabel, WordCloudItem } from "@/types/dashboard";

interface SentimentWordCloudProps {
  words: WordCloudItem[];
}

const SENTIMENT_CLASS: Record<SentimentLabel, string> = {
  positive: "text-emerald-600 dark:text-emerald-400",
  negative: "text-destructive",
  neutral: "text-muted-foreground",
};

// 별도 워드클라우드 라이브러리 없이, 빈도(weight)를 글자 크기로 매핑하는
// 단순 flex-wrap 배치로 시작한다. 정교한 원형 패킹이 필요해지면 그때 교체한다.
export function SentimentWordCloud({ words }: SentimentWordCloudProps) {
  const maxWeight = Math.max(...words.map((word) => word.weight), 1);

  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
      {words.map((word) => {
        const scale = word.weight / maxWeight;
        const fontSizeRem = 0.8 + scale * 1.4;
        return (
          <span
            key={word.text}
            className={cn("font-medium leading-none", SENTIMENT_CLASS[word.sentiment])}
            style={{ fontSize: `${fontSizeRem}rem` }}
          >
            {word.text}
          </span>
        );
      })}
    </div>
  );
}
