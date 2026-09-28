import type { Metadata } from "next";
import { PageView } from "@/components/dashboard/page-view";

export const metadata: Metadata = { title: "팬 반응" };

export default function FansPage() {
  return <PageView slug="fans" />;
}
