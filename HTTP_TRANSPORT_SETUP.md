# Phase 3.4 — Streamable HTTP Transport Setup Guide

**Status**: ⚠️ Ready for Testing (Requires Python 3.10+)
**Date**: February 12, 2026

---

## Overview

Phase 3.4 enables the WealthPoint MCP server to accept connections from React frontends and other HTTP clients using **Streamable HTTP** transport. This is in addition to the existing stdio transport used by Claude Desktop and Claude Code.

```
┌─────────────────────────────────────────────────┐
│  CLIENTS                                        │
│                                                 │
│  stdio:                                         │
│  - Claude Desktop                               │
│  - Claude Code                                  │
│  - Cursor                                       │
│                                                 │
│  HTTP (Streamable):                             │
│  - React Chat Frontend                          │
│  - Custom web applications                      │
│  - Remote MCP clients                           │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│  WealthPoint MCP Server                         │
│  (FastMCP)                                      │
│                                                 │
│  Port 3001 (HTTP)                               │
│  - Tools: upload_portfolio, ask, analyze_risk   │
│  - Resources: portfolio://{id}, positions://... │
│  - Prompts: portfolio-summary, risk-report      │
└─────────────────────────────────────────────────┘
```

---

## Requirements

### ⚠️ Critical: Python Version

**The MCP SDK requires Python 3.10 or higher.**

Current environment: Python 3.9.17 ❌
Required: Python 3.10+ ✅

**Setup Python 3.10+ with pyenv:**

```bash
# Install Python 3.10 or higher
pyenv install 3.10.13  # or 3.11, 3.12

# Set local Python version for this project
cd /Users/kevintan/Documents/Projects/wealthpoint-projects/finance-analysis
pyenv local 3.10.13

# Verify
python --version  # Should show Python 3.10.13
```

### Dependencies

Once Python 3.10+ is active:

```bash
# Install all requirements
pip install -r requirements.txt

# Verify MCP is installed
pip show mcp
# Should show version 1.0.0 or higher
```

**Key dependencies for HTTP transport:**
- `mcp>=1.0.0` — MCP SDK with FastMCP
- `anthropic>=0.39.0` — Claude API client
- `httpx>=0.27.0` — Async HTTP client
- `starlette` — ASGI framework (auto-installed with mcp)
- `uvicorn` — ASGI server (auto-installed with mcp)

---

## Server Implementation

The MCP server already has Streamable HTTP support implemented in [mcp_server/server.py](mcp_server/server.py):

```python
# mcp_server/server.py (lines 57-79)

if __name__ == "__main__":
    # Parse command line arguments
    transport = "stdio"  # Default
    port = 3001

    if "--transport" in sys.argv:
        idx = sys.argv.index("--transport")
        if idx + 1 < len(sys.argv):
            transport = sys.argv[idx + 1]

    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])

    # Run server
    if transport == "streamable-http":
        # Streamable HTTP mode (for React frontend)
        print(f"Starting WealthPoint Analysis MCP Server in Streamable HTTP mode on port {port}...")
        mcp.run(transport="streamable-http", port=port)
    else:
        # stdio mode (for Claude Desktop, Claude Code)
        print("Starting WealthPoint Analysis MCP Server in stdio mode...", file=sys.stderr)
        mcp.run()
```

**How it works:**
- FastMCP's `mcp.run(transport="streamable-http", port=3001)` starts a Starlette/Uvicorn HTTP server
- The server exposes MCP protocol over HTTP with Server-Sent Events (SSE) for streaming responses
- All MCP tools, resources, and prompts are available via HTTP POST requests

---

## Running the Server

### Option 1: stdio Mode (Claude Desktop, Claude Code)

**Default mode** — used by Claude Desktop and local MCP clients:

```bash
python -m mcp_server.server
```

Output:
```
Starting WealthPoint Analysis MCP Server in stdio mode...
[WealthPoint MCP] Registered: 11 tools, 7 resources, 4 prompts
```

### Option 2: Streamable HTTP Mode (React Frontend)

**HTTP mode** — used by React frontend and remote clients:

```bash
python -m mcp_server.server --transport streamable-http --port 3001
```

Output:
```
Starting WealthPoint Analysis MCP Server in Streamable HTTP mode on port 3001...
[WealthPoint MCP] Registered: 11 tools, 7 resources, 4 prompts
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:3001 (Press CTRL+C to quit)
```

**Custom port:**

```bash
python -m mcp_server.server --transport streamable-http --port 8080
```

### Running in Production

**Background with nohup:**

```bash
nohup python -m mcp_server.server --transport streamable-http --port 3001 > mcp_server.log 2>&1 &
```

**With systemd (Linux):**

```ini
# /etc/systemd/system/wealthpoint-mcp.service
[Unit]
Description=WealthPoint MCP Server
After=network.target

[Service]
Type=simple
User=wealthpoint
WorkingDirectory=/opt/wealthpoint-platform
Environment="ANTHROPIC_API_KEY=sk-ant-..."
ExecStart=/opt/wealthpoint-platform/.venv/bin/python -m mcp_server.server --transport streamable-http --port 3001
Restart=always

[Install]
WantedBy=multi-user.target
```

**With Docker:**

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 3001

CMD ["python", "-m", "mcp_server.server", "--transport", "streamable-http", "--port", "3001"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  mcp-server:
    build: .
    ports:
      - "3001:3001"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_URL=sqlite:///./wealthpoint.db
    volumes:
      - ./wealthpoint.db:/app/wealthpoint.db
    restart: unless-stopped
```

---

## React Frontend Integration

### MCP Client Setup

The React frontend connects to the MCP server using the `@modelcontextprotocol/sdk` package:

```bash
# In your React project
npm install @modelcontextprotocol/sdk
```

### Client Implementation

```typescript
// services/mcp-client.ts

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamable-http.js";

class MCPClient {
  private client: Client;
  private transport: StreamableHTTPClientTransport;

  constructor(serverUrl: string = "http://localhost:3001") {
    this.transport = new StreamableHTTPClientTransport(serverUrl);
    this.client = new Client(
      {
        name: "wealthpoint-react-client",
        version: "1.0.0",
      },
      {
        capabilities: {},
      }
    );
  }

  async connect(): Promise<void> {
    await this.client.connect(this.transport);
    console.log("✅ Connected to WealthPoint MCP Server");
  }

  async disconnect(): Promise<void> {
    await this.client.close();
  }

  /**
   * Call an MCP tool
   */
  async callTool(name: string, args: Record<string, unknown>): Promise<any> {
    const result = await this.client.callTool({
      name,
      arguments: args,
    });
    return JSON.parse(result.content[0].text);
  }

  /**
   * Read an MCP resource
   */
  async readResource(uri: string): Promise<any> {
    const result = await this.client.readResource({ uri });
    return JSON.parse(result.contents[0].text);
  }

  /**
   * List available tools
   */
  async listTools(): Promise<any[]> {
    const result = await this.client.listTools();
    return result.tools;
  }

  /**
   * List available resources
   */
  async listResources(): Promise<any[]> {
    const result = await this.client.listResources();
    return result.resources;
  }
}

export const mcpClient = new MCPClient();
```

### React Hook

```typescript
// hooks/useChat.ts

import { useState, useEffect } from "react";
import { mcpClient } from "../services/mcp-client";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  display_type?: string;
  charts?: any[];
  tables?: any[];
  kpis?: any[];
}

export function useChat() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  // Connect to MCP server on mount
  useEffect(() => {
    mcpClient.connect().then(() => setIsConnected(true));
    return () => {
      mcpClient.disconnect();
    };
  }, []);

  /**
   * Upload a portfolio PDF
   */
  const uploadPDF = async (file: File) => {
    // Convert file to base64
    const base64 = await fileToBase64(file);

    // Call upload_portfolio tool
    const result = await mcpClient.callTool("upload_portfolio", {
      pdf_base64: base64,
      filename: file.name,
      client_id: "default",
    });

    // Store session_id for subsequent calls
    setSessionId(result.session_id);

    // Add assistant message
    addMessage({
      role: "assistant",
      content: result.message || `Portfolio loaded: ${file.name}`,
      display_type: result.display_type,
      kpis: result.kpis,
    });

    return result;
  };

  /**
   * Send a question about the portfolio
   */
  const sendMessage = async (question: string) => {
    if (!sessionId) {
      throw new Error("No portfolio loaded. Please upload a PDF first.");
    }

    // Add user message
    addMessage({ role: "user", content: question });

    // Call ask_portfolio tool
    const result = await mcpClient.callTool("ask_portfolio", {
      session_id: sessionId,
      question,
    });

    // Add assistant message
    addMessage({
      role: "assistant",
      content: result.content,
      display_type: result.display_type,
      charts: result.charts,
      tables: result.tables,
      kpis: result.kpis,
    });

    return result;
  };

  const addMessage = (message: ChatMessage) => {
    setMessages((prev) => [...prev, message]);
  };

  return {
    messages,
    sessionId,
    isConnected,
    uploadPDF,
    sendMessage,
  };
}

// Helper function
async function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const base64 = (reader.result as string).split(",")[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}
```

### Chat Component

```typescript
// components/Chat/ChatContainer.tsx

import { useChat } from "../../hooks/useChat";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";

export function ChatContainer() {
  const { messages, sessionId, isConnected, uploadPDF, sendMessage } = useChat();

  if (!isConnected) {
    return <div>Connecting to WealthPoint MCP Server...</div>;
  }

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <ChatMessage key={idx} message={msg} />
        ))}
      </div>

      <ChatInput
        sessionId={sessionId}
        onUploadPDF={uploadPDF}
        onSendMessage={sendMessage}
      />
    </div>
  );
}
```

---

## Testing the Connection

### 1. Start the Server

```bash
# Terminal 1
python -m mcp_server.server --transport streamable-http --port 3001
```

### 2. Test with curl

**List available tools:**

```bash
curl -X POST http://localhost:3001/mcp/v1/tools/list \
  -H "Content-Type: application/json" \
  -d '{}'
```

Expected response:
```json
{
  "tools": [
    {
      "name": "upload_portfolio",
      "description": "Parse a portfolio valuation PDF...",
      "inputSchema": { ... }
    },
    {
      "name": "ask_portfolio",
      "description": "Ask any question about a portfolio...",
      "inputSchema": { ... }
    },
    ...
  ]
}
```

**Call a tool:**

```bash
curl -X POST http://localhost:3001/mcp/v1/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_market_data",
    "arguments": {
      "session_id": "test-session-123"
    }
  }'
```

### 3. Test with MCP Inspector

```bash
# Install MCP CLI tools
npm install -g @modelcontextprotocol/inspector

# Start inspector (opens browser UI)
mcp-inspector http://localhost:3001
```

The inspector provides a web UI to:
- List all tools, resources, and prompts
- Test tool calls interactively
- View resource contents
- Monitor server logs

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'mcp'`

**Cause**: MCP SDK not installed or Python version < 3.10

**Solution**:
```bash
# Check Python version
python --version  # Must be 3.10+

# Install MCP
pip install mcp>=1.0.0
```

### Issue: `ERROR: Could not find a version that satisfies the requirement mcp`

**Cause**: Python version too old (< 3.10)

**Solution**:
```bash
# Install Python 3.10+
pyenv install 3.10.13
pyenv local 3.10.13

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Port 3001 already in use

**Cause**: Another process is using port 3001

**Solution**:
```bash
# Find and kill the process
lsof -ti :3001 | xargs kill -9

# Or use a different port
python -m mcp_server.server --transport streamable-http --port 8080
```

### Issue: CORS errors in React frontend

**Cause**: Browser blocking cross-origin requests

**Solution**: FastMCP handles CORS automatically. If issues persist, check:
1. Server is running on the expected port
2. React app is using the correct server URL
3. No proxy/firewall blocking the connection

### Issue: Connection refused from React app

**Checklist**:
- [ ] Server is running: `lsof -i :3001`
- [ ] Correct URL: `http://localhost:3001` (not `http://127.0.0.1:3001`)
- [ ] No firewall blocking localhost connections
- [ ] Server logs show no startup errors

---

## Environment Variables

Create `.env` file with:

```env
# LLM
ANTHROPIC_API_KEY=sk-ant-...
OLLAMA_MODEL=llama3.1
OLLAMA_URL=http://localhost:11434

# Database
DATABASE_URL=sqlite:///./wealthpoint.db

# MCP Transport
MCP_TRANSPORT=streamable-http  # or "stdio"
MCP_HTTP_PORT=3001

# Server
LOG_LEVEL=INFO
```

Load with:
```bash
python-dotenv run python -m mcp_server.server --transport streamable-http
```

---

## Security Considerations

### Production Deployment

For production use with remote clients:

1. **Use HTTPS** (not HTTP):
   ```bash
   # Use a reverse proxy like nginx or Caddy
   # Or configure FastMCP with SSL certificates
   ```

2. **Add authentication**:
   - API key validation in MCP tools
   - JWT tokens for session management
   - Rate limiting per client

3. **Restrict origins**:
   - Configure CORS to only allow your frontend domain
   - Block unauthorized origins

4. **Network isolation**:
   - Run on internal network only
   - Use VPN for remote access
   - Firewall rules limiting access

### Example: Add API Key Auth

```python
# mcp_server/auth.py
from functools import wraps
from app.config import settings

def require_api_key(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Check API key in request context
        # (FastMCP provides request context)
        api_key = kwargs.get("_api_key")
        if api_key != settings.api_key:
            raise ValueError("Invalid API key")
        return await func(*args, **kwargs)
    return wrapper

# Apply to tools
@mcp.tool()
@require_api_key
async def upload_portfolio(...):
    ...
```

---

## Next Steps

### Phase 3.4 Checklist

- [x] Document Python 3.10+ requirement
- [x] Document server startup commands
- [x] Document React frontend integration
- [x] Document testing procedures
- [ ] **Upgrade Python to 3.10+ and test server startup**
- [ ] **Verify HTTP transport works correctly**
- [ ] **Test with React frontend**
- [ ] **Deploy to staging environment**

### Phase 4 & 5 (After HTTP transport verified)

- Phase 4: Implement remaining agents (compliance, dividend, margin, full report)
- Phase 5: Build React Chat Frontend with HTTP client

---

## References

- [MCP Python SDK Documentation](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP Reference](https://github.com/modelcontextprotocol/python-sdk/tree/main/src/mcp/server/fastmcp)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Streamable HTTP Transport](https://spec.modelcontextprotocol.io/specification/architecture/#transports)
