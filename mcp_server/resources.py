"""
MCP Resources - Data the LLM can read.

Resources expose portfolio data in a structured format. The client LLM
can load these into its context to understand the portfolio before making
tool calls or answering questions.

Phase 1 resources:
- portfolio://{session_id} - Complete portfolio data
- portfolio://{session_id}/positions - All positions
- portfolio://{session_id}/listed - Listed positions only
- portfolio://{session_id}/allocation - Asset allocation
- portfolio://{session_id}/exposure - Currency/regional/sector exposure
- portfolio://{session_id}/pnl - P&L overview and detail
- clients://list - List of all clients

Phase 3 additions:
- More granular resources as needed
"""
import json
from mcp_server import mcp
from app.database import get_session, Client, Portfolio


# ────────────────────────────────────────────────────────────────────────────
# Phase 1 Resources
# ────────────────────────────────────────────────────────────────────────────


@mcp.resource("portfolio://{session_id}")
async def get_portfolio(session_id: str) -> str:
    """
    Complete structured portfolio data as JSON.

    Args:
        session_id: Portfolio session ID

    Returns:
        JSON string with complete portfolio data
    """
    with get_session() as session:
        portfolio = session.get(Portfolio, session_id)
        if not portfolio:
            return json.dumps({"error": "Portfolio not found"})

        return portfolio.data_json


@mcp.resource("portfolio://{session_id}/positions")
async def get_positions(session_id: str) -> str:
    """
    All positions with ISIN, value, weight, P&L.

    Args:
        session_id: Portfolio session ID

    Returns:
        JSON array of positions
    """
    with get_session() as session:
        portfolio = session.get(Portfolio, session_id)
        if not portfolio:
            return json.dumps({"error": "Portfolio not found"})

        data = json.loads(portfolio.data_json)
        positions = data.get("positions", [])

        return json.dumps(positions, indent=2)


@mcp.resource("portfolio://{session_id}/listed")
async def get_listed(session_id: str) -> str:
    """
    Listed positions with tickers (compatible with Finance-Guru analysis tools).

    Args:
        session_id: Portfolio session ID

    Returns:
        JSON array of listed positions with ticker symbols
    """
    with get_session() as session:
        portfolio = session.get(Portfolio, session_id)
        if not portfolio:
            return json.dumps({"error": "Portfolio not found"})

        data = json.loads(portfolio.data_json)
        positions = data.get("positions", [])

        # Filter for listed positions only
        listed = [p for p in positions if p.get("is_listed", False)]

        return json.dumps(listed, indent=2)


@mcp.resource("portfolio://{session_id}/allocation")
async def get_allocation(session_id: str) -> str:
    """
    Asset allocation breakdown.

    Args:
        session_id: Portfolio session ID

    Returns:
        JSON object with asset allocation data
    """
    with get_session() as session:
        portfolio = session.get(Portfolio, session_id)
        if not portfolio:
            return json.dumps({"error": "Portfolio not found"})

        data = json.loads(portfolio.data_json)
        allocation = data.get("asset_allocation", [])

        return json.dumps(allocation, indent=2)


@mcp.resource("portfolio://{session_id}/exposure")
async def get_exposure(session_id: str) -> str:
    """
    Currency, regional, and sector exposure.

    Args:
        session_id: Portfolio session ID

    Returns:
        JSON object with exposure data
    """
    with get_session() as session:
        portfolio = session.get(Portfolio, session_id)
        if not portfolio:
            return json.dumps({"error": "Portfolio not found"})

        data = json.loads(portfolio.data_json)

        exposure = {
            "currency": data.get("currency_exposure", []),
            "regional": data.get("regional_exposure", []),
            "sector": data.get("sector_exposure", []),
        }

        return json.dumps(exposure, indent=2)


@mcp.resource("portfolio://{session_id}/pnl")
async def get_pnl(session_id: str) -> str:
    """
    P&L overview and detailed breakdown.

    Args:
        session_id: Portfolio session ID

    Returns:
        JSON object with P&L data
    """
    with get_session() as session:
        portfolio = session.get(Portfolio, session_id)
        if not portfolio:
            return json.dumps({"error": "Portfolio not found"})

        data = json.loads(portfolio.data_json)

        pnl = {
            "overview": data.get("pnl_overview", {}),
            "detail": data.get("pnl_detail", {}),
            "tops": data.get("tops", []),
            "flops": data.get("flops", []),
        }

        return json.dumps(pnl, indent=2)


@mcp.resource("clients://list")
async def list_clients() -> str:
    """
    List all clients and their portfolios.

    Returns:
        JSON array of clients with portfolio counts
    """
    with get_session() as session:
        clients = session.query(Client).all()

        result = []
        for client in clients:
            portfolio_count = (
                session.query(Portfolio)
                .filter(Portfolio.client_id == client.id)
                .count()
            )

            result.append(
                {
                    "id": client.id,
                    "name": client.name,
                    "email": client.email,
                    "risk_profile": client.risk_profile,
                    "portfolio_count": portfolio_count,
                }
            )

        return json.dumps(result, indent=2)
