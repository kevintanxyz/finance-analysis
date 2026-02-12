#!/usr/bin/env python3
"""
Quick Test: Options Pricer with Real yfinance Data

Tests Black-Scholes option pricing with actual market data.
This is NOT a unit test - it fetches real data from yfinance.
"""

from __future__ import annotations

import asyncio
from datetime import date
from app.analysis.options_calculator import OptionsCalculator
from app.models.analysis import BlackScholesInput


async def main():
    print("=" * 70)
    print("🧪 OPTIONS PRICER - LIVE DATA TEST")
    print("=" * 70)
    print()

    # Test with Apple (AAPL) options
    ticker = "AAPL"
    days_to_expiry = 30  # 30-day options

    print(f"📥 Fetching market data for {ticker}...")

    try:
        # Create calculator
        calculator = OptionsCalculator()

        # Fetch current price and historical volatility
        current_price, historical_vol = await calculator.fetch_stock_data_for_options(
            ticker, days=90
        )

        print(f"✅ Current Price: ${current_price:.2f}")
        print(f"📊 Historical Volatility: {historical_vol:.1%}")
        print()

        # Calculate ATM call option
        atm_strike = round(current_price / 5) * 5  # Round to nearest $5
        print(f"🔹 Testing ATM CALL option: Strike ${atm_strike:.2f}")
        print("-" * 70)

        call_input = BlackScholesInput(
            spot_price=current_price,
            strike=atm_strike,
            time_to_expiry=days_to_expiry / 365,
            volatility=historical_vol,
            risk_free_rate=0.045,
            dividend_yield=0.005,  # AAPL pays ~0.5% dividend
            option_type="call",
        )

        call_results = await calculator.price_option(call_input, ticker)

        print(f"Option Type:         CALL")
        print(f"Strike Price:        ${atm_strike:.2f}")
        print(f"Days to Expiry:      {days_to_expiry}")
        print(f"Moneyness:           {call_results.moneyness}")
        print()

        print(f"💰 PRICING:")
        print(f"  Theoretical Price:   ${call_results.option_price:.2f}")
        print(f"  Intrinsic Value:     ${call_results.intrinsic_value:.2f}")
        print(f"  Time Value:          ${call_results.time_value:.2f}")
        print()

        print(f"📊 GREEKS:")
        print(f"  Delta:               {call_results.delta:>7.3f}  (${abs(call_results.delta):.2f} per $1 stock move)")
        print(f"  Gamma:               {call_results.gamma:>7.4f}  (delta changes by {call_results.gamma:.4f} per $1)")
        print(f"  Theta:               {call_results.theta:>7.2f}  (${abs(call_results.theta):.2f} time decay per day)")
        print(f"  Vega:                {call_results.vega:>7.2f}  (${abs(call_results.vega):.2f} per 1% vol change)")
        print(f"  Rho:                 {call_results.rho:>7.2f}  (${abs(call_results.rho):.2f} per 1% rate change)")
        print()

        # Calculate OTM protective put
        put_strike = atm_strike - 10  # $10 OTM protective put
        print(f"🔹 Testing OTM PROTECTIVE PUT: Strike ${put_strike:.2f}")
        print("-" * 70)

        put_input = BlackScholesInput(
            spot_price=current_price,
            strike=put_strike,
            time_to_expiry=days_to_expiry / 365,
            volatility=historical_vol,
            risk_free_rate=0.045,
            dividend_yield=0.005,
            option_type="put",
        )

        put_results = await calculator.price_option(put_input, ticker)

        print(f"Option Type:         PUT")
        print(f"Strike Price:        ${put_strike:.2f}")
        print(f"Days to Expiry:      {days_to_expiry}")
        print(f"Moneyness:           {put_results.moneyness}")
        print()

        print(f"💰 PRICING:")
        print(f"  Theoretical Price:   ${put_results.option_price:.2f}")
        print(f"  Intrinsic Value:     ${put_results.intrinsic_value:.2f}")
        print(f"  Time Value:          ${put_results.time_value:.2f}")
        print(f"  → Cost per contract: ${put_results.option_price * 100:.0f} ({put_results.option_price / current_price:.1%} of stock price)")
        print()

        print(f"📊 GREEKS:")
        print(f"  Delta:               {put_results.delta:>7.3f}  (protection ratio: {abs(put_results.delta):.1%})")
        print(f"  Gamma:               {put_results.gamma:>7.4f}  (delta changes by {put_results.gamma:.4f} per $1)")
        print(f"  Theta:               {put_results.theta:>7.2f}  (${abs(put_results.theta):.2f} time decay per day)")
        print(f"  Vega:                {put_results.vega:>7.2f}  (${abs(put_results.vega):.2f} per 1% vol change)")
        print(f"  Rho:                 {put_results.rho:>7.2f}  (${abs(put_results.rho):.2f} per 1% rate change)")
        print()

        # Business Interpretation
        print("=" * 70)
        print(f"💡 BUSINESS INTERPRETATION")
        print("=" * 70)
        print()

        print(f"**{ticker} CALL Option ({days_to_expiry} days, ${atm_strike} strike):**")
        if call_results.moneyness == "ATM":
            print(f"  ✓ This is an at-the-money call with delta ~{call_results.delta:.2f}")
            print(f"  ✓ Highly sensitive to stock price moves (high gamma)")
            print(f"  ✓ For every $1 stock increase → ${call_results.delta:.2f} option gain")
        print()

        print(f"**{ticker} PROTECTIVE PUT ({days_to_expiry} days, ${put_strike} strike):**")
        protection_pct = abs(current_price - put_strike) / current_price
        print(f"  ✓ Protects against downside below ${put_strike:.2f} ({protection_pct:.1%} below current price)")
        print(f"  ✓ Insurance cost: ${put_results.option_price:.2f} per share (${put_results.option_price * 100:.0f} per contract)")
        print(f"  ✓ Daily time decay: ${abs(put_results.theta):.2f} per day")

        total_decay = abs(put_results.theta) * days_to_expiry
        print(f"  ✓ Total time decay over {days_to_expiry} days: ~${total_decay:.2f}")

        if abs(put_results.delta) < 0.30:
            print(f"  ⚠️  Low delta ({put_results.delta:.2f}) means limited protection")
            print(f"     Consider a higher strike for better protection")
        else:
            print(f"  ✓ Good protection ratio: Delta {put_results.delta:.2f} means {abs(put_results.delta):.0%} hedge")

        print()
        print("=" * 70)
        print("⚠️  DISCLAIMER: For testing purposes only. Not investment advice.")
        print("             Theoretical prices may differ from actual market prices.")
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
