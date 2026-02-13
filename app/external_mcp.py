"""
External MCP Servers Manager
Manages connections to external MCP servers (Exa, Bright Data, Sequential Thinking)
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


@dataclass
class ExternalServer:
    """Configuration for an external MCP server"""
    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None
    enabled: bool = True


class ExternalMCPServers:
    """
    Manages connections to external MCP servers and provides unified tool access.

    Launches external MCP servers as subprocesses and maintains stdio connections:
    - Exa: Web search and research
    - Bright Data: News and market data
    - Sequential Thinking: Enhanced reasoning capabilities
    - EODHD: Financial market data (quotes, fundamentals, news, technical indicators)
    """

    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.servers: List[ExternalServer] = []
        self.tools_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._initialized = False
        self._exit_stack = AsyncExitStack()

    async def initialize(self):
        """Initialize all external MCP server connections"""
        if self._initialized:
            logger.info("External MCP servers already initialized")
            return

        logger.info("Initializing external MCP servers...")

        # Configure external servers
        self.servers = [
            ExternalServer(
                name="exa",
                command="npx",
                args=["-y", "exa-mcp-server"],
                env={"EXA_API_KEY": os.getenv("EXA_API_KEY", "")},
                enabled=bool(os.getenv("EXA_API_KEY"))
            ),
            ExternalServer(
                name="bright-data",
                command="npx",
                args=["-y", "@brightdata/mcp"],
                env={"API_TOKEN": os.getenv("BRIGHT_DATA_API_KEY", "")},  # Bright Data expects API_TOKEN
                enabled=bool(os.getenv("BRIGHT_DATA_API_KEY"))
            ),
            ExternalServer(
                name="sequential-thinking",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-sequential-thinking"],
                enabled=True  # No API key required
            ),
            ExternalServer(
                name="eodhd",
                command="sh",
                args=[
                    "-c",
                    f"cd {os.path.join(os.getcwd(), 'external_mcp_servers/eodhd')} && python -m entrypoints.server_stdio --apikey {os.getenv('EODHD_API_KEY', '')}"
                ],
                env={"EODHD_API_KEY": os.getenv("EODHD_API_KEY", "")},
                enabled=bool(os.getenv("EODHD_API_KEY"))
            ),
        ]

        # Launch and connect to each server
        for server in self.servers:
            if not server.enabled:
                logger.warning(f"Skipping {server.name} - API key not configured")
                continue

            try:
                await self._connect_server(server)
                logger.info(f"✅ Connected to {server.name}")
            except Exception as e:
                logger.error(f"Failed to connect to {server.name}: {e}")
                import traceback
                traceback.print_exc()

        self._initialized = True
        logger.info(f"External MCP servers initialized: {list(self.sessions.keys())}")

    async def _connect_server(self, server: ExternalServer):
        """Connect to a single external MCP server"""
        # Create server parameters
        server_params = StdioServerParameters(
            command=server.command,
            args=server.args,
            env={**os.environ, **(server.env or {})}
        )

        # Launch server and enter context manager (keep it alive)
        read_stream, write_stream = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )

        # Create and initialize session
        session = ClientSession(read_stream, write_stream)
        await self._exit_stack.enter_async_context(session)

        # Initialize the session
        await session.initialize()

        # Store session
        self.sessions[server.name] = session

        # Cache tools from this server
        tools_result = await session.list_tools()
        self.tools_cache[server.name] = [
            {
                "name": f"{server.name}_{tool.name}",  # Prefix with server name
                "description": tool.description or "",
                "input_schema": tool.inputSchema,
                "server": server.name,
                "original_name": tool.name,
            }
            for tool in tools_result.tools
        ]

        logger.info(f"Loaded {len(self.tools_cache[server.name])} tools from {server.name}")

    async def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get combined list of all tools from all connected servers"""
        if not self._initialized:
            await self.initialize()

        all_tools = []
        for server_name, tools in self.tools_cache.items():
            all_tools.extend(tools)

        return all_tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on the appropriate external server.

        Args:
            tool_name: Tool name (prefixed with server name, e.g., "exa_search")
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        # Extract server name from tool name prefix
        if "_" not in tool_name:
            raise ValueError(f"Invalid external tool name: {tool_name} (must be prefixed with server name)")

        server_name, original_tool_name = tool_name.split("_", 1)

        if server_name not in self.sessions:
            raise ValueError(f"No connection to server: {server_name}")

        session = self.sessions[server_name]

        # Call the tool on the external server
        logger.info(f"Calling {server_name}.{original_tool_name} with args: {arguments}")
        result = await session.call_tool(original_tool_name, arguments)

        return result

    async def shutdown(self):
        """Shutdown all external server connections"""
        logger.info("Shutting down external MCP servers...")

        try:
            # Close all connections managed by the exit stack
            await self._exit_stack.aclose()
            logger.info("All external MCP servers disconnected")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

        self.sessions.clear()
        self.tools_cache.clear()
        self._initialized = False


# Global instance
_external_servers: Optional[ExternalMCPServers] = None


async def get_external_servers() -> ExternalMCPServers:
    """Get or create the global external servers manager"""
    global _external_servers

    if _external_servers is None:
        _external_servers = ExternalMCPServers()
        await _external_servers.initialize()

    return _external_servers
