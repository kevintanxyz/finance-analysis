#!/usr/bin/env python3
"""
Quick Test: Correlation Calculator with Real yfinance Data

Tests correlation analysis with actual market data to validate integration.
This is NOT a unit test - it fetches real data from yfinance.
"""

import asyncio
from app.analysis.correlation_calculator import CorrelationCalculator
from app.models.analysis import CorrelationConfig


async def main():
    print("=" * 70)
    print("🧪 CORRELATION CALCULATOR - LIVE DATA TEST")
    print("=" * 70)
    print()

    # Test with tech portfolio: AAPL, NVDA, TSLA
    tickers = ["AAPL", "NVDA", "TSLA"]
    days = 90

    print(f"📥 Fetching {days} days of price data for {', '.join(tickers)}...")

    try:
        # Create calculator
        config = CorrelationConfig(
            method="pearson",
            rolling_window=None,  # Full period
            min_periods=30,
        )
        calculator = CorrelationCalculator(config)

        # Fetch synchronized data from yfinance
        portfolio_data = await calculator.fetch_portfolio_data_from_yfinance(tickers, days)
        print(f"✅ Fetched {len(portfolio_data.dates)} data points")
        print(f"📅 Date range: {portfolio_data.dates[0]} to {portfolio_data.dates[-1]}")
        print()

        # Calculate correlation analysis
        print("🧮 Calculating portfolio correlation...")
        results = await calculator.calculate_portfolio_correlation(portfolio_data)
        print("✅ Calculation complete!")
        print()

        # Display results
        print("=" * 70)
        print(f"📊 PORTFOLIO DIVERSIFICATION ANALYSIS")
        print(f"📅 As of: {results.calculation_date}")
        print("=" * 70)
        print()

        # Diversification Score
        print("🎯 DIVERSIFICATION SCORE")
        print("-" * 70)
        print(f"  Score:                    {results.diversification_score:>10.3f}")

        if results.diversification_score > 0.6:
            rating = "Excellent"
            emoji = "✅"
        elif results.diversification_score > 0.4:
            rating = "Good"
            emoji = "🟢"
        elif results.diversification_score > 0.2:
            rating = "Moderate"
            emoji = "🟡"
        else:
            rating = "Poor"
            emoji = "🔴"

        print(f"  Rating:                   {emoji} {rating:>10}")
        print()

        # Correlation Matrix
        print("🔗 CORRELATION MATRIX")
        print("-" * 70)

        # Header row
        print(f"{'':>12}", end="")
        for ticker in results.tickers:
            print(f"{ticker:>10}", end="")
        print()

        # Matrix rows
        for ticker1 in results.tickers:
            print(f"  {ticker1:>10}", end="")
            for ticker2 in results.tickers:
                corr = results.correlation_matrix.correlation_matrix[ticker1][ticker2]
                print(f"{corr:>10.3f}", end="")
            print()
        print()

        # Average Correlation
        print("📊 PORTFOLIO METRICS")
        print("-" * 70)
        print(f"  Average Correlation:      {results.correlation_matrix.average_correlation:>10.3f}")

        if results.concentration_warning:
            print(f"  ⚠️  WARNING: High correlation (>{0.7:.1f}) indicates concentration risk!")
        else:
            print(f"  ✅ No concentration risk detected")
        print()

        # Pairwise Analysis
        print("🔍 PAIRWISE CORRELATIONS")
        print("-" * 70)

        pairs_analyzed = set()
        for i, ticker1 in enumerate(results.tickers):
            for j, ticker2 in enumerate(results.tickers):
                if i < j:  # Only upper triangle
                    pair_key = tuple(sorted([ticker1, ticker2]))
                    if pair_key not in pairs_analyzed:
                        pairs_analyzed.add(pair_key)
                        corr = results.correlation_matrix.correlation_matrix[ticker1][ticker2]

                        # Interpret correlation
                        if corr > 0.7:
                            interp = "Strong positive (move together)"
                            symbol = "📈"
                        elif corr > 0.5:
                            interp = "Moderate positive"
                            symbol = "↗️"
                        elif corr > 0.3:
                            interp = "Weak positive"
                            symbol = "→"
                        elif corr > -0.3:
                            interp = "Independent"
                            symbol = "⚪"
                        else:
                            interp = "Negative (hedge!)"
                            symbol = "🛡️"

                        print(f"  {ticker1} vs {ticker2}:  {corr:>6.3f}  {symbol}  {interp}")
        print()

        # Business Interpretation
        print("💡 INTERPRETATION")
        print("-" * 70)

        if results.diversification_score > 0.6:
            print("  Your portfolio shows excellent diversification. The assets have")
            print("  low correlation, providing good protection against market moves.")
        elif results.diversification_score > 0.4:
            print("  Your portfolio shows good diversification. Consider adding more")
            print("  uncorrelated assets for further risk reduction.")
        elif results.diversification_score > 0.2:
            print("  Your portfolio shows moderate diversification. The assets are")
            print("  somewhat correlated - consider adding uncorrelated positions.")
        else:
            print("  ⚠️  Your portfolio has poor diversification. The assets are highly")
            print("  correlated and will likely move together during market stress.")
            print("  Consider adding uncorrelated or negatively correlated assets.")

        print()
        print("=" * 70)
        print("⚠️  DISCLAIMER: For testing purposes only. Not investment advice.")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
