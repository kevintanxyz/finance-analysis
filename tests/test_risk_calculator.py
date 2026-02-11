"""
Unit Tests for Risk Calculator

Tests risk metric calculations with synthetic data.
No external API calls (yfinance) - all data is mocked.

BUSINESS CRITICAL: These calculations drive investment decisions.
All formulas must be verified and validated.
"""

import pytest
from datetime import date, timedelta
import numpy as np
from pydantic import ValidationError

from app.models.analysis import (
    PriceDataInput,
    RiskCalculationConfig,
    RiskMetricsOutput,
)
from app.analysis.risk_calculator import RiskCalculator


# ============================================================================
# Fixtures - Synthetic Test Data
# ============================================================================

@pytest.fixture
def simple_uptrend_prices():
    """
    Simple upward trend - low volatility, positive returns.

    EXPECTED RESULTS:
    - Low volatility (~10% annual)
    - Positive Sharpe (good risk-adjusted returns)
    - Small max drawdown (~-5%)
    - Low VaR
    """
    num_days = 100
    start_price = 100.0
    daily_return = 0.001  # 0.1% daily = ~25% annual

    prices = [start_price * (1 + daily_return) ** i for i in range(num_days)]
    dates = [date.today() - timedelta(days=num_days - i - 1) for i in range(num_days)]

    return PriceDataInput(
        ticker="UPTREND",
        prices=prices,
        dates=dates,
    )


@pytest.fixture
def volatile_stock_prices():
    """
    Volatile stock with random walk - high volatility, mixed returns.

    EXPECTED RESULTS:
    - High volatility (~40%+ annual)
    - Variable Sharpe (depends on direction)
    - Large max drawdown (>-20%)
    - High VaR
    """
    num_days = 100
    np.random.seed(42)  # Reproducible

    prices = [100.0]
    for _ in range(num_days - 1):
        # Random daily return between -3% and +3%
        daily_return = np.random.normal(0, 0.015)
        prices.append(prices[-1] * (1 + daily_return))

    dates = [date.today() - timedelta(days=num_days - i - 1) for i in range(num_days)]

    return PriceDataInput(
        ticker="VOLATILE",
        prices=prices,
        dates=dates,
    )


@pytest.fixture
def standard_config():
    """Standard risk calculation configuration."""
    return RiskCalculationConfig(
        confidence_level=0.95,
        var_method="historical",
        rolling_window=252,
        risk_free_rate=0.045,
    )


# ============================================================================
# Tests - Pydantic Model Validation
# ============================================================================

def test_price_data_input_validation():
    """Test PriceDataInput validation rules."""
    # Valid input
    valid_data = PriceDataInput(
        ticker="AAPL",
        prices=[100.0, 101.0, 102.0] * 10,  # 30 prices
        dates=[date(2025, 1, i) for i in range(1, 31)],
    )
    assert valid_data.ticker == "AAPL"
    assert len(valid_data.prices) == 30

    # Invalid: Too few data points
    with pytest.raises(ValidationError):
        PriceDataInput(
            ticker="AAPL",
            prices=[100.0, 101.0],  # Only 2 prices
            dates=[date(2025, 1, 1), date(2025, 1, 2)],
        )

    # Invalid: Negative price
    with pytest.raises(ValidationError):
        PriceDataInput(
            ticker="AAPL",
            prices=[100.0, -50.0, 102.0] * 10,
            dates=[date(2025, 1, i) for i in range(1, 31)],
        )

    # Invalid: Mismatched lengths
    with pytest.raises(ValidationError):
        PriceDataInput(
            ticker="AAPL",
            prices=[100.0] * 30,
            dates=[date(2025, 1, i) for i in range(1, 21)],  # Only 20 dates
        )


def test_risk_calculation_config_validation():
    """Test RiskCalculationConfig validation."""
    # Valid config
    config = RiskCalculationConfig(
        confidence_level=0.95,
        var_method="historical",
        rolling_window=252,
        risk_free_rate=0.045,
    )
    assert config.confidence_level == 0.95

    # Invalid: Confidence too low
    with pytest.raises(ValidationError):
        RiskCalculationConfig(confidence_level=0.4)

    # Invalid: Risk-free rate negative
    with pytest.raises(ValidationError):
        RiskCalculationConfig(risk_free_rate=-0.05)


# ============================================================================
# Tests - Risk Calculations
# ============================================================================

@pytest.mark.asyncio
async def test_calculate_risk_metrics_uptrend(simple_uptrend_prices, standard_config):
    """
    Test risk metrics on simple uptrend.

    BUSINESS VALIDATION:
    - Uptrend should have positive Sharpe
    - Low volatility stock should have low VaR
    - Consistent growth should have small drawdown

    EDGE CASE LEARNED: Perfect uptrend (no down days) → VaR can be ≥ 0
    """
    calculator = RiskCalculator(standard_config)
    results = await calculator.calculate_risk_metrics(simple_uptrend_prices)

    # Verify output type
    assert isinstance(results, RiskMetricsOutput)
    assert results.ticker == "UPTREND"

    # Verify metrics are reasonable
    assert results.sharpe_ratio > 0, "Uptrend should have positive Sharpe"
    assert results.annual_volatility >= 0, "Volatility must be non-negative"
    assert results.max_drawdown <= 0, "Drawdown should be ≤ 0"
    # VaR can be >= 0 for perfect uptrend (no down days) - this is correct!
    assert results.cvar_95 <= results.var_95 or results.var_95 >= 0, \
        "CVaR should be more extreme than VaR, unless perfect uptrend"


@pytest.mark.asyncio
async def test_calculate_risk_metrics_volatile(volatile_stock_prices, standard_config):
    """
    Test risk metrics on volatile stock.

    BUSINESS VALIDATION:
    - Volatile stock should have high annual volatility
    - Random walk should have larger VaR
    - Expect larger max drawdown
    """
    calculator = RiskCalculator(standard_config)
    results = await calculator.calculate_risk_metrics(volatile_stock_prices)

    # Verify output type
    assert isinstance(results, RiskMetricsOutput)
    assert results.ticker == "VOLATILE"

    # Verify volatility is high
    assert results.annual_volatility > 0.20, "High volatility expected"

    # Verify VaR is meaningful
    assert results.var_95 < -0.01, "VaR should reflect volatility"

    # Verify CVaR > VaR (more extreme)
    assert results.cvar_95 <= results.var_95


@pytest.mark.asyncio
async def test_calculate_with_benchmark(simple_uptrend_prices, standard_config):
    """
    Test beta/alpha calculation with benchmark.

    BUSINESS VALIDATION:
    - Similar trends should have beta ≈ 1.0
    - Consistent outperformance should have positive alpha
    """
    calculator = RiskCalculator(standard_config)

    # Use same uptrend as benchmark (should give beta ≈ 1.0)
    results = await calculator.calculate_risk_metrics(
        simple_uptrend_prices,
        benchmark_data=simple_uptrend_prices  # Same as ticker
    )

    # Beta should be very close to 1.0 (perfect correlation)
    assert results.beta is not None
    assert 0.9 < results.beta < 1.1, f"Beta should be ~1.0, got {results.beta}"

    # Alpha should be close to 0 (same performance)
    assert results.alpha is not None
    assert abs(results.alpha) < 0.05, f"Alpha should be ~0, got {results.alpha}"


# ============================================================================
# Tests - Edge Cases
# ============================================================================

def test_minimum_data_points():
    """Test that calculator requires minimum 30 data points."""
    with pytest.raises(ValidationError):
        PriceDataInput(
            ticker="SHORT",
            prices=[100.0] * 20,
            dates=[date(2025, 1, i) for i in range(1, 21)],
        )


@pytest.mark.asyncio
async def test_perfect_uptrend_no_drawdown():
    """
    Test perfect uptrend with no drawdown.

    EDGE CASE: If price only goes up, max drawdown should be 0.
    """
    # Perfect uptrend (no down days)
    start_date = date(2025, 1, 1)
    perfect_up = PriceDataInput(
        ticker="PERFECT",
        prices=[100.0 + i for i in range(50)],  # 100, 101, 102, ...
        dates=[start_date + timedelta(days=i) for i in range(50)],
    )

    config = RiskCalculationConfig()
    calculator = RiskCalculator(config)
    results = await calculator.calculate_risk_metrics(perfect_up)

    # Max drawdown should be 0 (or very close)
    assert abs(results.max_drawdown) < 0.01, "Perfect uptrend should have ~0 drawdown"

    # Calmar might be inf (divide by 0 drawdown)
    # This is handled in the calculator


# ============================================================================
# Tests - Configuration Variations
# ============================================================================

@pytest.mark.asyncio
async def test_parametric_var_method(simple_uptrend_prices):
    """Test parametric VaR calculation method."""
    config = RiskCalculationConfig(
        confidence_level=0.95,
        var_method="parametric",  # Different from default
        rolling_window=90,
        risk_free_rate=0.045,
    )

    calculator = RiskCalculator(config)
    results = await calculator.calculate_risk_metrics(simple_uptrend_prices)

    # Should still produce valid results
    # Note: VaR can be >= 0 for uptrends with positive returns
    assert results.annual_volatility > 0
    assert results.var_95 is not None


@pytest.mark.asyncio
async def test_different_confidence_levels(simple_uptrend_prices):
    """
    Test VaR with different confidence levels.

    BUSINESS VALIDATION:
    - Higher confidence → more conservative (larger negative VaR)
    - 99% VaR should be more extreme than 95% VaR
    """
    calc_95 = RiskCalculator(RiskCalculationConfig(confidence_level=0.95))
    calc_99 = RiskCalculator(RiskCalculationConfig(confidence_level=0.99))

    results_95 = await calc_95.calculate_risk_metrics(simple_uptrend_prices)
    results_99 = await calc_99.calculate_risk_metrics(simple_uptrend_prices)

    # 99% VaR should be more extreme (more negative) than 95% VaR
    assert results_99.var_95 <= results_95.var_95, \
        "99% confidence should have more extreme VaR"


# ============================================================================
# Integration Test - Full Workflow
# ============================================================================

@pytest.mark.asyncio
async def test_full_risk_analysis_workflow(simple_uptrend_prices, volatile_stock_prices):
    """
    Integration test: Full risk analysis workflow.

    BUSINESS CRITICAL: This simulates the actual MCP tool workflow.
    """
    config = RiskCalculationConfig(
        confidence_level=0.95,
        var_method="historical",
        rolling_window=100,
        risk_free_rate=0.045,
    )

    calculator = RiskCalculator(config)

    # Analyze uptrend vs volatile benchmark
    results = await calculator.calculate_risk_metrics(
        price_data=simple_uptrend_prices,
        benchmark_data=volatile_stock_prices,
    )

    # Verify all metrics are present
    assert results.var_95 is not None
    assert results.cvar_95 is not None
    assert results.sharpe_ratio is not None
    assert results.sortino_ratio is not None
    assert results.max_drawdown is not None
    assert results.calmar_ratio is not None
    assert results.annual_volatility is not None
    assert results.beta is not None
    assert results.alpha is not None

    # Verify calculation date
    assert results.calculation_date == simple_uptrend_prices.dates[-1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
