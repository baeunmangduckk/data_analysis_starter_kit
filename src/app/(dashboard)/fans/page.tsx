import type { Metadata } from "next";
import { PlaceholderPage } from "@/components/dashboard/placeholder-page";

export const metadata: Metadata = { title: "팬 반응" };

export default function FansPage() {
  return <PlaceholderPage slug="fans" />;
}
