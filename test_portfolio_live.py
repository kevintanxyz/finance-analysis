#!/usr/bin/env python3
"""
Quick Test: Portfolio Optimizer with Real yfinance Data

Tests Modern Portfolio Theory optimization with actual market data.
This is NOT a unit test - it fetches real data from yfinance.
"""

from __future__ import annotations

import asyncio
from app.analysis.portfolio_optimizer import PortfolioOptimizer
from app.models.analysis import OptimizationConfig


async def main():
    print("=" * 70)
    print("🧪 PORTFOLIO OPTIMIZER - LIVE DATA TEST")
    print("=" * 70)
    print()

    # Test with a diversified portfolio
    tickers = ["AAPL", "NVDA", "TSLA", "SPY"]
    days = 252  # 1 year of data

    print(f"📥 Fetching {days} days of data for portfolio: {', '.join(tickers)}...")
    print()

    try:
        # Fetch portfolio data
        data = await PortfolioOptimizer.fetch_portfolio_data(tickers, days=days)

        print(f"✅ Data fetched: {len(data.dates)} days ({data.dates[0]} to {data.dates[-1]})")
        print()

        # Test 1: Maximum Sharpe Ratio (Aggressive Growth)
        print("=" * 70)
        print(f"🔹 TEST 1: MAXIMUM SHARPE RATIO (Aggressive Growth)")
        print("=" * 70)

        config_max_sharpe = OptimizationConfig(
            method="max_sharpe",
            risk_free_rate=0.045,
            position_limits=(0.0, 1.0),  # No position limits
        )

        optimizer = PortfolioOptimizer(config_max_sharpe)
        result_sharpe = await optimizer.optimize(data)

        print(f"\nOptimization Method:     {result_sharpe.method.upper().replace('_', ' ')}")
        print(f"Expected Annual Return:  {result_sharpe.expected_return:>7.2%}")
        print(f"Expected Volatility:     {result_sharpe.expected_volatility:>7.2%}")
        print(f"Sharpe Ratio:            {result_sharpe.sharpe_ratio:>7.2f}")
        print(f"Diversification Ratio:   {result_sharpe.diversification_ratio:>7.2f}")
        print()

        print("💰 OPTIMAL ALLOCATION:")
        print("-" * 70)
        print(f"{'Asset':<10} {'Weight':>10} {'$100k Allocation':>20}")
        print("-" * 70)

        sorted_weights = sorted(
            result_sharpe.optimal_weights.items(), key=lambda x: x[1], reverse=True
        )

        for ticker, weight in sorted_weights:
            allocation = weight * 100000
            print(f"{ticker:<10} {weight:>9.2%} ${allocation:>19,.0f}")

        print("-" * 70)
        print(f"{'TOTAL':<10} {sum(result_sharpe.optimal_weights.values()):>9.2%} ${'100,000':>19}")
        print()

        # Interpret Sharpe ratio
        if result_sharpe.sharpe_ratio > 2.0:
            sharpe_label = "EXCELLENT"
        elif result_sharpe.sharpe_ratio > 1.0:
            sharpe_label = "GOOD"
        elif result_sharpe.sharpe_ratio > 0.5:
            sharpe_label = "FAIR"
        else:
            sharpe_label = "POOR"

        print(f"📊 Sharpe Ratio Interpretation: {sharpe_label}")
        print()

        # Test 2: Minimum Variance (Conservative)
        print("=" * 70)
        print(f"🔹 TEST 2: MINIMUM VARIANCE (Conservative / Defensive)")
        print("=" * 70)

        config_min_var = OptimizationConfig(
            method="min_variance",
            risk_free_rate=0.045,
        )

        optimizer_min_var = PortfolioOptimizer(config_min_var)
        result_min_var = await optimizer_min_var.optimize(data)

        print(f"\nOptimization Method:     {result_min_var.method.upper().replace('_', ' ')}")
        print(f"Expected Annual Return:  {result_min_var.expected_return:>7.2%}")
        print(f"Expected Volatility:     {result_min_var.expected_volatility:>7.2%}")
        print(f"Sharpe Ratio:            {result_min_var.sharpe_ratio:>7.2f}")
        print(f"Diversification Ratio:   {result_min_var.diversification_ratio:>7.2f}")
        print()

        print("💰 OPTIMAL ALLOCATION:")
        print("-" * 70)
        print(f"{'Asset':<10} {'Weight':>10} {'$100k Allocation':>20}")
        print("-" * 70)

        sorted_weights_min = sorted(
            result_min_var.optimal_weights.items(), key=lambda x: x[1], reverse=True
        )

        for ticker, weight in sorted_weights_min:
            allocation = weight * 100000
            print(f"{ticker:<10} {weight:>9.2%} ${allocation:>19,.0f}")

        print("-" * 70)
        print(f"{'TOTAL':<10} {sum(result_min_var.optimal_weights.values()):>9.2%} ${'100,000':>19}")
        print()

        # Test 3: Risk Parity (All-Weather)
        print("=" * 70)
        print(f"🔹 TEST 3: RISK PARITY (All-Weather Portfolio)")
        print("=" * 70)

        config_risk_parity = OptimizationConfig(
            method="risk_parity",
            risk_free_rate=0.045,
        )

        optimizer_rp = PortfolioOptimizer(config_risk_parity)
        result_rp = await optimizer_rp.optimize(data)

        print(f"\nOptimization Method:     {result_rp.method.upper().replace('_', ' ')}")
        print(f"Expected Annual Return:  {result_rp.expected_return:>7.2%}")
        print(f"Expected Volatility:     {result_rp.expected_volatility:>7.2%}")
        print(f"Sharpe Ratio:            {result_rp.sharpe_ratio:>7.2f}")
        print(f"Diversification Ratio:   {result_rp.diversification_ratio:>7.2f}")
        print()

        print("💰 OPTIMAL ALLOCATION:")
        print("-" * 70)
        print(f"{'Asset':<10} {'Weight':>10} {'$100k Allocation':>20}")
        print("-" * 70)

        sorted_weights_rp = sorted(
            result_rp.optimal_weights.items(), key=lambda x: x[1], reverse=True
        )

        for ticker, weight in sorted_weights_rp:
            allocation = weight * 100000
            print(f"{ticker:<10} {weight:>9.2%} ${allocation:>19,.0f}")

        print("-" * 70)
        print(f"{'TOTAL':<10} {sum(result_rp.optimal_weights.values()):>9.2%} ${'100,000':>19}")
        print()

        # Test 4: Max Sharpe with Position Limits (Diversified)
        print("=" * 70)
        print(f"🔹 TEST 4: MAX SHARPE WITH POSITION LIMITS (Diversified)")
        print("=" * 70)

        config_limited = OptimizationConfig(
            method="max_sharpe",
            risk_free_rate=0.045,
            position_limits=(0.0, 0.30),  # Max 30% per position
        )

        optimizer_limited = PortfolioOptimizer(config_limited)
        result_limited = await optimizer_limited.optimize(data)

        print(f"\nOptimization Method:     MAX SHARPE (30% Position Limit)")
        print(f"Expected Annual Return:  {result_limited.expected_return:>7.2%}")
        print(f"Expected Volatility:     {result_limited.expected_volatility:>7.2%}")
        print(f"Sharpe Ratio:            {result_limited.sharpe_ratio:>7.2f}")
        print(f"Diversification Ratio:   {result_limited.diversification_ratio:>7.2f}")
        print()

        print("💰 OPTIMAL ALLOCATION:")
        print("-" * 70)
        print(f"{'Asset':<10} {'Weight':>10} {'$100k Allocation':>20}")
        print("-" * 70)

        sorted_weights_limited = sorted(
            result_limited.optimal_weights.items(), key=lambda x: x[1], reverse=True
        )

        for ticker, weight in sorted_weights_limited:
            allocation = weight * 100000
            print(f"{ticker:<10} {weight:>9.2%} ${allocation:>19,.0f}")

        print("-" * 70)
        print(f"{'TOTAL':<10} {sum(result_limited.optimal_weights.values()):>9.2%} ${'100,000':>19}")
        print()

        # Comparison Summary
        print("=" * 70)
        print(f"💡 COMPARISON SUMMARY")
        print("=" * 70)
        print()

        print(f"{'Strategy':<25} {'Return':>10} {'Risk':>10} {'Sharpe':>10}")
        print("-" * 70)
        print(
            f"{'Max Sharpe (Aggressive)':<25} {result_sharpe.expected_return:>9.2%} "
            f"{result_sharpe.expected_volatility:>9.2%} {result_sharpe.sharpe_ratio:>9.2f}"
        )
        print(
            f"{'Min Variance (Defensive)':<25} {result_min_var.expected_return:>9.2%} "
            f"{result_min_var.expected_volatility:>9.2%} {result_min_var.sharpe_ratio:>9.2f}"
        )
        print(
            f"{'Risk Parity (Balanced)':<25} {result_rp.expected_return:>9.2%} "
            f"{result_rp.expected_volatility:>9.2%} {result_rp.sharpe_ratio:>9.2f}"
        )
        print(
            f"{'Max Sharpe + Limits':<25} {result_limited.expected_return:>9.2%} "
            f"{result_limited.expected_volatility:>9.2%} {result_limited.sharpe_ratio:>9.2f}"
        )
        print()

        print("🎯 RECOMMENDATIONS:")
        print("-" * 70)
        print(
            f"  • **Aggressive Growth**: Max Sharpe (Sharpe: {result_sharpe.sharpe_ratio:.2f})"
        )
        print(f"     → Highest expected return but concentrated positions")
        print()
        print(
            f"  • **Conservative/Defensive**: Min Variance (Volatility: {result_min_var.expected_volatility:.1%})"
        )
        print(f"     → Lowest risk, capital preservation focus")
        print()
        print(
            f"  • **Balanced/All-Weather**: Risk Parity (Div Ratio: {result_rp.diversification_ratio:.2f})"
        )
        print(f"     → Equal risk contribution, stable across market regimes")
        print()
        print(f"  • **Diversified Growth**: Max Sharpe + Limits (Max 30% per position)")
        print(f"     → Good risk-adjusted returns with forced diversification")
        print()

        print("=" * 70)
        print("⚠️  DISCLAIMER: For testing purposes only. Not investment advice.")
        print("             Past performance does not guarantee future results.")
        print("             Consult a financial advisor before investing.")
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
