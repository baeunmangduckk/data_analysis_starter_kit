import type { Metadata } from "next";
import { DataMissing } from "@/components/dashboard/data-missing";
import { PageHeader } from "@/components/dashboard/page-header";
import { SourceList } from "@/components/dashboard/source-list";
import { getSources } from "@/lib/data";
import { getNavItem } from "@/lib/nav";

export const metadata: Metadata = { title: "출처" };

export default async function SourcesPage() {
  const data = await getSources();
  const item = getNavItem("sources");
  if (!data) return <DataMissing file="sources.json" />;

  const usedCount = data.sources.filter((source) => source.usedBy.length > 0).length;

  return (
    <>
      <PageHeader
        title={item.label}
        summary={`총 ${data.sources.length}건 중 ${usedCount}건이 화면에서 인용됩니다.`}
        generatedAt={data.generatedAt}
      />
      <SourceList sources={data.sources} />
    </>
  );
}
