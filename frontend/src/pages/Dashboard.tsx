/**
 * Dashboard Page - Portfolio Overview with KPIs and Charts
 */

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, TrendingUp, DollarSign, PieChart, AlertCircle } from "lucide-react";
import { AllocationPieChart } from "@/components/charts/AllocationPieChart";
import { PerformanceLineChart } from "@/components/charts/PerformanceLineChart";
import { getPortfolioAllocation, analyzeRisk } from "@/services/mcp-tools";
import type { AllocationItem, PerformancePeriod, RiskMetrics } from "@/services/mcp-types";

export default function Dashboard() {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [allocation, setAllocation] = useState<AllocationItem[]>([]);
  const [performance, setPerformance] = useState<PerformancePeriod[]>([]);
  const [totalValue, setTotalValue] = useState<number>(0);
  const [riskMetrics, setRiskMetrics] = useState<RiskMetrics | null>(null);

  // Fetch portfolio data on mount
  useEffect(() => {
    async function loadDashboardData() {
      try {
        setIsLoading(true);
        setError(null);

        // Get active session ID from localStorage (set by PDF upload)
        const sessionId = localStorage.getItem("activeSessionId");

        if (!sessionId) {
          setError("No portfolio loaded. Please upload a PDF first.");
          setIsLoading(false);
          return;
        }

        // Fetch allocation data
        const allocationResult = await getPortfolioAllocation(sessionId);
        setAllocation(allocationResult.allocation);
        setPerformance(allocationResult.performance || []);
        setTotalValue(allocationResult.total_value);

        // Fetch risk metrics
        try {
          const riskResult = await analyzeRisk(sessionId);
          setRiskMetrics(riskResult.risk_metrics);
        } catch (riskError) {
          console.warn("Could not load risk metrics:", riskError);
          // Don't fail the whole dashboard if risk metrics fail
        }

        setIsLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load dashboard data");
        setIsLoading(false);
      }
    }

    loadDashboardData();
  }, []);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-120px)] items-center justify-center">
        <div className="flex flex-col items-center gap-2">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="container mx-auto py-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  // Calculate summary metrics
  const equityAllocation = allocation.find((a) => a.asset_class === "Equities")?.weight_pct || 0;
  const bondAllocation = allocation.find((a) => a.asset_class === "Bonds")?.weight_pct || 0;
  const latestPerformance = performance.length > 0 ? performance[performance.length - 1] : null;
  const performancePct = latestPerformance?.performance_pct || 0;

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Portfolio Dashboard</h1>
        <p className="text-muted-foreground">
          Overview of your investments, allocation, and performance
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Total Value */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Value</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              CHF {totalValue.toLocaleString("en-US", { minimumFractionDigits: 2 })}
            </div>
            <p className="text-xs text-muted-foreground">Portfolio net worth</p>
          </CardContent>
        </Card>

        {/* Performance */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Performance</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${performancePct >= 0 ? "text-green-600" : "text-red-600"}`}>
              {performancePct >= 0 ? "+" : ""}{performancePct.toFixed(2)}%
            </div>
            <p className="text-xs text-muted-foreground">
              {latestPerformance ? `Since ${new Date(latestPerformance.from_date).toLocaleDateString()}` : "No data"}
            </p>
          </CardContent>
        </Card>

        {/* Equity Allocation */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Equity Allocation</CardTitle>
            <PieChart className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{equityAllocation.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">Stock exposure</p>
          </CardContent>
        </Card>

        {/* Risk Metric */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Portfolio Risk</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {riskMetrics?.risk_score ? riskMetrics.risk_score.toFixed(1) : "N/A"}
            </div>
            <p className="text-xs text-muted-foreground">
              {riskMetrics?.volatility ? `Volatility: ${(riskMetrics.volatility * 100).toFixed(1)}%` : "No data"}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Allocation Chart */}
        {allocation.length > 0 && <AllocationPieChart data={allocation} />}

        {/* Performance Chart */}
        {performance.length > 0 && <PerformanceLineChart data={performance} />}
      </div>

      {/* Empty state if no charts */}
      {allocation.length === 0 && performance.length === 0 && (
        <Card>
          <CardHeader>
            <CardTitle>No data available</CardTitle>
            <CardDescription>
              Upload a portfolio PDF to see your allocation and performance charts
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      {/* Top Positions Table */}
      {allocation.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Asset Allocation Breakdown</CardTitle>
            <CardDescription>Detailed view of your portfolio allocation</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="relative w-full overflow-auto">
              <table className="w-full caption-bottom text-sm">
                <thead className="[&_tr]:border-b">
                  <tr className="border-b transition-colors hover:bg-muted/50">
                    <th className="h-12 px-4 text-left align-middle font-medium">Asset Class</th>
                    <th className="h-12 px-4 text-right align-middle font-medium">Value (CHF)</th>
                    <th className="h-12 px-4 text-right align-middle font-medium">Weight (%)</th>
                  </tr>
                </thead>
                <tbody className="[&_tr:last-child]:border-0">
                  {allocation.map((item, idx) => (
                    <tr key={idx} className="border-b transition-colors hover:bg-muted/50">
                      <td className="p-4 align-middle">{item.asset_class}</td>
                      <td className="p-4 align-middle text-right">
                        {item.value_chf.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                      </td>
                      <td className="p-4 align-middle text-right">{item.weight_pct.toFixed(2)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
