import { PageHeader } from "@/components/dashboard/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { getNavItem } from "@/lib/nav";

interface PlaceholderPageProps {
  slug: string;
}

// 페이지 데이터가 연결되기 전까지 라우트와 사이드바 동작만 확인하기 위한 임시 화면.
// 각 페이지가 구현되면 이 컴포넌트 호출을 실제 화면으로 교체한다.
export function PlaceholderPage({ slug }: PlaceholderPageProps) {
  const item = getNavItem(slug);

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title={item.label} summary={item.description} />
      <Card>
        <CardContent className="py-10 text-center text-sm text-muted-foreground">
          이 페이지는 준비 중입니다.
        </CardContent>
      </Card>
    </div>
  );
}
