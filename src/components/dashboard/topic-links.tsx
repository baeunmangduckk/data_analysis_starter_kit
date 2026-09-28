import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { NAV_ITEMS } from "@/lib/nav";

// 홈에서 각 주제 페이지로 들어가는 링크 카드. 사이드바와 같은 nav.ts를 쓰므로 페이지를 추가하면 함께 나타난다.
export function TopicLinks() {
  const topics = NAV_ITEMS.filter((item) => item.slug !== "home");

  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-base font-semibold">주제별 살펴보기</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {topics.map((topic) => (
          <Link key={topic.slug} href={topic.href} className="group rounded-xl focus-visible:outline-2 focus-visible:outline-ring">
            <Card className="h-full transition-colors group-hover:bg-muted/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <topic.icon className="size-4 text-muted-foreground" />
                  {topic.label}
                  <ArrowRight className="ml-auto size-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{topic.description}</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </section>
  );
}
