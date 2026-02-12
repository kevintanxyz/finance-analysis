"""
Live test for get_market_data MCP tool.

This script creates a test portfolio with listed positions and validates
that the market data tool fetches and formats real-time data correctly.
"""
import asyncio
import json
from datetime import datetime

from app.database import get_session, Client, Portfolio
from app.models.portfolio import (
    PortfolioData, Position, AssetClass, PositionType,
    MandateDetails, PortfolioDetails, AllocationItem, PnLOverview
)


async def create_test_portfolio() -> str:
    """Create a test portfolio with listed positions."""
    session = get_session()

    # Create or get test client
    client = session.get(Client, "test-market-data")
    if not client:
        client = Client(
            id="test-market-data",
            name="Market Data Test Client",
            risk_profile="moderate",
            notes="Auto-created for testing get_market_data tool",
        )
        session.add(client)
        session.commit()

    # Create test portfolio data with listed positions
    portfolio_data = PortfolioData(
        valuation_date=datetime.now().strftime("%Y-%m-%d"),
        mandate=MandateDetails(
            mandate="Test Market Data",
            custody_bank="Test Bank",
            portfolio_number="TEST-001",
        ),
        portfolio_details=PortfolioDetails(
            currency="CHF",
            profile="Test",
        ),
        total_value_chf=100000.00,
        asset_allocation=[
            AllocationItem(
                asset_class="Equities",
                value_chf=100000.00,
                weight_pct=100.0,
            ),
        ],
        pnl_overview=PnLOverview(
            total_pnl=0.0,
            total_pnl_pct=0.0,
        ),
        positions=[
            Position(
                asset_class=AssetClass.EQUITIES,
                position_type=PositionType.EQUITY,
                currency="USD",
                isin="US0378331005",
                name="Apple Inc.",
                cost_price=150.00,
                quote=175.00,
                value_chf=35000.00,
                weight_pct=35.0,
                ticker="AAPL",
                is_listed=True,
            ),
            Position(
                asset_class=AssetClass.EQUITIES,
                position_type=PositionType.EQUITY,
                currency="USD",
                isin="US0231351067",
                name="Amazon.com Inc.",
                cost_price=3200.00,
                quote=3500.00,
                value_chf=35000.00,
                weight_pct=35.0,
                ticker="AMZN",
                is_listed=True,
            ),
            Position(
                asset_class=AssetClass.EQUITIES,
                position_type=PositionType.ETF,
                currency="USD",
                isin="US78462F1030",
                name="SPDR S&P 500 ETF Trust",
                cost_price=450.00,
                quote=475.00,
                value_chf=30000.00,
                weight_pct=30.0,
                ticker="SPY",
                is_listed=True,
            ),
        ],
        currency_exposure=[],
        regional_exposure=[],
        sector_exposure=[],
        pnl_detail=None,
        tops=[],
        flops=[],
        performance=[],
        transactions=[],
        risk_analysis=None,
    )

    # Save to database
    portfolio = Portfolio(
        id=f"test-market-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        client_id=client.id,
        valuation_date=portfolio_data.valuation_date,
        total_value_chf=portfolio_data.total_value_chf,
        data_json=portfolio_data.model_dump_json(),
        pdf_filename="test_market_data.pdf",
    )
    session.add(portfolio)
    session.commit()

    print(f"✅ Created test portfolio: {portfolio.id}")
    print(f"   Positions: AAPL, AMZN, SPY")
    print(f"   Total value: CHF {portfolio_data.total_value_chf:,.2f}")

    return portfolio.id


async def test_get_market_data(session_id: str):
    """Test the get_market_data tool."""
    from mcp_server.tools import get_market_data

    print(f"\n📊 Fetching market data for session {session_id}...")

    result = await get_market_data(session_id)

    print(f"\n{'='*80}")
    print("MARKET DATA RESULT")
    print('='*80)

    # Print content
    print(f"\n{result['content']}\n")

    # Print KPIs
    if result.get('kpis'):
        print("\n📈 KPI CARDS:")
        for kpi in result['kpis']:
            change = f" ({kpi['change']})" if kpi.get('change') else ""
            print(f"   {kpi['label']}: {kpi['value']}{change}")

    # Print table data
    if result.get('tables'):
        print("\n📋 MARKET DATA TABLE:")
        table = result['tables'][0]
        rows = table['rows']

        # Print header
        print("\n   Ticker | Name          | Price   | 1D %   | 5D %   | 1M %   | Value CHF | Weight % | P/E   | Beta")
        print("   " + "-" * 105)

        # Print rows
        for row in rows:
            ticker = row.get('ticker', 'N/A')[:6].ljust(6)
            name = row.get('name', 'N/A')[:13].ljust(13)
            price = f"{row.get('current_price', 0):>7.2f}" if row.get('current_price') else "    N/A"
            chg1d = f"{row.get('change_1d_pct', 0):>6.2f}" if row.get('change_1d_pct') is not None else "   N/A"
            chg5d = f"{row.get('change_5d_pct', 0):>6.2f}" if row.get('change_5d_pct') is not None else "   N/A"
            chg1m = f"{row.get('change_1m_pct', 0):>6.2f}" if row.get('change_1m_pct') is not None else "   N/A"
            value = f"{row.get('value_chf', 0):>9,.2f}"
            weight = f"{row.get('weight_pct', 0):>8.2f}"
            pe = f"{row.get('pe_ratio', 0):>5.1f}" if row.get('pe_ratio') else "  N/A"
            beta = f"{row.get('beta', 0):>4.2f}" if row.get('beta') else " N/A"

            print(f"   {ticker} | {name} | {price} | {chg1d} | {chg5d} | {chg1m} | {value} | {weight} | {pe} | {beta}")

            # Show error if any
            if row.get('error'):
                print(f"          ⚠️  Error: {row['error']}")

    print(f"\n{'='*80}\n")

    # Print raw JSON for debugging
    print("\n🔍 RAW JSON OUTPUT:")
    print(json.dumps(result, indent=2, default=str))


async def main():
    """Main test function."""
    print("="*80)
    print("LIVE TEST: get_market_data MCP Tool")
    print("="*80)
    print("\nThis test creates a portfolio with listed positions (AAPL, AMZN, SPY)")
    print("and validates that get_market_data fetches real-time market data.\n")

    # Create test portfolio
    session_id = await create_test_portfolio()

    # Test get_market_data
    await test_get_market_data(session_id)

    print("\n✅ Test complete!")
    print("\nNote: This test uses live market data from yfinance.")
    print("Results will vary based on current market conditions and trading hours.")


if __name__ == "__main__":
    asyncio.run(main())
