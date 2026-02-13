/**
 * Flow Response Table Component
 *
 * Table view showing all outputs as rows with sorting, filtering, and CSV export
 */

"use client";

import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";
import { Download } from "lucide-react";
import Papa from "papaparse";
import { useMemo, useState } from "react";

import { FeedbackButton } from "@/components/feedback";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { getTelemetryIdsFromMetadata, METADATA_FIELD } from "@/lib/telemetry";

import type { SchemaProperty, ResponseData } from "@/types";
import type { FeedbackConfig } from "@/types/FlowMetadata";

interface FlowResponseTableProps {
  responseSchema?: SchemaProperty | null;
  outputs: ResponseData[];
  feedbackConfig?: FeedbackConfig | null;
  telemetryEnabled?: boolean;
}

function formatCellValue(value: ResponseData, qtypeType?: string): string {
  if (value === null || value === undefined) return "";

  try {
    if (
      qtypeType &&
      [
        "image",
        "video",
        "audio",
        "file",
        "citation_document",
        "bytes",
      ].includes(qtypeType)
    ) {
      const parsed = JSON.parse(String(value));
      return parsed.filename || `[${qtypeType}]`;
    }
  } catch {
    // Ignore parsing errors
  }

  if (typeof value === "object") {
    return JSON.stringify(value);
  }

  return String(value);
}

export default function FlowResponseTable({
  responseSchema,
  outputs,
  feedbackConfig,
  telemetryEnabled = false,
}: FlowResponseTableProps) {
  const [searchText, setSearchText] = useState("");
  const [sorting, setSorting] = useState<SortingState>([]);

  const data = useMemo(() => {
    return outputs.map((output) => {
      const outputData =
        output && typeof output === "object"
          ? (output as Record<string, ResponseData>).outputs || output
          : output || {};
      return outputData as Record<string, ResponseData>;
    });
  }, [outputs]);

  const columns = useMemo<ColumnDef<Record<string, ResponseData>>[]>(() => {
    if (!responseSchema?.properties) return [];

    const dataColumns: ColumnDef<Record<string, ResponseData>>[] =
      Object.entries(responseSchema.properties)
        .filter(([key]) => key !== METADATA_FIELD)
        .map(([key, schema]) => {
          const prop = schema as SchemaProperty;
          return {
            accessorKey: key,
            header: prop.title || key,
            cell: (ctx) => {
              const value = ctx.row.original[key];
              return formatCellValue(value, prop.qtype_type);
            },
          };
        });

    // Add feedback column if enabled
    if (feedbackConfig && telemetryEnabled) {
      dataColumns.push({
        id: "feedback",
        header: "Feedback",
        cell: (ctx) => {
          const telemetryIds = getTelemetryIdsFromMetadata(
            ctx.row.original[METADATA_FIELD],
          );

          if (!telemetryIds) {
            return null;
          }

          return (
            <FeedbackButton
              feedbackConfig={feedbackConfig}
              spanId={telemetryIds.spanId}
              traceId={telemetryIds.traceId}
            />
          );
        },
      });
    }

    return dataColumns;
  }, [responseSchema, feedbackConfig, telemetryEnabled]);

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      globalFilter: searchText,
    },
    onSortingChange: setSorting,
    onGlobalFilterChange: setSearchText,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  const handleDownloadCSV = () => {
    const exportableProperties = Object.entries(
      responseSchema?.properties ?? {},
    )
      .filter(([key]) => key !== METADATA_FIELD)
      .map(([key, schema]) => ({
        key,
        schema: schema as SchemaProperty,
      }));

    const csvData = table.getFilteredRowModel().rows.map((row) => {
      const rowData: Record<string, string> = {};

      for (const { key, schema } of exportableProperties) {
        const header = schema.title || key;
        rowData[header] = formatCellValue(row.original[key], schema.qtype_type);
      }

      return rowData;
    });

    const csv = Papa.unparse(csvData);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    const timestamp = new Date().toISOString().split("T")[0];
    link.setAttribute("href", url);
    link.setAttribute("download", `flow-results-${timestamp}.csv`);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (!outputs || outputs.length === 0) {
    return (
      <div className="text-gray-500 dark:text-gray-400 text-sm">
        No response data to display
      </div>
    );
  }

  if (!responseSchema?.properties || columns.length === 0) {
    return (
      <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded">
        <pre className="text-xs text-gray-800 dark:text-gray-200 overflow-x-auto whitespace-pre-wrap">
          {JSON.stringify(outputs, null, 2)}
        </pre>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <Input
          placeholder="Search all columns..."
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          className="max-w-sm"
        />
        <Button onClick={handleDownloadCSV} variant="outline" size="sm">
          <Download className="mr-2 h-4 w-4" />
          Download CSV
        </Button>
      </div>

      <div className="border rounded-lg overflow-hidden">
        <div className="overflow-auto" style={{ maxHeight: "400px" }}>
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-900 sticky top-0">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <th
                      key={header.id}
                      className="px-4 py-2 text-left font-medium cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                      onClick={header.column.getToggleSortingHandler()}
                    >
                      <div className="flex items-center gap-2">
                        {flexRender(
                          header.column.columnDef.header,
                          header.getContext(),
                        )}
                        {{
                          asc: " 🔼",
                          desc: " 🔽",
                        }[header.column.getIsSorted() as string] ?? null}
                      </div>
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  className="border-t hover:bg-gray-50 dark:hover:bg-gray-900"
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-2">
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext(),
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="text-sm text-muted-foreground">
        {table.getFilteredRowModel().rows.length} row(s) total
      </div>
    </div>
  );
}
