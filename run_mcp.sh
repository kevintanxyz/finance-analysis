#!/bin/bash
# Wrapper script to load .env and start WealthPoint MCP server

DIR="/Users/kevintan/Documents/Projects/wealthpoint-projects/finance-analysis"
cd "$DIR"

# Load .env file if it exists
if [ -f "$DIR/.env" ]; then
    set -a  # automatically export all variables
    source "$DIR/.env"
    set +a
fi

# Run the MCP server with uv
exec uv run python -m mcp_server.server "$@"
