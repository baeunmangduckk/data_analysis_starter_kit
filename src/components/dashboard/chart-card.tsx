"use client";

import { useState } from "react";
import { ChartColumn, Table2 } from "lucide-react";
import { CsvButton } from "@/components/dashboard/csv-button";
import { DataTable } from "@/components/dashboard/data-table";
import { MultiSeriesChart } from "@/components/dashboard/multi-series-chart";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ChartSection, TableColumn } from "@/types/page";

interface ChartCardProps {
  section: ChartSection;
}

// 차트와 같은 데이터를 표로도 볼 수 있게 한다 — 색만으로 구분하기 어려운 사용자와
// 정확한 수치를 확인하려는 사용자를 위한 대체 뷰이며, CSV로 내려받을 수도 있다.
export function ChartCard({ section }: ChartCardProps) {
  const [showTable, setShowTable] = useState(false);

  const columns: TableColumn[] = [
    { key: section.xKey, label: "구분", align: "left" },
    ...section.series.map((s) => ({ key: s.key, label: s.label, align: "right" as const })),
  ];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div className="flex flex-col gap-1">
            <CardTitle>{section.title}</CardTitle>
            {section.caption ? <p className="text-xs text-muted-foreground">{section.caption}</p> : null}
          </div>
          <div className="flex shrink-0 items-center gap-1">
            <Button variant="outline" size="sm" onClick={() => setShowTable((prev) => !prev)}>
              {showTable ? <ChartColumn /> : <Table2 />}
              {showTable ? "차트로 보기" : "표로 보기"}
            </Button>
            <CsvButton filename={section.title} columns={columns} rows={section.points} />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {showTable ? <DataTable columns={columns} rows={section.points} /> : <MultiSeriesChart section={section} />}
      </CardContent>
    </Card>
  );
}
