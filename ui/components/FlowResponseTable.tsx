/**
 * Flow Response Table Component
 *
 * Table view showing all outputs as rows with sorting, filtering, and CSV export
 */

"use client";

import "react-data-grid/lib/styles.css";

import { Download } from "lucide-react";
import Papa from "papaparse";
import { useMemo, useState } from "react";
import { DataGrid, type Column } from "react-data-grid";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

import type { SchemaProperty, ResponseData } from "@/types";

interface FlowResponseTableProps {
  responseSchema?: SchemaProperty | null;
  outputs: ResponseData[];
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
}: FlowResponseTableProps) {
  const [searchText, setSearchText] = useState("");

  const rows = useMemo(() => {
    return outputs.map((output) => {
      const outputData =
        output && typeof output === "object"
          ? (output as Record<string, ResponseData>).outputs || output
          : output || {};
      return outputData as Record<string, ResponseData>;
    });
  }, [outputs]);

  const columns = useMemo<Column<Record<string, ResponseData>>[]>(() => {
    if (!responseSchema?.properties) return [];

    return Object.entries(responseSchema.properties).map(([key, schema]) => {
      const prop = schema as SchemaProperty;
      return {
        key,
        name: prop.title || key,
        sortable: true,
        resizable: true,
        renderCell: ({ row }) => {
          const value = row[key];
          return formatCellValue(value, prop.qtype_type);
        },
      };
    });
  }, [responseSchema]);

  const filteredRows = useMemo(() => {
    if (!searchText) return rows;

    return rows.filter((row) =>
      Object.values(row).some((value) =>
        String(value).toLowerCase().includes(searchText.toLowerCase()),
      ),
    );
  }, [rows, searchText]);

  const handleDownloadCSV = () => {
    const csvData = filteredRows.map((row) => {
      const rowData: Record<string, string> = {};
      columns.forEach((col) => {
        const propertySchema = responseSchema?.properties?.[
          col.key as string
        ] as SchemaProperty | undefined;
        rowData[col.name as string] = formatCellValue(
          row[col.key as string],
          propertySchema?.qtype_type,
        );
      });
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

      <div className="rdg-light">
        <DataGrid
          columns={columns}
          rows={filteredRows}
          className="fill-grid"
          style={{ height: "400px" }}
        />
      </div>

      <div className="text-sm text-muted-foreground">
        {filteredRows.length} row(s) total
      </div>
    </div>
  );
}
