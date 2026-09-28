import type { Metadata } from "next";
import { PlaceholderPage } from "@/components/dashboard/placeholder-page";

export const metadata: Metadata = { title: "기획사 재무" };

export default function FinancePage() {
  return <PlaceholderPage slug="finance" />;
}
