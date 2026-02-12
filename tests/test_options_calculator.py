"""
Unit Tests for Options Calculator

Tests Black-Scholes option pricing and Greeks calculations.
All tests use synthetic data with no external API calls.

BUSINESS CRITICAL: Options pricing drives hedging and strategy decisions.
All Black-Scholes formulas must be verified and validated.
"""

import pytest
from datetime import date
from pydantic import ValidationError

from app.models.analysis import BlackScholesInput, GreeksOutput
from app.analysis.options_calculator import OptionsCalculator


# ============================================================================
# Fixtures - Test Data
# ============================================================================

@pytest.fixture
def calculator():
    """Create options calculator instance."""
    return OptionsCalculator()


@pytest.fixture
def atm_call_input():
    """
    At-the-money call option (S = K = 100).

    EXPECTED RESULTS:
    - Option price should be mostly time value
    - Delta should be around 0.50
    - Moneyness should be ATM
    """
    return BlackScholesInput(
        spot_price=100.0,
        strike=100.0,
        time_to_expiry=0.25,  # 3 months
        volatility=0.30,  # 30%
        risk_free_rate=0.05,
        dividend_yield=0.0,
        option_type="call",
    )


@pytest.fixture
def itm_put_input():
    """
    In-the-money put option (S = 90, K = 100).

    EXPECTED RESULTS:
    - Option price should include $10 intrinsic value
    - Delta should be negative (around -0.70)
    - Moneyness should be ITM
    """
    return BlackScholesInput(
        spot_price=90.0,
        strike=100.0,
        time_to_expiry=0.25,  # 3 months
        volatility=0.30,  # 30%
        risk_free_rate=0.05,
        dividend_yield=0.0,
        option_type="put",
    )


@pytest.fixture
def otm_call_input():
    """
    Out-of-the-money call option (S = 100, K = 120).

    EXPECTED RESULTS:
    - Option price should be all time value (no intrinsic)
    - Delta should be low (< 0.30)
    - Moneyness should be OTM
    """
    return BlackScholesInput(
        spot_price=100.0,
        strike=120.0,
        time_to_expiry=0.25,  # 3 months
        volatility=0.30,  # 30%
        risk_free_rate=0.05,
        dividend_yield=0.0,
        option_type="call",
    )


# ============================================================================
# Tests - Pydantic Model Validation
# ============================================================================

def test_black_scholes_input_validation():
    """Test BlackScholesInput validation rules."""

    # Valid input
    valid_input = BlackScholesInput(
        spot_price=100.0,
        strike=110.0,
        time_to_expiry=0.5,
        volatility=0.25,
        risk_free_rate=0.04,
        dividend_yield=0.02,
        option_type="call",
    )
    assert valid_input.spot_price == 100.0
    assert valid_input.option_type == "call"

    # Invalid: Negative spot price
    with pytest.raises(ValidationError):
        BlackScholesInput(
            spot_price=-100.0,  # Negative
            strike=110.0,
            time_to_expiry=0.5,
            volatility=0.25,
            option_type="call",
        )

    # Invalid: Zero time to expiry
    with pytest.raises(ValidationError):
        BlackScholesInput(
            spot_price=100.0,
            strike=110.0,
            time_to_expiry=0.0,  # Zero
            volatility=0.25,
            option_type="call",
        )

    # Invalid: Extreme volatility (> 3.0)
    with pytest.raises(ValidationError):
        BlackScholesInput(
            spot_price=100.0,
            strike=110.0,
            time_to_expiry=0.5,
            volatility=3.5,  # > 3.0
            option_type="call",
        )

    # Invalid: Invalid option type
    with pytest.raises(ValidationError):
        BlackScholesInput(
            spot_price=100.0,
            strike=110.0,
            time_to_expiry=0.5,
            volatility=0.25,
            option_type="invalid",  # Must be "call" or "put"
        )


# ============================================================================
# Tests - Call Option Pricing
# ============================================================================

@pytest.mark.asyncio
async def test_atm_call_pricing(calculator, atm_call_input):
    """
    Test ATM call option pricing.

    BUSINESS VALIDATION:
    - ATM options have delta around 0.50
    - Price should be mostly time value
    - Option should be classified as ATM
    """
    results = await calculator.price_option(atm_call_input, "TEST")

    # Verify output type
    assert isinstance(results, GreeksOutput)
    assert results.ticker == "TEST"
    assert results.option_type == "call"

    # Verify pricing
    assert results.option_price > 0.0, "Option price should be positive"
    assert results.intrinsic_value == 0.0, "ATM call has no intrinsic value"
    assert results.time_value == results.option_price, "ATM option is all time value"

    # Verify delta (should be around 0.50 for ATM)
    assert 0.40 < results.delta < 0.60, "ATM call delta should be around 0.50"

    # Verify moneyness
    assert results.moneyness == "ATM"

    # Verify Greeks are reasonable
    assert results.gamma > 0.0, "Gamma should be positive"
    assert results.theta < 0.0, "Theta should be negative (time decay)"
    assert results.vega > 0.0, "Vega should be positive"


@pytest.mark.asyncio
async def test_otm_call_pricing(calculator, otm_call_input):
    """
    Test OTM call option pricing.

    BUSINESS VALIDATION:
    - OTM options have low delta
    - Price should be all time value (no intrinsic)
    - Should be classified as OTM
    """
    results = await calculator.price_option(otm_call_input, "TEST")

    # Verify pricing
    assert results.option_price > 0.0, "Option price should be positive"
    assert results.intrinsic_value == 0.0, "OTM call has no intrinsic value"
    assert results.time_value == results.option_price, "OTM option is all time value"

    # Verify delta (should be low for OTM)
    assert results.delta < 0.40, "OTM call delta should be low"

    # Verify moneyness
    assert results.moneyness == "OTM"


# ============================================================================
# Tests - Put Option Pricing
# ============================================================================

@pytest.mark.asyncio
async def test_itm_put_pricing(calculator, itm_put_input):
    """
    Test ITM put option pricing.

    BUSINESS VALIDATION:
    - ITM puts have intrinsic value (K - S)
    - Delta should be negative (around -0.70 for ITM)
    - Should be classified as ITM
    """
    results = await calculator.price_option(itm_put_input, "TEST")

    # Verify output type
    assert isinstance(results, GreeksOutput)
    assert results.option_type == "put"

    # Verify pricing
    assert results.option_price > 0.0, "Option price should be positive"
    assert results.intrinsic_value == 10.0, "ITM put has $10 intrinsic value (100 - 90)"
    assert results.time_value > 0.0, "Option should have time value"
    assert results.option_price == results.intrinsic_value + results.time_value

    # Verify delta (should be negative for puts)
    assert results.delta < 0.0, "Put delta should be negative"
    assert -0.80 < results.delta < -0.60, "Deep ITM put delta should be around -0.70"

    # Verify moneyness
    assert results.moneyness == "ITM"


@pytest.mark.asyncio
async def test_atm_put_pricing(calculator):
    """
    Test ATM put option pricing.

    BUSINESS VALIDATION:
    - ATM puts have delta around -0.50
    - Price should be mostly time value
    """
    atm_put = BlackScholesInput(
        spot_price=100.0,
        strike=100.0,
        time_to_expiry=0.25,
        volatility=0.30,
        option_type="put",
    )

    results = await calculator.price_option(atm_put, "TEST")

    # Verify delta (should be around -0.50 for ATM put)
    assert -0.60 < results.delta < -0.40, "ATM put delta should be around -0.50"

    # Verify moneyness
    assert results.moneyness == "ATM"


# ============================================================================
# Tests - Put-Call Parity
# ============================================================================

@pytest.mark.asyncio
async def test_put_call_parity(calculator):
    """
    Test put-call parity relationship.

    FORMULA:
        Call - Put = S * e^(-qT) - K * e^(-rT)

    BUSINESS VALIDATION:
    - Put-call parity should hold for European options
    - Violation indicates arbitrage opportunity
    """
    # Common parameters
    params_call = BlackScholesInput(
        spot_price=100.0,
        strike=100.0,
        time_to_expiry=0.25,
        volatility=0.30,
        risk_free_rate=0.05,
        dividend_yield=0.0,
        option_type="call",
    )

    params_put = BlackScholesInput(
        spot_price=100.0,
        strike=100.0,
        time_to_expiry=0.25,
        volatility=0.30,
        risk_free_rate=0.05,
        dividend_yield=0.0,
        option_type="put",
    )

    # Calculate prices
    call_result = await calculator.price_option(params_call, "TEST")
    put_result = await calculator.price_option(params_put, "TEST")

    # Calculate put-call parity
    # C - P = S - K * e^(-rT)
    import math
    lhs = call_result.option_price - put_result.option_price
    rhs = 100.0 - 100.0 * math.exp(-0.05 * 0.25)

    # Should be approximately equal (within $0.01)
    assert abs(lhs - rhs) < 0.01, f"Put-call parity violated: {lhs:.4f} != {rhs:.4f}"


# ============================================================================
# Tests - Greeks Calculations
# ============================================================================

@pytest.mark.asyncio
async def test_gamma_positive(calculator, atm_call_input):
    """
    Test that gamma is always positive.

    BUSINESS VALIDATION:
    - Gamma measures convexity (second derivative)
    - Gamma is always positive for both calls and puts
    - Highest for ATM options near expiry
    """
    results = await calculator.price_option(atm_call_input, "TEST")

    assert results.gamma > 0.0, "Gamma should always be positive"
    assert results.gamma < 0.1, "Gamma should be reasonable magnitude"


@pytest.mark.asyncio
async def test_theta_negative(calculator, atm_call_input):
    """
    Test that theta is always negative.

    BUSINESS VALIDATION:
    - Theta measures time decay
    - Options lose value over time (theta is negative)
    - ATM options have highest theta
    """
    results = await calculator.price_option(atm_call_input, "TEST")

    assert results.theta < 0.0, "Theta should always be negative (time decay)"


@pytest.mark.asyncio
async def test_vega_positive(calculator, atm_call_input):
    """
    Test that vega is always positive.

    BUSINESS VALIDATION:
    - Vega measures volatility sensitivity
    - Higher volatility always increases option value
    - Vega is positive for both calls and puts
    """
    results = await calculator.price_option(atm_call_input, "TEST")

    assert results.vega > 0.0, "Vega should always be positive"


# ============================================================================
# Tests - Moneyness Classification
# ============================================================================

@pytest.mark.asyncio
async def test_moneyness_classification(calculator):
    """
    Test moneyness classification for various scenarios.

    BUSINESS VALIDATION:
    - ITM: In the money (call: S > K, put: S < K)
    - ATM: At the money (S ≈ K, within 2%)
    - OTM: Out of the money (call: S < K, put: S > K)
    """
    # Deep ITM call
    itm_call = BlackScholesInput(
        spot_price=120.0, strike=100.0, time_to_expiry=0.25,
        volatility=0.30, option_type="call"
    )
    result = await calculator.price_option(itm_call, "TEST")
    assert result.moneyness == "ITM", "S=120, K=100 should be ITM call"
    assert result.intrinsic_value == 20.0, "ITM call intrinsic = S - K"

    # Deep OTM call
    otm_call = BlackScholesInput(
        spot_price=80.0, strike=100.0, time_to_expiry=0.25,
        volatility=0.30, option_type="call"
    )
    result = await calculator.price_option(otm_call, "TEST")
    assert result.moneyness == "OTM", "S=80, K=100 should be OTM call"
    assert result.intrinsic_value == 0.0, "OTM call has no intrinsic value"

    # Deep ITM put
    itm_put = BlackScholesInput(
        spot_price=80.0, strike=100.0, time_to_expiry=0.25,
        volatility=0.30, option_type="put"
    )
    result = await calculator.price_option(itm_put, "TEST")
    assert result.moneyness == "ITM", "S=80, K=100 should be ITM put"
    assert result.intrinsic_value == 20.0, "ITM put intrinsic = K - S"

    # Deep OTM put
    otm_put = BlackScholesInput(
        spot_price=120.0, strike=100.0, time_to_expiry=0.25,
        volatility=0.30, option_type="put"
    )
    result = await calculator.price_option(otm_put, "TEST")
    assert result.moneyness == "OTM", "S=120, K=100 should be OTM put"
    assert result.intrinsic_value == 0.0, "OTM put has no intrinsic value"


# ============================================================================
# Tests - Edge Cases
# ============================================================================

@pytest.mark.asyncio
async def test_near_expiry_option(calculator):
    """
    Test option near expiry (high theta).

    BUSINESS VALIDATION:
    - Options near expiry have high time decay
    - Theta should be more negative
    """
    near_expiry = BlackScholesInput(
        spot_price=100.0,
        strike=100.0,
        time_to_expiry=7/365,  # 1 week
        volatility=0.30,
        option_type="call",
    )

    results = await calculator.price_option(near_expiry, "TEST")

    assert results.option_price > 0.0, "Option should have some value"
    assert results.theta < -0.05, "Near-expiry option should have high theta"


@pytest.mark.asyncio
async def test_high_volatility_increases_price(calculator):
    """
    Test that higher volatility increases option price.

    BUSINESS VALIDATION:
    - Higher volatility = higher option value
    - Vega measures this sensitivity
    """
    low_vol = BlackScholesInput(
        spot_price=100.0, strike=100.0, time_to_expiry=0.25,
        volatility=0.15, option_type="call"
    )

    high_vol = BlackScholesInput(
        spot_price=100.0, strike=100.0, time_to_expiry=0.25,
        volatility=0.50, option_type="call"
    )

    low_vol_result = await calculator.price_option(low_vol, "TEST")
    high_vol_result = await calculator.price_option(high_vol, "TEST")

    assert high_vol_result.option_price > low_vol_result.option_price, \
        "Higher volatility should increase option price"


# ============================================================================
# Integration Test - Full Workflow
# ============================================================================

@pytest.mark.asyncio
async def test_full_options_workflow(calculator):
    """
    Integration test: Full options pricing workflow.

    BUSINESS CRITICAL: This simulates the actual MCP tool workflow.
    """
    # Create input for a protective put strategy
    protective_put = BlackScholesInput(
        spot_price=150.0,
        strike=145.0,  # 3.3% OTM
        time_to_expiry=30/365,  # 30 days
        volatility=0.35,  # 35% vol
        risk_free_rate=0.045,
        dividend_yield=0.02,
        option_type="put",
    )

    # Calculate option price and Greeks
    results = await calculator.price_option(protective_put, "STOCK")

    # Verify all components are present
    assert results.ticker == "STOCK"
    assert results.option_type == "put"
    assert results.calculation_date == date.today()

    # Verify pricing components
    assert results.option_price > 0.0
    assert results.intrinsic_value >= 0.0
    assert results.time_value >= 0.0
    assert results.option_price == results.intrinsic_value + results.time_value

    # Verify Greeks
    assert -1.0 <= results.delta <= 0.0, "Put delta should be negative"
    assert results.gamma > 0.0
    assert results.theta < 0.0
    assert results.vega > 0.0

    # Verify moneyness
    assert results.moneyness in ["ITM", "ATM", "OTM"]

    # Verify input parameters are preserved
    assert results.spot_price == 150.0
    assert results.strike == 145.0
    assert results.time_to_expiry == 30/365


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
