import type { Metadata } from "next";
import { PlaceholderPage } from "@/components/dashboard/placeholder-page";

export const metadata: Metadata = { title: "시장 전망" };

export default function MarketPage() {
  return <PlaceholderPage slug="market" />;
}
