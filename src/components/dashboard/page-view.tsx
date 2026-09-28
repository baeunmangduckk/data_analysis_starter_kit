import { DataMissing } from "@/components/dashboard/data-missing";
import { PageHeader } from "@/components/dashboard/page-header";
import { SectionRenderer } from "@/components/dashboard/section-renderer";
import { getPage } from "@/lib/data";

interface PageViewProps {
  slug: string;
}

// public/data/<slug>.json(PageData)을 읽어 헤더 + 섹션들로 렌더링한다.
// 라우트의 page.tsx는 <PageView slug="..." /> 한 줄이면 되고, 화면 구성은 JSON이 결정한다.
export async function PageView({ slug }: PageViewProps) {
  const page = await getPage(slug);
  if (!page) return <DataMissing file={`${slug}.json`} />;

  return (
    <>
      <PageHeader title={page.title} summary={page.summary} generatedAt={page.generatedAt} />
      <SectionRenderer sections={page.sections} />
    </>
  );
}
