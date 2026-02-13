/**
 * ChatToolResult - Conditional rendering of tool results
 * Handles text, table, chart, and error display types
 */

import { Card } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import type { ToolResult, AllocationItem, PerformancePeriod } from "@/services/mcp-types";
import ReactMarkdown from "react-markdown";
import { AllocationPieChart } from "@/components/charts/AllocationPieChart";
import { PerformanceLineChart } from "@/components/charts/PerformanceLineChart";

interface ChatToolResultProps {
  result: ToolResult;
}

export function ChatToolResult({ result }: ChatToolResultProps) {
  // Error display
  if (result.displayType === "error") {
    return (
      <Alert variant="destructive" className="mt-2">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>
          {result.error || "An error occurred while processing your request"}
        </AlertDescription>
      </Alert>
    );
  }

  // Text display (with markdown support)
  if (result.displayType === "text") {
    return (
      <Card className="mt-2 p-4">
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown>{String(result.data)}</ReactMarkdown>
        </div>
      </Card>
    );
  }

  // Table display
  if (result.displayType === "table") {
    const tableData = result.data as Array<Record<string, unknown>>;
    if (!tableData || tableData.length === 0) {
      return (
        <Card className="mt-2 p-4">
          <p className="text-sm text-muted-foreground">No data available</p>
        </Card>
      );
    }

    const columns = Object.keys(tableData[0]);

    return (
      <Card className="mt-2 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/50">
              <tr>
                {columns.map((col) => (
                  <th
                    key={col}
                    className="px-4 py-2 text-left font-medium capitalize"
                  >
                    {col.replace(/_/g, " ")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableData.map((row, idx) => (
                <tr key={idx} className="border-b last:border-0">
                  {columns.map((col) => (
                    <td key={col} className="px-4 py-2">
                      {String(row[col])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    );
  }

  // Chart display with Recharts integration
  if (result.displayType === "chart") {
    const chartData = result.data as any;

    // Check if data is empty
    if (!chartData || (Array.isArray(chartData) && chartData.length === 0)) {
      return (
        <Card className="mt-2 p-4">
          <p className="text-sm text-muted-foreground">No chart data available</p>
        </Card>
      );
    }

    // Detect allocation data (has asset_class, value_chf, weight_pct)
    if (
      Array.isArray(chartData) &&
      chartData.length > 0 &&
      "asset_class" in chartData[0] &&
      "value_chf" in chartData[0]
    ) {
      return (
        <div className="mt-2">
          <AllocationPieChart data={chartData as AllocationItem[]} />
        </div>
      );
    }

    // Detect performance data (has from_date, to_date, performance_pct)
    if (
      Array.isArray(chartData) &&
      chartData.length > 0 &&
      "from_date" in chartData[0] &&
      "to_date" in chartData[0] &&
      "performance_pct" in chartData[0]
    ) {
      return (
        <div className="mt-2">
          <PerformanceLineChart data={chartData as PerformancePeriod[]} />
        </div>
      );
    }

    // Fallback for unknown chart types
    return (
      <Card className="mt-2 p-4">
        <p className="text-sm text-muted-foreground mb-2">
          Chart type not yet supported
        </p>
        <pre className="text-xs overflow-auto">{JSON.stringify(chartData, null, 2)}</pre>
      </Card>
    );
  }

  // Fallback for unknown types
  return (
    <Card className="mt-2 p-4">
      <pre className="text-xs">{JSON.stringify(result.data, null, 2)}</pre>
    </Card>
  );
}
