import { Card, CardContent } from "@/components/ui/card";

interface DataMissingProps {
  file: string;
}

// public/data/<file>이 없을 때(아직 etl을 실행하지 않은 경우) 빈 화면 대신 원인과 해결 방법을 알려준다.
export function DataMissing({ file }: DataMissingProps) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center gap-2 py-10 text-center">
        <p className="text-sm font-medium">데이터 파일을 찾을 수 없습니다 ({file})</p>
        <p className="text-sm text-muted-foreground">
          터미널에서 <code className="rounded bg-muted px-1.5 py-0.5 text-xs">npm run etl</code>을 실행한 뒤 새로고침하세요.
        </p>
      </CardContent>
    </Card>
  );
}
