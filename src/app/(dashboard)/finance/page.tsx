import type { Metadata } from "next";
import { PageView } from "@/components/dashboard/page-view";

export const metadata: Metadata = { title: "기획사 재무" };

export default function FinancePage() {
  return <PageView slug="finance" />;
}
