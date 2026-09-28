"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface ErrorProps {
  error: Error;
  reset: () => void;
}

// JSON 문법 오류 등 데이터를 읽는 도중 예기치 않은 실패가 났을 때 보여주는 화면.
export default function DashboardError({ error, reset }: ErrorProps) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
        <p className="text-sm font-medium">데이터를 불러오는 중 문제가 발생했습니다.</p>
        <p className="text-xs text-muted-foreground">{error.message}</p>
        <Button variant="outline" size="sm" onClick={reset}>
          다시 시도
        </Button>
      </CardContent>
    </Card>
  );
}
