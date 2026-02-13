/**
 * MCP Client - HTTP API client
 * Connects to WealthPoint Analysis HTTP API on port 3001
 */

import axios, { type AxiosInstance } from "axios";

const API_URL = import.meta.env.VITE_MCP_SERVER_URL || "http://localhost:3001";

class MCPClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      timeout: 0, // No timeout - Claude API with tools can take time
      headers: {
        "Content-Type": "application/json",
      },
    });
  }

  /**
   * Call an MCP tool via HTTP API
   */
  async callTool<T = unknown>(
    toolName: string,
    toolArguments?: Record<string, unknown>,
  ): Promise<T> {
    try {
      const response = await this.client.post<{ result: T; error: string | null }>(
        "/tools/call",
        {
          tool_name: toolName,
          arguments: toolArguments || {},
        },
      );

      if (response.data.error) {
        throw new Error(response.data.error);
      }

      return response.data.result as T;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const errorMsg = error.response?.data?.error || error.message;
        throw new Error(`Tool call failed: ${errorMsg}`);
      }
      throw error;
    }
  }

  /**
   * List available MCP tools
   */
  async listTools(): Promise<Array<{ name: string; description: string }>> {
    try {
      const response = await this.client.get<{ tools: Array<{ name: string; description: string }> }>(
        "/tools",
      );
      return response.data.tools;
    } catch (error) {
      console.error("Failed to list tools:", error);
      return [];
    }
  }

  /**
   * Health check
   */
  async ping(): Promise<boolean> {
    try {
      const response = await this.client.get("/");
      return response.status === 200;
    } catch {
      return false;
    }
  }

  /**
   * Chat with Claude AI (with MCP tools access)
   * This provides the same experience as Claude Desktop
   */
  async chat(params: {
    message: string;
    sessionId?: string;
    history?: Array<{ role: string; content: string }>;
  }): Promise<{
    message: string;
    session_id?: string;
    model: string;
    stop_reason: string;
  }> {
    try {
      const response = await this.client.post<{
        message: string;
        session_id?: string;
        model: string;
        stop_reason: string;
      }>("/chat", {
        message: params.message,
        session_id: params.sessionId || null,
        history: params.history || [],
      });

      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const errorMsg = error.response?.data?.detail || error.message;
        throw new Error(`Chat failed: ${errorMsg}`);
      }
      throw error;
    }
  }

  /**
   * Chat with Claude AI using streaming (real-time updates)
   * Shows tool execution status like Claude Desktop
   */
  async chatStream(
    params: {
      message: string;
      sessionId?: string;
      history?: Array<{ role: string; content: string }>;
    },
    callbacks: {
      onText?: (text: string) => void;
      onStatus?: (status: string) => void;
      onComplete?: (fullMessage: string) => void;
      onError?: (error: Error) => void;
    }
  ): Promise<void> {
    try {
      const response = await fetch(`${API_URL}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: params.message,
          session_id: params.sessionId || null,
          history: params.history || [],
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("Response body is not readable");
      }

      const decoder = new TextDecoder();
      let buffer = "";
      let fullMessage = "";

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          break;
        }

        // Decode the chunk and add to buffer
        buffer += decoder.decode(value, { stream: true });

        // Process complete SSE messages (separated by \n\n)
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || ""; // Keep incomplete message in buffer

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const jsonStr = line.slice(6); // Remove "data: " prefix

            try {
              const data = JSON.parse(jsonStr);

              if (data.type === "text") {
                fullMessage += data.content;
                callbacks.onText?.(data.content);
              } else if (data.type === "status") {
                callbacks.onStatus?.(data.message);
              } else if (data.type === "error") {
                callbacks.onError?.(new Error(data.message));
              }
            } catch (e) {
              console.error("Failed to parse SSE message:", jsonStr, e);
            }
          }
        }
      }

      callbacks.onComplete?.(fullMessage);
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      callbacks.onError?.(err);
      throw err;
    }
  }
}

// Singleton instance
export const mcpClient = new MCPClient();
