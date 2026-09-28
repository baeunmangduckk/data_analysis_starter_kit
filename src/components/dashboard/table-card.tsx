import { CsvButton } from "@/components/dashboard/csv-button";
import { DataTable } from "@/components/dashboard/data-table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TableSection } from "@/types/page";

interface TableCardProps {
  section: TableSection;
}

export function TableCard({ section }: TableCardProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div className="flex flex-col gap-1">
            <CardTitle>{section.title}</CardTitle>
            {section.caption ? <p className="text-xs text-muted-foreground">{section.caption}</p> : null}
          </div>
          <CsvButton filename={section.title} columns={section.columns} rows={section.rows} />
        </div>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        <DataTable columns={section.columns} rows={section.rows} />
      </CardContent>
    </Card>
  );
}
