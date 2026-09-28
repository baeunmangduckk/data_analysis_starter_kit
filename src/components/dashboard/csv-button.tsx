"use client";

import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { TableColumn } from "@/types/page";

interface CsvButtonProps {
  filename: string;
  columns: TableColumn[];
  rows: Record<string, string | number | null>[];
}

function escapeCsv(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "";
  const text = String(value);
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

export function CsvButton({ filename, columns, rows }: CsvButtonProps) {
  const handleDownload = () => {
    const header = columns.map((column) => escapeCsv(column.label)).join(",");
    const lines = rows.map((row) => columns.map((column) => escapeCsv(row[column.key])).join(","));
    // BOM을 붙여야 Excel이 한글 CSV를 UTF-8로 올바르게 연다.
    const blob = new Blob(["﻿" + [header, ...lines].join("\n")], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${filename}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Button variant="outline" size="sm" onClick={handleDownload}>
      <Download />
      CSV
    </Button>
  );
}
