import type { Metadata } from "next";
import { PageView } from "@/components/dashboard/page-view";

export const metadata: Metadata = { title: "AI·버추얼 아이돌" };

export default function AiVirtualPage() {
  return <PageView slug="ai-virtual" />;
}
