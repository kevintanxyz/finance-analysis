/**
 * TypeScript types for MCP (Model Context Protocol) integration
 */

// MCP Tool Result Types
export interface MCPToolResult {
  content: Array<{
    type: "text" | "image" | "resource";
    text?: string;
    data?: string;
    uri?: string;
    mimeType?: string;
  }>;
  isError?: boolean;
}

// Portfolio-specific tool results
export interface PortfolioAllocation {
  equity_pct: number;
  bond_pct: number;
  cash_pct: number;
  other_pct: number;
}

export interface Position {
  ticker: string;
  name: string;
  quantity: number;
  value_chf: number;
  weight_pct: number;
  asset_class: string;
}

export interface RiskMetrics {
  var_95: number;
  beta: number;
  sharpe_ratio: number;
  volatility: number;
  max_drawdown: number;
}

export interface PerformancePeriod {
  from_date: string;
  to_date: string;
  start_value: number;
  end_value: number;
  profit_loss: number;
  performance_pct: number;
}

// MCP Request/Response Types
export interface MCPRequest {
  jsonrpc: "2.0";
  method: string;
  params: {
    name: string;
    arguments?: Record<string, unknown>;
  };
  id: number;
}

export interface MCPResponse<T = unknown> {
  jsonrpc: "2.0";
  result?: T;
  error?: {
    code: number;
    message: string;
    data?: unknown;
  };
  id: number;
}

// Chat Message Types
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  toolCalls?: ToolCall[];
  toolResults?: ToolResult[];
}

export interface ToolCall {
  toolName: string;
  arguments: Record<string, unknown>;
}

export interface ToolResult {
  toolName: string;
  displayType: "text" | "table" | "chart" | "error";
  data: unknown;
  error?: string;
}

// Display Type for Conditional Rendering
export type DisplayType = "text" | "table" | "chart" | "error";
