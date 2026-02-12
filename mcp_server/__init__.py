"""
WealthPoint Analysis MCP Server - Portfolio Intelligence Platform for Family Offices.

This module exposes all portfolio analysis capabilities via the Model Context Protocol (MCP).
Any MCP-compatible client (Claude Desktop, Claude Code, React app, etc.) can connect.

Architecture:
- Tools: Actions the LLM can perform (upload_portfolio, ask_portfolio, analyze_risk, etc.)
- Resources: Data the LLM can read (portfolio://{id}, positions://{id}, etc.)
- Prompts: Pre-defined conversation templates (portfolio-summary, risk-report, etc.)

The MCP server is the ONLY surface of exposure - there's no FastAPI or REST API.
All logic is in app/ modules (parsers, analysis, services, llm).
"""
from mcp.server.fastmcp import FastMCP

__version__ = "1.0.0"

# Create the FastMCP instance here to avoid circular imports
# All modules (tools, resources, prompts, server) will import from here
mcp = FastMCP("wealthpoint-analysis")
