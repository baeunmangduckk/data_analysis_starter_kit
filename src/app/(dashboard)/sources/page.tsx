import type { Metadata } from "next";
import { PlaceholderPage } from "@/components/dashboard/placeholder-page";

export const metadata: Metadata = { title: "출처" };

export default function SourcesPage() {
  return <PlaceholderPage slug="sources" />;
}
