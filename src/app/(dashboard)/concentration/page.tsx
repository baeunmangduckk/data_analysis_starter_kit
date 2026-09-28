import type { Metadata } from "next";
import { PlaceholderPage } from "@/components/dashboard/placeholder-page";

export const metadata: Metadata = { title: "판매 집중도·양극화" };

export default function ConcentrationPage() {
  return <PlaceholderPage slug="concentration" />;
}
