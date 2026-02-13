/**
 * Typed wrappers for WealthPoint MCP tools
 * Provides type-safe access to all 16 portfolio analysis tools
 */

import { mcpClient } from "./mcp-client";
import type {
  PortfolioAllocation,
  Position,
  RiskMetrics,
  PerformancePeriod,
} from "./mcp-types";

/**
 * Upload portfolio PDF
 */
export async function uploadPortfolio(pdfBase64: string, filename: string) {
  return mcpClient.callTool<{ session_id: string; status: string }>(
    "upload_portfolio",
    {
      pdf_base64: pdfBase64,
      filename,
    },
  );
}

/**
 * Get portfolio allocation breakdown
 */
export async function getPortfolioAllocation(sessionId: string) {
  return mcpClient.callTool<{
    allocation: PortfolioAllocation;
    positions: Position[];
    total_value_chf: number;
  }>("get_portfolio_allocation", {
    session_id: sessionId,
  });
}

/**
 * Analyze portfolio risk
 */
export async function analyzeRisk(sessionId: string, ticker: string) {
  return mcpClient.callTool<RiskMetrics>("analyze_risk", {
    session_id: sessionId,
    ticker,
  });
}

/**
 * Analyze momentum indicators
 */
export async function analyzeMomentum(sessionId: string, ticker: string) {
  return mcpClient.callTool<{
    rsi_14: number;
    macd: { value: number; signal: number; histogram: number };
    sma_50: number;
    sma_200: number;
  }>("analyze_momentum", {
    session_id: sessionId,
    ticker,
  });
}

/**
 * Analyze correlation between tickers
 */
export async function analyzeCorrelation(
  sessionId: string,
  tickers: string[],
) {
  return mcpClient.callTool<{
    correlation_matrix: Record<string, Record<string, number>>;
  }>("analyze_correlation", {
    session_id: sessionId,
    tickers,
  });
}

/**
 * Get market data for positions
 */
export async function getMarketData(sessionId: string) {
  return mcpClient.callTool<{
    market_data: Array<{
      ticker: string;
      price: number;
      change_pct: number;
      volume: number;
    }>;
  }>("get_market_data", {
    session_id: sessionId,
  });
}

/**
 * Analyze portfolio profile (risk tolerance, objectives)
 */
export async function analyzePortfolioProfile(sessionId: string) {
  return mcpClient.callTool<{
    profile: {
      risk_tolerance: string;
      risk_score_pct: number;
      investment_objectives: string[];
      experience_level: string;
    };
    allocation_breakdown: PortfolioAllocation;
  }>("analyze_portfolio_profile", {
    session_id: sessionId,
  });
}

/**
 * Recommend portfolio rebalancing
 */
export async function recommendRebalancing(
  sessionId: string,
  targetAllocation?: PortfolioAllocation,
) {
  return mcpClient.callTool<{
    rebalancing_required: boolean;
    recommendations: Array<{
      asset_class: string;
      action: string;
      amount_chf: number;
      priority: string;
    }>;
  }>("recommend_rebalancing", {
    session_id: sessionId,
    target_allocation: targetAllocation,
  });
}

/**
 * Analyze dividends
 */
export async function analyzeDividends(sessionId: string) {
  return mcpClient.callTool<{
    portfolio_dividend_yield: number;
    annual_income_chf: number;
    top_contributors: Array<{
      ticker: string;
      dividend_yield: number;
      annual_dividend_chf: number;
    }>;
  }>("analyze_dividends", {
    session_id: sessionId,
  });
}

/**
 * Check compliance
 */
export async function checkCompliance(
  sessionId: string,
  limits?: {
    max_position_pct?: number;
    max_asset_class_pct?: number;
    min_positions?: number;
  },
) {
  return mcpClient.callTool<{
    compliant: boolean;
    violations: Array<{
      severity: string;
      description: string;
      amount_chf: number;
    }>;
  }>("check_compliance", {
    session_id: sessionId,
    limits,
  });
}

/**
 * Generate full portfolio report (orchestrates 8 analysis sections)
 */
export async function generateFullReport(sessionId: string) {
  return mcpClient.callTool<{
    sections: {
      allocation: unknown;
      compliance: unknown;
      market_data: unknown;
      dividends: unknown;
      margin: unknown;
      risk: unknown;
      momentum: unknown;
      correlation: unknown;
    };
    executive_summary: {
      compliant: boolean;
      dividend_yield: number;
      leverage_ratio: number;
      diversification_score: number;
    };
  }>("generate_full_report", {
    session_id: sessionId,
  });
}

/**
 * Ask natural language question about portfolio
 */
export async function askPortfolio(sessionId: string, question: string) {
  const result = await mcpClient.callTool<{
    content: string;
    display_type: string;
    tables?: Array<{
      title: string;
      columns: Array<{ key: string; label: string; type: string }>;
      rows: Array<Record<string, unknown>>;
    }>;
    charts?: unknown;
    kpis?: unknown;
  }>("ask_portfolio", {
    session_id: sessionId,
    question,
  });

  // Return the full structured response
  return result;
}

/**
 * List all available MCP tools
 */
export async function listAvailableTools() {
  return mcpClient.listTools();
}
