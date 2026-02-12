"""
Unit tests for Phase 4 Agent Tools.

Tests all 7 agent tools:
1. check_compliance
2. analyze_dividends
3. analyze_margin
4. generate_full_report
5. analyze_portfolio_profile
6. analyze_security
7. recommend_rebalancing
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import tools to test
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp_server.tools import (
    check_compliance,
    analyze_dividends,
    analyze_margin,
    generate_full_report,
    analyze_portfolio_profile,
    analyze_security,
    recommend_rebalancing
)
from app.models.portfolio import PortfolioData, Position


# ────────────────────────────────────────────────────────────────────────────
# Test Fixtures
# ────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_portfolio_data():
    """Create a realistic portfolio for testing."""
    from app.models.portfolio import AssetClass, PositionType

    return PortfolioData(
        portfolio_id="test-portfolio-001",
        valuation_date="2024-02-12",
        total_value_chf=298758.42,
        currency="CHF",
        positions=[
            # Equity positions
            Position(
                name="Apple Inc.",
                ticker="AAPL",
                isin="US0378331005",
                asset_class=AssetClass.EQUITIES,
                position_type=PositionType.EQUITY,
                quantity=300,
                quote=185.50,  # Use quote instead of price_chf
                value_chf=55650.00,
                weight_pct=18.63,
                currency="USD",
                fx_rate=0.88,
                is_listed=True
            ),
            Position(
                name="Microsoft Corp",
                ticker="MSFT",
                isin="US5949181045",
                asset_class=AssetClass.EQUITIES,
                position_type=PositionType.EQUITY,
                quantity=200,
                quote=380.00,
                value_chf=76000.00,
                weight_pct=25.43,
                currency="USD",
                fx_rate=0.88,
                is_listed=True
            ),
            Position(
                name="Roche Holding AG",
                ticker="ROG.SW",
                isin="CH0012032048",
                asset_class=AssetClass.EQUITIES,
                position_type=PositionType.EQUITY,
                quantity=100,
                quote=358.00,
                value_chf=35800.00,
                weight_pct=11.98,
                currency="CHF",
                fx_rate=1.0,
                is_listed=True
            ),
            # Bond position
            Position(
                name="Swiss Govt Bond 1.5% 2030",
                ticker=None,
                isin="CH0224397213",
                asset_class=AssetClass.BONDS,
                position_type=PositionType.BOND_FX,
                quantity=50000,
                quote=98.50,
                value_chf=49250.00,
                weight_pct=16.48,
                currency="CHF",
                fx_rate=1.0,
                is_listed=False
            ),
            # ETF position
            Position(
                name="SPDR S&P 500 ETF",
                ticker="SPY",
                isin="US78462F1030",
                asset_class=AssetClass.EQUITIES,
                position_type=PositionType.ETF,
                quantity=150,
                quote=450.00,
                value_chf=67500.00,
                weight_pct=22.59,
                currency="USD",
                fx_rate=0.88,
                is_listed=True
            ),
            # Cash position
            Position(
                name="Cash CHF",
                ticker=None,
                isin=None,
                asset_class=AssetClass.CASH,
                position_type=PositionType.CASH_ACCOUNT,
                quantity=1,
                quote=14558.42,
                value_chf=14558.42,
                weight_pct=4.87,
                currency="CHF",
                fx_rate=1.0,
                is_listed=False
            )
        ],
        currency_exposure=[
            {"name": "CHF", "value_chf": 99608.42, "weight_pct": 33.35},
            {"name": "USD", "value_chf": 199150.00, "weight_pct": 66.65}
        ],
        asset_class_allocation=[
            {"name": "Equities", "value_chf": 234950.00, "weight_pct": 78.63},
            {"name": "Bonds", "value_chf": 49250.00, "weight_pct": 16.48},
            {"name": "Cash", "value_chf": 14558.42, "weight_pct": 4.87}
        ]
    )


@pytest.fixture
def mock_db_session(sample_portfolio_data):
    """Mock database session with portfolio."""
    from contextlib import contextmanager

    mock_session = MagicMock()
    mock_portfolio = Mock()
    mock_portfolio.data_json = sample_portfolio_data.model_dump_json()
    mock_session.get.return_value = mock_portfolio

    @contextmanager
    def mock_get_session():
        yield mock_session

    return mock_get_session


# ────────────────────────────────────────────────────────────────────────────
# Test 1: check_compliance
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_check_compliance_default_limits(mock_db_session):
    """Test compliance check with default limits."""
    with patch('mcp_server.tools.get_session', return_value=mock_db_session):
        result = await check_compliance("test-session-id")

    assert result["success"] == True
    assert "compliance" in result
    assert "is_compliant" in result["compliance"]
    assert "violations" in result["compliance"]
    assert "summary" in result["compliance"]


@pytest.mark.asyncio
async def test_check_compliance_custom_limits(mock_db_session):
    """Test compliance check with custom strict limits."""
    with patch('mcp_server.tools.get_session', return_value=mock_db_session):
        result = await check_compliance(
            "test-session-id",
            max_position_pct=15.0,  # Stricter than default 20%
            min_positions=8  # More than we have
        )

    assert result["success"] == True
    # Should have violations since MSFT is 25.43%
    violations = result["compliance"]["violations"]
    assert len(violations) > 0


@pytest.mark.asyncio
async def test_check_compliance_portfolio_not_found():
    """Test compliance check when portfolio doesn't exist."""
    mock_session = MagicMock()
    mock_session.get.return_value = None

    with patch('mcp_server.tools.get_session', return_value=mock_session):
        result = await check_compliance("nonexistent-session")

    assert result["success"] == False
    assert "not found" in result["error"]


# ────────────────────────────────────────────────────────────────────────────
# Test 2: analyze_dividends
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analyze_dividends_with_yfinance_data(mock_db_session):
    """Test dividend analysis with mocked yfinance data."""
    mock_yf_info = {
        "trailingAnnualDividendRate": 9.80,
        "exDividendDate": 1707696000  # Feb 12, 2024
    }

    with patch('mcp_server.tools.get_session', return_value=mock_db_session), \
         patch('yfinance.Ticker') as mock_ticker:

        # Mock yfinance Ticker
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = mock_yf_info
        mock_ticker.return_value = mock_ticker_instance

        result = await analyze_dividends("test-session-id")

    assert result["success"] == True
    assert "dividends" in result
    assert "portfolio_yield_pct" in result["dividends"]
    assert "total_annual_dividends_chf" in result["dividends"]


@pytest.mark.asyncio
async def test_analyze_dividends_yield_calculation(mock_db_session):
    """Test that dividend yield is calculated correctly using share price."""
    # Mock yfinance to return dividend data
    mock_yf_info = {
        "trailingAnnualDividendRate": 9.80,  # CHF per share
        "exDividendDate": 1707696000
    }

    with patch('mcp_server.tools.get_session', return_value=mock_db_session), \
         patch('yfinance.Ticker') as mock_ticker:

        mock_ticker_instance = Mock()
        mock_ticker_instance.info = mock_yf_info
        mock_ticker.return_value = mock_ticker_instance

        result = await analyze_dividends("test-session-id")

    # For Roche: 9.80 / 358 = 2.74%
    # Check that yields are reasonable (not 272%!)
    if result["success"]:
        positions = result["dividends"]["positions"]
        for pos in positions:
            if pos["dividend_yield_pct"] > 0:
                assert pos["dividend_yield_pct"] < 20, \
                    f"Dividend yield {pos['dividend_yield_pct']}% is suspiciously high for {pos['ticker']}"


# ────────────────────────────────────────────────────────────────────────────
# Test 3: analyze_margin
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analyze_margin_no_leverage(mock_db_session):
    """Test margin analysis for unleveraged portfolio."""
    with patch('mcp_server.tools.get_session', return_value=mock_db_session):
        result = await analyze_margin("test-session-id")

    assert result["success"] == True
    assert "margin" in result
    assert result["margin"]["leverage_ratio"] == 1.0
    assert result["margin"]["estimated_margin_debt_chf"] == 0.0


@pytest.mark.asyncio
async def test_analyze_margin_with_custom_rate(mock_db_session):
    """Test margin analysis with custom interest rate."""
    with patch('mcp_server.tools.get_session', return_value=mock_db_session):
        result = await analyze_margin("test-session-id", margin_interest_rate=6.5)

    assert result["success"] == True
    # Should use 6.5% rate for calculations


# ────────────────────────────────────────────────────────────────────────────
# Test 4: generate_full_report
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_full_report_orchestration(mock_db_session):
    """Test that full report calls all 8 sections."""
    with patch('mcp_server.tools.get_session', return_value=mock_db_session), \
         patch('mcp_server.tools.get_portfolio_allocation') as mock_alloc, \
         patch('mcp_server.tools.check_compliance') as mock_compliance, \
         patch('mcp_server.tools.get_market_data') as mock_market, \
         patch('mcp_server.tools.analyze_dividends') as mock_div, \
         patch('mcp_server.tools.analyze_margin') as mock_margin, \
         patch('mcp_server.tools.analyze_risk') as mock_risk, \
         patch('mcp_server.tools.analyze_momentum') as mock_momentum, \
         patch('mcp_server.tools.analyze_correlation') as mock_corr:

        # Mock all sub-tools to return success
        mock_alloc.return_value = {"success": True}
        mock_compliance.return_value = {"success": True, "compliance": {"is_compliant": True}}
        mock_market.return_value = {"success": True}
        mock_div.return_value = {"success": True, "dividends": {"portfolio_yield_pct": 2.5}}
        mock_margin.return_value = {"success": True, "margin": {"leverage_ratio": 1.0}}
        mock_risk.return_value = {"success": True}
        mock_momentum.return_value = {"success": True}
        mock_corr.return_value = {"success": True, "correlation": {"diversification_score": 0.75}}

        result = await generate_full_report("test-session-id")

    assert result["success"] == True
    assert "report" in result
    assert "sections" in result["report"]

    # Verify all 8 sections are present
    sections = result["report"]["sections"]
    assert "1_allocation" in sections
    assert "2_compliance" in sections
    assert "3_market_data" in sections
    assert "4_dividends" in sections
    assert "5_margin" in sections
    assert "6_risk" in sections
    assert "7_momentum" in sections
    assert "8_correlation" in sections


@pytest.mark.asyncio
async def test_generate_full_report_passes_tickers_to_correlation(mock_db_session):
    """Test that full report correctly passes tickers to analyze_correlation."""
    with patch('mcp_server.tools.get_session', return_value=mock_db_session), \
         patch('mcp_server.tools.get_portfolio_allocation') as mock_alloc, \
         patch('mcp_server.tools.check_compliance') as mock_compliance, \
         patch('mcp_server.tools.get_market_data') as mock_market, \
         patch('mcp_server.tools.analyze_dividends') as mock_div, \
         patch('mcp_server.tools.analyze_margin') as mock_margin, \
         patch('mcp_server.tools.analyze_risk') as mock_risk, \
         patch('mcp_server.tools.analyze_momentum') as mock_momentum, \
         patch('mcp_server.tools.analyze_correlation') as mock_corr:

        mock_alloc.return_value = {"success": True}
        mock_compliance.return_value = {"success": True, "compliance": {"is_compliant": True}}
        mock_market.return_value = {"success": True}
        mock_div.return_value = {"success": True, "dividends": {"portfolio_yield_pct": 2.5}}
        mock_margin.return_value = {"success": True, "margin": {"leverage_ratio": 1.0}}
        mock_risk.return_value = {"success": True}
        mock_momentum.return_value = {"success": True}
        mock_corr.return_value = {"success": True}

        await generate_full_report("test-session-id")

    # Verify analyze_correlation was called with tickers list
    mock_corr.assert_called_once()
    call_args = mock_corr.call_args
    assert len(call_args[0]) == 2  # session_id and tickers
    tickers = call_args[0][1]
    assert isinstance(tickers, list)
    assert len(tickers) > 0  # Should have extracted tickers


# ────────────────────────────────────────────────────────────────────────────
# Test 5: analyze_portfolio_profile
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analyze_portfolio_profile_classification(mock_db_session):
    """Test investor profile classification."""
    with patch('mcp_server.tools.get_session', return_value=mock_db_session):
        result = await analyze_portfolio_profile("test-session-id")

    assert result["success"] == True
    assert "profile" in result
    assert "risk_tolerance" in result["profile"]
    assert result["profile"]["risk_tolerance"] in ["Conservative", "Moderate", "Aggressive"]
    assert "risk_score_pct" in result["profile"]
    assert 0 <= result["profile"]["risk_score_pct"] <= 100


@pytest.mark.asyncio
async def test_analyze_portfolio_profile_empty_currency_exposure(mock_db_session):
    """Test that profile handles empty currency_exposure list gracefully."""
    # Modify sample data to have empty currency_exposure
    mock_portfolio = Mock()
    sample_data = PortfolioData(
        portfolio_id="test",
        valuation_date="2024-02-12",
        total_value_chf=100000,
        currency="CHF",
        positions=[],
        currency_exposure=[],  # Empty list
        asset_class_allocation=[]
    )
    mock_portfolio.data_json = sample_data.model_dump_json()
    mock_db_session.get.return_value = mock_portfolio

    with patch('mcp_server.tools.get_session', return_value=mock_db_session):
        result = await analyze_portfolio_profile("test-session-id")

    # Should not crash with IndexError
    assert result["success"] == True


# ────────────────────────────────────────────────────────────────────────────
# Test 6: analyze_security
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analyze_security_fundamental_and_technical(mock_db_session):
    """Test full security analysis with both fundamental and technical data."""
    mock_yf_info = {
        "longName": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "currentPrice": 185.50,
        "marketCap": 2850000000000,
        "trailingPE": 29.5,
        "priceToBook": 45.8,
        "profitMargins": 0.253,
        "returnOnEquity": 1.472,
        "fiftyDayAverage": 178.25,
        "twoHundredDayAverage": 175.00
    }

    with patch('mcp_server.tools.get_session', return_value=mock_db_session), \
         patch('yfinance.Ticker') as mock_ticker:

        mock_ticker_instance = Mock()
        mock_ticker_instance.info = mock_yf_info
        mock_ticker_instance.history.return_value = Mock(empty=False)  # For RSI calculation
        mock_ticker.return_value = mock_ticker_instance

        result = await analyze_security("test-session-id", "AAPL")

    assert result["success"] == True
    assert "research" in result
    assert "profile" in result["research"]
    assert "price_data" in result["research"]


@pytest.mark.asyncio
async def test_analyze_security_yfinance_imported():
    """Test that analyze_security properly imports yfinance."""
    # This test verifies the fix for the 'yf' is not defined bug
    mock_session = MagicMock()
    mock_portfolio = Mock()
    sample_data = PortfolioData(
        portfolio_id="test",
        valuation_date="2024-02-12",
        total_value_chf=100000,
        currency="CHF",
        positions=[],
        currency_exposure=[],
        asset_class_allocation=[]
    )
    mock_portfolio.data_json = sample_data.model_dump_json()
    mock_session.get.return_value = mock_portfolio

    with patch('mcp_server.tools.get_session', return_value=mock_session), \
         patch('yfinance.Ticker') as mock_ticker:

        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {"currentPrice": 100}
        mock_ticker.return_value = mock_ticker_instance

        result = await analyze_security("test-session-id", "AAPL")

    # Should not raise NameError: name 'yf' is not defined
    mock_ticker.assert_called_once_with("AAPL")


# ────────────────────────────────────────────────────────────────────────────
# Test 7: recommend_rebalancing
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_recommend_rebalancing_custom_target(mock_db_session):
    """Test rebalancing with custom target allocation."""
    with patch('mcp_server.tools.get_session', return_value=mock_db_session):
        result = await recommend_rebalancing(
            "test-session-id",
            target_equity_pct=60.0,
            target_bond_pct=30.0,
            target_cash_pct=10.0
        )

    assert result["success"] == True
    assert "rebalancing" in result
    assert "target_allocation" in result["rebalancing"]
    assert result["rebalancing"]["target_allocation"]["equity_pct"] == 60.0


@pytest.mark.asyncio
async def test_recommend_rebalancing_auto_target(mock_db_session):
    """Test rebalancing with auto-inferred target allocation."""
    with patch('mcp_server.tools.get_session', return_value=mock_db_session):
        result = await recommend_rebalancing("test-session-id")

    assert result["success"] == True
    # Should have inferred target based on profile
    assert "target_allocation" in result["rebalancing"]


@pytest.mark.asyncio
async def test_recommend_rebalancing_threshold(mock_db_session):
    """Test rebalancing threshold triggers."""
    with patch('mcp_server.tools.get_session', return_value=mock_db_session):
        # Current: 78.63% equity, target: 60% equity = 18.63% drift
        # With 5% threshold: should trigger
        result = await recommend_rebalancing(
            "test-session-id",
            target_equity_pct=60.0,
            target_bond_pct=30.0,
            target_cash_pct=10.0,
            rebalancing_threshold_pct=5.0
        )

    assert result["success"] == True
    assert result["rebalancing"]["required"] == True


# ────────────────────────────────────────────────────────────────────────────
# Integration Tests
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_all_tools_handle_missing_portfolio():
    """Test that all tools handle missing portfolio gracefully."""
    mock_session = MagicMock()
    mock_session.get.return_value = None

    tools_to_test = [
        (check_compliance, ("test-session",)),
        (analyze_dividends, ("test-session",)),
        (analyze_margin, ("test-session",)),
        (generate_full_report, ("test-session",)),
        (analyze_portfolio_profile, ("test-session",)),
        (analyze_security, ("test-session", "AAPL")),
        (recommend_rebalancing, ("test-session",))
    ]

    with patch('mcp_server.tools.get_session', return_value=mock_session):
        for tool_func, args in tools_to_test:
            result = await tool_func(*args)
            assert result["success"] == False, f"{tool_func.__name__} should return success=False for missing portfolio"
            assert "not found" in result.get("error", "").lower(), f"{tool_func.__name__} should have 'not found' error message"


@pytest.mark.asyncio
async def test_all_tools_return_structured_output(mock_db_session):
    """Test that all tools return properly structured output."""
    with patch('mcp_server.tools.get_session', return_value=mock_db_session), \
         patch('yfinance.Ticker') as mock_ticker, \
         patch('mcp_server.tools.get_portfolio_allocation') as mock_alloc, \
         patch('mcp_server.tools.get_market_data') as mock_market, \
         patch('mcp_server.tools.analyze_risk') as mock_risk, \
         patch('mcp_server.tools.analyze_momentum') as mock_momentum, \
         patch('mcp_server.tools.analyze_correlation') as mock_corr:

        # Mock yfinance
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {"currentPrice": 100, "trailingAnnualDividendRate": 0}
        mock_ticker.return_value = mock_ticker_instance

        # Mock dependencies for generate_full_report
        mock_alloc.return_value = {"success": True}
        mock_market.return_value = {"success": True}
        mock_risk.return_value = {"success": True}
        mock_momentum.return_value = {"success": True}
        mock_corr.return_value = {"success": True}

        tools_to_test = [
            (check_compliance, ("test-session",)),
            (analyze_dividends, ("test-session",)),
            (analyze_margin, ("test-session",)),
            (generate_full_report, ("test-session",)),
            (analyze_portfolio_profile, ("test-session",)),
            (analyze_security, ("test-session", "AAPL")),
            (recommend_rebalancing, ("test-session",))
        ]

        for tool_func, args in tools_to_test:
            result = await tool_func(*args)

            # All tools should have these fields
            assert "success" in result, f"{tool_func.__name__} missing 'success' field"
            assert isinstance(result["success"], bool), f"{tool_func.__name__} 'success' should be boolean"
            assert "display_type" in result, f"{tool_func.__name__} missing 'display_type' field"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
