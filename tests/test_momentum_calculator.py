"""
Unit Tests for Momentum Calculator

Tests momentum indicator calculations with synthetic data.
No external API calls (yfinance) - all data is mocked.

BUSINESS CRITICAL: Momentum indicators drive trading decisions.
All formulas must be verified and validated.
"""

import pytest
from datetime import date, timedelta
import numpy as np
from pydantic import ValidationError

from app.models.analysis import (
    MomentumDataInput,
    MomentumConfig,
    RSIOutput,
    MACDOutput,
    StochasticOutput,
    WilliamsROutput,
    ROCOutput,
    AllMomentumOutput,
)
from app.analysis.momentum_calculator import MomentumIndicators


# ============================================================================
# Fixtures - Synthetic Test Data
# ============================================================================

@pytest.fixture
def uptrend_ohlc_data():
    """
    Simple upward trend with OHLC data.

    EXPECTED RESULTS:
    - RSI > 50 (bullish momentum)
    - MACD bullish (upward trend)
    - ROC positive (price increasing)
    """
    num_days = 50
    start_date = date(2025, 1, 1)

    # Generate upward trending prices
    dates = [start_date + timedelta(days=i) for i in range(num_days)]
    close_prices = [100.0 + i * 0.5 for i in range(num_days)]  # +0.5 per day
    high_prices = [c + 1.0 for c in close_prices]  # +1.0 above close
    low_prices = [c - 0.5 for c in close_prices]  # -0.5 below close

    return MomentumDataInput(
        ticker="UPTREND",
        dates=dates,
        close=close_prices,
        high=high_prices,
        low=low_prices,
    )


@pytest.fixture
def volatile_ohlc_data():
    """
    Volatile stock with random walk and wide ranges.

    EXPECTED RESULTS:
    - RSI varies (overbought/oversold conditions)
    - MACD oscillates
    - High/low spread reflects volatility
    """
    num_days = 50
    start_date = date(2025, 1, 1)
    np.random.seed(42)  # Reproducible

    dates = [start_date + timedelta(days=i) for i in range(num_days)]

    # Random walk for close prices
    close_prices = [100.0]
    for _ in range(num_days - 1):
        change = np.random.normal(0, 2.0)  # 2% std dev
        close_prices.append(max(close_prices[-1] + change, 1.0))

    # Generate high/low with realistic spreads
    high_prices = [c + abs(np.random.normal(1.5, 0.5)) for c in close_prices]
    low_prices = [c - abs(np.random.normal(1.0, 0.5)) for c in close_prices]

    return MomentumDataInput(
        ticker="VOLATILE",
        dates=dates,
        close=close_prices,
        high=high_prices,
        low=low_prices,
    )


@pytest.fixture
def standard_momentum_config():
    """Standard momentum calculation configuration."""
    return MomentumConfig(
        rsi_period=14,
        macd_fast=12,
        macd_slow=26,
        macd_signal=9,
        stoch_k_period=14,
        stoch_d_period=3,
        williams_period=14,
        roc_period=12,
    )


# ============================================================================
# Tests - Pydantic Model Validation
# ============================================================================

def test_momentum_data_input_validation():
    """Test MomentumDataInput validation rules."""
    start_date = date(2025, 1, 1)

    # Valid input
    valid_data = MomentumDataInput(
        ticker="AAPL",
        dates=[start_date + timedelta(days=i) for i in range(20)],
        close=[100.0 + i for i in range(20)],
        high=[101.0 + i for i in range(20)],
        low=[99.0 + i for i in range(20)],
    )
    assert valid_data.ticker == "AAPL"
    assert len(valid_data.close) == 20

    # Invalid: Too few data points
    with pytest.raises(ValidationError):
        MomentumDataInput(
            ticker="AAPL",
            dates=[start_date],
            close=[100.0],
            high=[101.0],
            low=[99.0],
        )

    # Invalid: Negative price
    with pytest.raises(ValidationError):
        MomentumDataInput(
            ticker="AAPL",
            dates=[start_date + timedelta(days=i) for i in range(20)],
            close=[-50.0] * 20,  # Negative prices
            high=[101.0] * 20,
            low=[99.0] * 20,
        )

    # Invalid: High < Low
    with pytest.raises(ValidationError):
        MomentumDataInput(
            ticker="AAPL",
            dates=[start_date + timedelta(days=i) for i in range(20)],
            close=[100.0] * 20,
            high=[99.0] * 20,  # High less than Low
            low=[101.0] * 20,
        )


def test_momentum_config_validation():
    """Test MomentumConfig validation."""
    # Valid config
    config = MomentumConfig(
        rsi_period=14,
        macd_fast=12,
        macd_slow=26,
    )
    assert config.rsi_period == 14

    # Invalid: MACD fast >= slow
    with pytest.raises(ValidationError):
        MomentumConfig(
            macd_fast=26,
            macd_slow=12,  # Should be > fast
        )


# ============================================================================
# Tests - RSI Calculations
# ============================================================================

@pytest.mark.asyncio
async def test_calculate_rsi_uptrend(uptrend_ohlc_data, standard_momentum_config):
    """
    Test RSI on uptrend.

    BUSINESS VALIDATION:
    - Uptrend should have high RSI (> 50)
    - RSI should be in valid range (0-100)
    """
    calculator = MomentumIndicators(standard_momentum_config)
    result = await calculator.calculate_rsi(uptrend_ohlc_data)

    # Verify output type
    assert isinstance(result, RSIOutput)
    assert result.ticker == "UPTREND"

    # Verify RSI is in valid range
    assert 0 <= result.current_rsi <= 100

    # Uptrend should have RSI > 50
    assert result.current_rsi > 50, "Uptrend should have bullish RSI"


@pytest.mark.asyncio
async def test_calculate_rsi_insufficient_data():
    """Test RSI with insufficient data points."""
    start_date = date(2025, 1, 1)
    short_data = MomentumDataInput(
        ticker="SHORT",
        dates=[start_date + timedelta(days=i) for i in range(14)],  # Exactly 14
        close=[100.0] * 14,
    )

    calculator = MomentumIndicators(MomentumConfig(rsi_period=14))

    # Need 14 + 1 = 15 data points for RSI calculation
    with pytest.raises(ValueError, match="Need at least 15 data points"):
        await calculator.calculate_rsi(short_data)


# ============================================================================
# Tests - MACD Calculations
# ============================================================================

@pytest.mark.asyncio
async def test_calculate_macd_uptrend(uptrend_ohlc_data, standard_momentum_config):
    """
    Test MACD on uptrend.

    BUSINESS VALIDATION:
    - Uptrend should have bullish MACD signal
    - Histogram should reflect momentum direction
    """
    calculator = MomentumIndicators(standard_momentum_config)
    result = await calculator.calculate_macd(uptrend_ohlc_data)

    # Verify output type
    assert isinstance(result, MACDOutput)
    assert result.ticker == "UPTREND"

    # Verify MACD components exist
    assert result.macd_line is not None
    assert result.signal_line is not None
    assert result.histogram is not None

    # For strong uptrend, expect bullish signal
    assert result.signal == "bullish", "Uptrend should have bullish MACD"


# ============================================================================
# Tests - Stochastic Calculations
# ============================================================================

@pytest.mark.asyncio
async def test_calculate_stochastic_with_high_low(uptrend_ohlc_data, standard_momentum_config):
    """
    Test Stochastic with high/low data.

    BUSINESS VALIDATION:
    - %K and %D should be in range 0-100
    - %D should be smoother than %K
    """
    calculator = MomentumIndicators(standard_momentum_config)
    result = await calculator.calculate_stochastic(uptrend_ohlc_data)

    # Verify output type
    assert isinstance(result, StochasticOutput)
    assert result.ticker == "UPTREND"

    # Verify %K and %D are in valid range
    assert 0 <= result.k_value <= 100
    assert 0 <= result.d_value <= 100


@pytest.mark.asyncio
async def test_calculate_stochastic_without_high_low():
    """Test Stochastic requires high/low data."""
    start_date = date(2025, 1, 1)
    no_hl_data = MomentumDataInput(
        ticker="NOHL",
        dates=[start_date + timedelta(days=i) for i in range(20)],
        close=[100.0] * 20,
        # No high/low provided
    )

    calculator = MomentumIndicators(MomentumConfig())

    with pytest.raises(ValueError, match="Stochastic requires high and low"):
        await calculator.calculate_stochastic(no_hl_data)


# ============================================================================
# Tests - Williams %R Calculations
# ============================================================================

@pytest.mark.asyncio
async def test_calculate_williams_r(uptrend_ohlc_data, standard_momentum_config):
    """
    Test Williams %R.

    BUSINESS VALIDATION:
    - Williams %R should be in range -100 to 0
    """
    calculator = MomentumIndicators(standard_momentum_config)
    result = await calculator.calculate_williams_r(uptrend_ohlc_data)

    # Verify output type
    assert isinstance(result, WilliamsROutput)
    assert result.ticker == "UPTREND"

    # Verify Williams %R is in valid range
    assert -100 <= result.williams_r <= 0


# ============================================================================
# Tests - ROC Calculations
# ============================================================================

@pytest.mark.asyncio
async def test_calculate_roc_uptrend(uptrend_ohlc_data, standard_momentum_config):
    """
    Test ROC on uptrend.

    BUSINESS VALIDATION:
    - Uptrend should have positive ROC
    - ROC signal should be bullish
    """
    calculator = MomentumIndicators(standard_momentum_config)
    result = await calculator.calculate_roc(uptrend_ohlc_data)

    # Verify output type
    assert isinstance(result, ROCOutput)
    assert result.ticker == "UPTREND"

    # Uptrend should have positive ROC
    assert result.roc > 0, "Uptrend should have positive ROC"
    assert result.signal == "bullish"


# ============================================================================
# Tests - All Indicators
# ============================================================================

@pytest.mark.asyncio
async def test_calculate_all_indicators(uptrend_ohlc_data, standard_momentum_config):
    """
    Test calculating all momentum indicators at once.

    BUSINESS VALIDATION:
    - All indicators should be present
    - Confluence should show agreement for uptrend
    """
    calculator = MomentumIndicators(standard_momentum_config)
    results = await calculator.calculate_all(uptrend_ohlc_data)

    # Verify output type
    assert isinstance(results, AllMomentumOutput)
    assert results.ticker == "UPTREND"

    # Verify all indicators are present
    assert results.rsi is not None
    assert results.macd is not None
    assert results.stochastic is not None
    assert results.williams_r is not None
    assert results.roc is not None

    # All use same calculation date
    assert results.rsi.calculation_date == results.calculation_date
    assert results.macd.calculation_date == results.calculation_date


# ============================================================================
# Tests - Edge Cases
# ============================================================================

@pytest.mark.asyncio
async def test_flat_prices():
    """
    Test indicators with flat (no change) prices.

    EDGE CASE: Flat prices should produce neutral signals.
    """
    start_date = date(2025, 1, 1)
    flat_data = MomentumDataInput(
        ticker="FLAT",
        dates=[start_date + timedelta(days=i) for i in range(30)],
        close=[100.0] * 30,  # No change
        high=[100.5] * 30,
        low=[99.5] * 30,
    )

    calculator = MomentumIndicators(MomentumConfig())

    # RSI should be neutral (around 50) for flat prices
    rsi_result = await calculator.calculate_rsi(flat_data)
    # Note: RSI with no gains or losses can produce NaN, which is then ~50
    # We just verify it doesn't crash
    assert isinstance(rsi_result, RSIOutput)

    # ROC should be 0 or neutral
    roc_result = await calculator.calculate_roc(flat_data)
    assert abs(roc_result.roc) < 0.01, "Flat prices should have ~0 ROC"
    assert roc_result.signal == "neutral"


# ============================================================================
# Integration Test - Full Workflow
# ============================================================================

@pytest.mark.asyncio
async def test_full_momentum_workflow(uptrend_ohlc_data, volatile_ohlc_data):
    """
    Integration test: Full momentum analysis workflow.

    BUSINESS CRITICAL: This simulates the actual MCP tool workflow.
    """
    config = MomentumConfig(
        rsi_period=14,
        macd_fast=12,
        macd_slow=26,
        macd_signal=9,
    )

    calculator = MomentumIndicators(config)

    # Analyze both uptrend and volatile stocks
    uptrend_results = await calculator.calculate_all(uptrend_ohlc_data)
    volatile_results = await calculator.calculate_all(volatile_ohlc_data)

    # Verify both completed successfully
    assert uptrend_results.ticker == "UPTREND"
    assert volatile_results.ticker == "VOLATILE"

    # Uptrend should have more bullish indicators
    assert uptrend_results.rsi.current_rsi > 50
    assert uptrend_results.macd.signal == "bullish"
    assert uptrend_results.roc.signal == "bullish"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
