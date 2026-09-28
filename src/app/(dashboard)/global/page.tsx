import type { Metadata } from "next";
import { PlaceholderPage } from "@/components/dashboard/placeholder-page";

export const metadata: Metadata = { title: "글로벌 확장" };

export default function GlobalPage() {
  return <PlaceholderPage slug="global" />;
}
