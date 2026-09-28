import Link from "next/link";
import { ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { NAV_ITEMS } from "@/lib/nav";
import type { Source } from "@/types/page";

interface SourceListProps {
  sources: Source[];
}

const PAGE_BY_SLUG = new Map(NAV_ITEMS.map((item) => [item.slug, item]));

export function SourceList({ sources }: SourceListProps) {
  // 화면에서 실제로 인용된 출처를 위로 올린다 (같은 그룹 안에서는 파일 순서 유지).
  const ordered = [...sources].sort((a, b) => Number(b.usedBy.length > 0) - Number(a.usedBy.length > 0));

  return (
    <Card>
      <CardContent className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>기관</TableHead>
              <TableHead>제목</TableHead>
              <TableHead className="text-right">연도</TableHead>
              <TableHead>비고</TableHead>
              <TableHead>사용처</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {ordered.map((source) => (
              <TableRow key={source.id}>
                <TableCell className="whitespace-normal font-medium">{source.org}</TableCell>
                <TableCell className="whitespace-normal">
                  {source.url ? (
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 underline-offset-4 hover:underline"
                    >
                      {source.title}
                      <ExternalLink className="size-3 shrink-0 text-muted-foreground" />
                    </a>
                  ) : (
                    source.title
                  )}
                </TableCell>
                <TableCell className="text-right tabular-nums">{source.year ?? "–"}</TableCell>
                <TableCell className="min-w-48 whitespace-normal text-muted-foreground">{source.note ?? "–"}</TableCell>
                <TableCell>
                  {source.usedBy.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                      {source.usedBy.map((slug) => {
                        const page = PAGE_BY_SLUG.get(slug);
                        return (
                          <Badge key={slug} variant="secondary" render={<Link href={page?.href ?? "/"} />}>
                            {page?.label ?? slug}
                          </Badge>
                        );
                      })}
                    </div>
                  ) : (
                    <span className="text-muted-foreground">–</span>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
