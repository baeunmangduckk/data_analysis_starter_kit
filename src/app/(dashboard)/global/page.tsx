import type { Metadata } from "next";
import { PageView } from "@/components/dashboard/page-view";

export const metadata: Metadata = { title: "글로벌 확장" };

export default function GlobalPage() {
  return <PageView slug="global" />;
}
