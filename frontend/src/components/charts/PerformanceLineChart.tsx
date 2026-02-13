/**
 * PerformanceLineChart - Display portfolio performance over time
 */

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { PerformancePeriod } from "@/services/mcp-types";

interface PerformanceLineChartProps {
  data: PerformancePeriod[];
  title?: string;
  description?: string;
}

export function PerformanceLineChart({
  data,
  title = "Portfolio Performance",
  description = "Historical value and performance",
}: PerformanceLineChartProps) {
  // Transform data for Recharts
  const chartData = data.map((period) => ({
    date: new Date(period.to_date).toLocaleDateString("en-US", {
      month: "short",
      year: "numeric",
    }),
    value: period.end_value,
    performance: period.cumulative_pct || period.performance_pct,
  }));

  // Custom tooltip
  function CustomTooltip({ active, payload }: any) {
    if (active && payload && payload.length) {
      return (
        <div className="rounded-lg border bg-background p-2 shadow-sm">
          <div className="grid gap-2">
            <div className="flex flex-col">
              <span className="text-[0.70rem] uppercase text-muted-foreground">
                Date
              </span>
              <span className="font-bold text-muted-foreground">
                {payload[0].payload.date}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-[0.70rem] uppercase text-muted-foreground">
                Value
              </span>
              <span className="font-bold">
                CHF {payload[0].value.toLocaleString("en-US", { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-[0.70rem] uppercase text-muted-foreground">
                Performance
              </span>
              <span className={`font-bold ${payload[1].value >= 0 ? "text-green-600" : "text-red-600"}`}>
                {payload[1].value >= 0 ? "+" : ""}
                {payload[1].value.toFixed(2)}%
              </span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="value"
              stroke="#8b5cf6"
              strokeWidth={2}
              name="Portfolio Value (CHF)"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="performance"
              stroke="#10b981"
              strokeWidth={2}
              name="Performance (%)"
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
