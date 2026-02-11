"""
NUMAN MCP Server - Main entry point.

Launch modes:
- stdio (default): For Claude Desktop, Claude Code, local clients
  python -m mcp_server.server

- Streamable HTTP: For React frontend, remote clients
  python -m mcp_server.server --transport streamable-http --port 3001

- Dev mode with inspector:
  mcp dev mcp_server/server.py
"""
import sys
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP(
    "numan-portfolio",
    # Note: version moved to pyproject.toml
)

# Import and register all tools, resources, and prompts
# The decorators (@mcp.tool, @mcp.resource, @mcp.prompt) auto-register them
from mcp_server import tools  # noqa: F401, E402
from mcp_server import resources  # noqa: F401, E402
from mcp_server import prompts  # noqa: F401, E402


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
        print(f"Starting NUMAN MCP Server in Streamable HTTP mode on port {port}...")
        mcp.run(transport="streamable-http", port=port)
    else:
        # stdio mode (for Claude Desktop, Claude Code)
        print("Starting NUMAN MCP Server in stdio mode...", file=sys.stderr)
        mcp.run()
