import type { Metadata } from "next";
import { PageView } from "@/components/dashboard/page-view";

export const metadata: Metadata = { title: "판매 집중도·양극화" };

export default function ConcentrationPage() {
  return <PageView slug="concentration" />;
}
