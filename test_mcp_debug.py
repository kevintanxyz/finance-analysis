#!/usr/bin/env python3
"""Debug script to test MCP registrations."""

import sys

# Import server module
from mcp_server.server import mcp

print(f"[TEST] Server mcp object id: {id(mcp)}")
print(f"[TEST] Before imports - Tools: {len(mcp._tool_manager._tools)}, Resources: {len(mcp._resource_manager._resources)}, Prompts: {len(mcp._prompt_manager._prompts)}")

# Import tools, resources, prompts
from mcp_server import tools, resources, prompts

print(f"[TEST] After imports - Tools: {len(mcp._tool_manager._tools)}, Resources: {len(mcp._resource_manager._resources)}, Prompts: {len(mcp._prompt_manager._prompts)}")
