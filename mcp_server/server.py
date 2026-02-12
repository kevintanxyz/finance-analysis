"""
WealthPoint Analysis MCP Server - Main entry point.

Launch modes:
- stdio (default): For Claude Desktop, Claude Code, local clients
  python -m mcp_server.server

- Streamable HTTP: For React frontend, remote clients
  python -m mcp_server.server --transport streamable-http --port 3001

- Dev mode with inspector:
  mcp dev mcp_server/server.py
"""
import sys
from mcp_server import mcp


def _verify_registrations():
    """Verify all tools, resources, and prompts are registered."""
    tools_count = len(mcp._tool_manager._tools)
    resources_count = len(mcp._resource_manager._resources)
    prompts_count = len(mcp._prompt_manager._prompts)

    print(f"[WealthPoint MCP] Registered: {tools_count} tools, {resources_count} resources, {prompts_count} prompts", file=sys.stderr)

    if tools_count == 0:
        print("[WealthPoint MCP] WARNING: No tools registered!", file=sys.stderr)


if __name__ == "__main__":
    # Import and register all tools, resources, and prompts
    # IMPORTANT: Import INSIDE __main__ to avoid double import issues
    # The decorators (@mcp.tool, @mcp.resource, @mcp.prompt) auto-register them
    print(f"[SERVER DEBUG] mcp object id: {id(mcp)}", file=sys.stderr)
    print("[DEBUG] Starting imports...", file=sys.stderr)
    try:
        from mcp_server import tools  # noqa: F401, E402
        print("[DEBUG] Tools imported", file=sys.stderr)
    except Exception as e:
        print(f"[ERROR] Failed to import tools: {e}", file=sys.stderr)

    try:
        from mcp_server import resources  # noqa: F401, E402
        print("[DEBUG] Resources imported", file=sys.stderr)
    except Exception as e:
        print(f"[ERROR] Failed to import resources: {e}", file=sys.stderr)

    try:
        from mcp_server import prompts  # noqa: F401, E402
        print("[DEBUG] Prompts imported", file=sys.stderr)
    except Exception as e:
        print(f"[ERROR] Failed to import prompts: {e}", file=sys.stderr)

    # Verify registrations after imports
    _verify_registrations()

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
