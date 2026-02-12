#!/usr/bin/env python3
"""
Quick Test: Momentum Calculator with Real yfinance Data

Tests momentum indicators with actual market data to validate integration.
This is NOT a unit test - it fetches real data from yfinance.
"""

import asyncio
from app.analysis.momentum_calculator import MomentumIndicators
from app.models.analysis import MomentumConfig


async def main():
    print("=" * 70)
    print("🧪 MOMENTUM CALCULATOR - LIVE DATA TEST")
    print("=" * 70)
    print()

    # Test with AAPL (should be stable, well-formed data)
    ticker = "AAPL"
    days = 90

    print(f"📥 Fetching {days} days of OHLC data for {ticker}...")

    try:
        # Create calculator
        config = MomentumConfig(
            rsi_period=14,
            macd_fast=12,
            macd_slow=26,
            macd_signal=9,
        )
        calculator = MomentumIndicators(config)

        # Fetch data from yfinance
        momentum_data = await calculator.fetch_momentum_data_from_yfinance(ticker, days)
        print(f"✅ Fetched {len(momentum_data.dates)} data points")
        print(f"📅 Date range: {momentum_data.dates[0]} to {momentum_data.dates[-1]}")
        print()

        # Calculate all momentum indicators
        print("🧮 Calculating momentum indicators...")
        results = await calculator.calculate_all(momentum_data)
        print("✅ Calculation complete!")
        print()

        # Display results
        print("=" * 70)
        print(f"📊 MOMENTUM ANALYSIS: {ticker}")
        print(f"📅 As of: {results.calculation_date}")
        print("=" * 70)
        print()

        # RSI
        print("📈 RELATIVE STRENGTH INDEX (RSI)")
        print("-" * 70)
        print(f"  Current RSI:              {results.rsi.current_rsi:>10.2f}")
        print(f"  Signal:                   {results.rsi.rsi_signal:>10}")
        print(f"  Period:                   {results.rsi.period:>10} days")
        if results.rsi.rsi_signal == "overbought":
            print("  🔴 OVERBOUGHT: RSI above 70, potential selling pressure")
        elif results.rsi.rsi_signal == "oversold":
            print("  🟢 OVERSOLD: RSI below 30, potential buying opportunity")
        else:
            print("  ⚪ NEUTRAL: RSI between 30-70, no extreme condition")
        print()

        # MACD
        print("📉 MACD (Moving Average Convergence Divergence)")
        print("-" * 70)
        print(f"  MACD Line:                {results.macd.macd_line:>10.2f}")
        print(f"  Signal Line:              {results.macd.signal_line:>10.2f}")
        print(f"  Histogram:                {results.macd.histogram:>10.2f}")
        print(f"  Trend:                    {results.macd.signal:>10}")
        if results.macd.signal == "bullish":
            print("  📈 BULLISH: MACD above signal line (upward momentum)")
        else:
            print("  📉 BEARISH: MACD below signal line (downward momentum)")
        print()

        # Stochastic
        print("🎯 STOCHASTIC OSCILLATOR")
        print("-" * 70)
        print(f"  %K (Fast):                {results.stochastic.k_value:>10.2f}")
        print(f"  %D (Slow):                {results.stochastic.d_value:>10.2f}")
        print(f"  Signal:                   {results.stochastic.signal:>10}")
        if results.stochastic.signal == "overbought":
            print("  🔴 OVERBOUGHT: %K > 80, potential reversal down")
        elif results.stochastic.signal == "oversold":
            print("  🟢 OVERSOLD: %K < 20, potential reversal up")
        else:
            print("  ⚪ NEUTRAL: %K between 20-80")
        print()

        # Williams %R
        print("📊 WILLIAMS %R")
        print("-" * 70)
        print(f"  Williams %R:              {results.williams_r.williams_r:>10.2f}")
        print(f"  Signal:                   {results.williams_r.signal:>10}")
        if results.williams_r.signal == "overbought":
            print("  🔴 OVERBOUGHT: %R > -20, potential sell signal")
        elif results.williams_r.signal == "oversold":
            print("  🟢 OVERSOLD: %R < -80, potential buy signal")
        else:
            print("  ⚪ NEUTRAL: %R between -20 and -80")
        print()

        # ROC
        print("🚀 RATE OF CHANGE (ROC)")
        print("-" * 70)
        print(f"  ROC:                      {results.roc.roc:>9.2f}%")
        print(f"  Signal:                   {results.roc.signal:>10}")
        if results.roc.signal == "bullish":
            print(f"  📈 BULLISH: Positive momentum ({results.roc.roc:.2f}% gain)")
        elif results.roc.signal == "bearish":
            print(f"  📉 BEARISH: Negative momentum ({abs(results.roc.roc):.2f}% loss)")
        else:
            print("  ⚪ NEUTRAL: No significant change")
        print()

        # Confluence Analysis
        print("🎯 MOMENTUM CONFLUENCE")
        print("-" * 70)

        bullish_count = 0
        bearish_count = 0

        if results.rsi.rsi_signal == "oversold":
            bullish_count += 1
        elif results.rsi.rsi_signal == "overbought":
            bearish_count += 1

        if results.macd.signal == "bullish":
            bullish_count += 1
        else:
            bearish_count += 1

        if results.stochastic.signal == "oversold":
            bullish_count += 1
        elif results.stochastic.signal == "overbought":
            bearish_count += 1

        if results.williams_r.signal == "oversold":
            bullish_count += 1
        elif results.williams_r.signal == "overbought":
            bearish_count += 1

        if results.roc.signal == "bullish":
            bullish_count += 1
        elif results.roc.signal == "bearish":
            bearish_count += 1

        print(f"  Bullish Signals:          {bullish_count:>10}/5")
        print(f"  Bearish Signals:          {bearish_count:>10}/5")
        print()

        if bullish_count >= 3:
            print(f"  ✅ STRONG BULLISH CONFLUENCE ({bullish_count}/5 indicators)")
        elif bearish_count >= 3:
            print(f"  ❌ STRONG BEARISH CONFLUENCE ({bearish_count}/5 indicators)")
        else:
            print("  ⚠️  MIXED SIGNALS: No clear confluence")

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
