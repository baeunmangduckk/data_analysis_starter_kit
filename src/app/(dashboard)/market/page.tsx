import type { Metadata } from "next";
import { PageView } from "@/components/dashboard/page-view";

export const metadata: Metadata = { title: "시장 전망" };

export default function MarketPage() {
  return <PageView slug="market" />;
}
