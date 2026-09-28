import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { TableColumn } from "@/types/page";

interface DataTableProps {
  columns: TableColumn[];
  rows: Record<string, string | number | null>[];
}

const numberFormatter = new Intl.NumberFormat("ko-KR");

// null은 결측이므로 빈 칸 대신 대시로 표시해 "값이 0"인 것과 구분한다.
function formatCell(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "–";
  return typeof value === "number" ? numberFormatter.format(value) : value;
}

export function DataTable({ columns, rows }: DataTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          {columns.map((column) => (
            <TableHead key={column.key} className={column.align === "right" ? "text-right" : undefined}>
              {column.label}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((row, index) => (
          <TableRow key={index}>
            {columns.map((column) => (
              <TableCell key={column.key} className={column.align === "right" ? "text-right tabular-nums" : undefined}>
                {formatCell(row[column.key])}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
