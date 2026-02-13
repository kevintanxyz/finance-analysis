/**
 * AllocationPieChart - Display portfolio allocation breakdown
 */

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { AllocationItem } from "@/services/mcp-types";

interface AllocationPieChartProps {
  data: AllocationItem[];
  title?: string;
  description?: string;
}

// Colors for different asset classes
const COLORS = {
  Cash: "#10b981", // green
  Bonds: "#3b82f6", // blue
  Equities: "#8b5cf6", // purple
  "Structured Products": "#f59e0b", // amber
  Others: "#6b7280", // gray
  // Fallback colors
  default: ["#ef4444", "#ec4899", "#14b8a6", "#f97316", "#eab308"],
};

function getColor(name: string, index: number): string {
  if (name in COLORS) {
    return COLORS[name as keyof typeof COLORS];
  }
  const defaultColors = COLORS.default;
  return defaultColors[index % defaultColors.length];
}

export function AllocationPieChart({
  data,
  title = "Asset Allocation",
  description = "Portfolio distribution by asset class",
}: AllocationPieChartProps) {
  // Transform data for Recharts
  const chartData = data.map((item) => ({
    name: item.asset_class,
    value: item.value_chf,
    weight: item.weight_pct,
  }));

  // Custom label showing percentage
  function renderLabel(entry: { name: string; weight: number }) {
    return `${entry.name}: ${entry.weight.toFixed(1)}%`;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={renderLabel}
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getColor(entry.name, index)} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number) => [
                `CHF ${value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
                "Value",
              ]}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
