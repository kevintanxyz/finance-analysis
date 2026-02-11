"""
Test Risk Calculator

Quick test to verify the risk calculator works correctly.
"""
import asyncio
from app.analysis.risk_calculator import RiskCalculator
from app.models.analysis import RiskCalculationConfig


async def test_risk_calculator():
    """Test risk calculator with real yfinance data."""
    print("🧪 Testing Risk Calculator...")
    print("=" * 70)

    # Create calculator with standard config
    config = RiskCalculationConfig(
        confidence_level=0.95,
        var_method="historical",
        rolling_window=90,
        risk_free_rate=0.045,
    )

    calculator = RiskCalculator(config)

    # Test with Apple (AAPL) - should work
    ticker = "AAPL"
    days = 90

    print(f"\n📥 Fetching {days} days of data for {ticker}...")

    try:
        # Fetch price data
        price_data = await calculator.fetch_price_data_from_yfinance(ticker, days)
        print(f"✅ Fetched {len(price_data.prices)} data points")
        print(f"📅 Latest data: {price_data.dates[-1]}")

        # Fetch benchmark
        print(f"\n📥 Fetching benchmark data for SPY...")
        benchmark_data = await calculator.fetch_price_data_from_yfinance("SPY", days)
        print(f"✅ Fetched {len(benchmark_data.prices)} benchmark points")

        # Calculate risk metrics
        print(f"\n🧮 Calculating risk metrics...")
        results = await calculator.calculate_risk_metrics(price_data, benchmark_data)

        # Display results
        print("\n" + "=" * 70)
        print(f"📊 RISK ANALYSIS: {results.ticker}")
        print(f"📅 Data Through: {results.calculation_date}")
        print("=" * 70)

        print("\n📉 VALUE AT RISK")
        print(f"  95% VaR (Daily):          {results.var_95:>10.2%}")
        print(f"  95% CVaR (Daily):         {results.cvar_95:>10.2%}")

        print("\n📈 RISK-ADJUSTED RETURNS")
        print(f"  Sharpe Ratio:             {results.sharpe_ratio:>10.2f}")
        print(f"  Sortino Ratio:            {results.sortino_ratio:>10.2f}")

        print("\n📊 DRAWDOWN ANALYSIS")
        print(f"  Maximum Drawdown:         {results.max_drawdown:>10.2%}")
        print(f"  Calmar Ratio:             {results.calmar_ratio:>10.2f}")

        print("\n🎢 VOLATILITY")
        print(f"  Annual Volatility:        {results.annual_volatility:>10.2%}")

        if results.beta is not None and results.alpha is not None:
            print("\n🎯 MARKET RELATIONSHIP")
            print(f"  Beta (vs SPY):            {results.beta:>10.2f}")
            print(f"  Alpha (vs SPY):           {results.alpha:>10.2%}")

        print("\n" + "=" * 70)
        print("✅ Test successful!")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(test_risk_calculator())
    exit(0 if success else 1)
