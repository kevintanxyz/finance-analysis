"""
Unit Tests for Correlation Calculator

Tests correlation and diversification calculations with synthetic data.
No external API calls (yfinance) - all data is mocked.

BUSINESS CRITICAL: Correlation analysis drives diversification decisions.
All formulas must be verified and validated.
"""

import pytest
from datetime import date, timedelta
import numpy as np
from pydantic import ValidationError

from app.models.analysis import (
    PortfolioPriceData,
    CorrelationConfig,
    CorrelationMatrixOutput,
    CovarianceMatrixOutput,
    PortfolioCorrelationOutput,
)
from app.analysis.correlation_calculator import CorrelationCalculator


# ============================================================================
# Fixtures - Synthetic Test Data
# ============================================================================

@pytest.fixture
def perfectly_correlated_data():
    """
    Two assets that move perfectly together (correlation = 1.0).

    EXPECTED RESULTS:
    - Correlation = 1.0 (perfect positive correlation)
    - Diversification score = 0.0 (no diversification benefit)
    - Concentration warning = True
    """
    num_days = 50
    start_date = date(2025, 1, 1)

    dates = [start_date + timedelta(days=i) for i in range(num_days)]

    # Both assets have identical returns
    asset1_prices = [100.0 * (1.01 ** i) for i in range(num_days)]
    asset2_prices = [200.0 * (1.01 ** i) for i in range(num_days)]  # Different scale, same returns

    return PortfolioPriceData(
        tickers=["ASSET1", "ASSET2"],
        dates=dates,
        prices={
            "ASSET1": asset1_prices,
            "ASSET2": asset2_prices,
        },
    )


@pytest.fixture
def negatively_correlated_data():
    """
    Two assets that move opposite to each other (correlation ≈ -1.0).

    EXPECTED RESULTS:
    - Correlation ≈ -1.0 (nearly perfect negative correlation - ideal hedge!)
    - Diversification score ≈ 2.0 (excellent diversification)
    - Concentration warning = False
    """
    num_days = 50
    start_date = date(2025, 1, 1)

    dates = [start_date + timedelta(days=i) for i in range(num_days)]

    # Create truly negatively correlated returns: when one goes up, other goes down
    asset1_prices = [100.0]
    asset2_prices = [200.0]

    for i in range(1, num_days):
        # Asset1 alternates up/down
        change1 = 1.0 * (1 if i % 2 == 0 else -1)
        asset1_prices.append(asset1_prices[-1] + change1)

        # Asset2 alternates opposite to Asset1
        change2 = -1.0 * (1 if i % 2 == 0 else -1)
        asset2_prices.append(asset2_prices[-1] + change2)

    return PortfolioPriceData(
        tickers=["HEDGE1", "HEDGE2"],
        dates=dates,
        prices={
            "HEDGE1": asset1_prices,
            "HEDGE2": asset2_prices,
        },
    )


@pytest.fixture
def uncorrelated_data():
    """
    Three assets with low correlation (independent movements).

    EXPECTED RESULTS:
    - Average correlation ≈ 0 (independent)
    - Diversification score ≈ 1.0 (excellent diversification)
    - Concentration warning = False
    """
    num_days = 100
    start_date = date(2025, 1, 1)
    np.random.seed(42)  # Reproducible

    dates = [start_date + timedelta(days=i) for i in range(num_days)]

    # Three independent random walks
    prices = {}
    for i, ticker in enumerate(["STOCK1", "STOCK2", "STOCK3"]):
        price_series = [100.0]
        for _ in range(num_days - 1):
            # Independent random returns
            ret = np.random.normal(0.001, 0.02)
            price_series.append(price_series[-1] * (1 + ret))
        prices[ticker] = price_series

    return PortfolioPriceData(
        tickers=["STOCK1", "STOCK2", "STOCK3"],
        dates=dates,
        prices=prices,
    )


@pytest.fixture
def standard_correlation_config():
    """Standard correlation calculation configuration."""
    return CorrelationConfig(
        method="pearson",
        rolling_window=None,  # Full period
        min_periods=30,
    )


# ============================================================================
# Tests - Pydantic Model Validation
# ============================================================================

def test_portfolio_price_data_validation():
    """Test PortfolioPriceData validation rules."""
    start_date = date(2025, 1, 1)

    # Valid input
    valid_data = PortfolioPriceData(
        tickers=["AAPL", "NVDA"],
        dates=[start_date + timedelta(days=i) for i in range(40)],
        prices={
            "AAPL": [100.0 + i for i in range(40)],
            "NVDA": [200.0 + i * 2 for i in range(40)],
        },
    )
    assert valid_data.tickers == ["AAPL", "NVDA"]
    assert len(valid_data.dates) == 40

    # Invalid: Too few tickers (need at least 2 for correlation)
    with pytest.raises(ValidationError):
        PortfolioPriceData(
            tickers=["AAPL"],  # Only 1 ticker
            dates=[start_date + timedelta(days=i) for i in range(40)],
            prices={"AAPL": [100.0] * 40},
        )

    # Invalid: Too few data points
    with pytest.raises(ValidationError):
        PortfolioPriceData(
            tickers=["AAPL", "NVDA"],
            dates=[start_date + timedelta(days=i) for i in range(20)],  # Only 20
            prices={
                "AAPL": [100.0] * 20,
                "NVDA": [200.0] * 20,
            },
        )

    # Invalid: Mismatched price series lengths
    with pytest.raises(ValidationError):
        PortfolioPriceData(
            tickers=["AAPL", "NVDA"],
            dates=[start_date + timedelta(days=i) for i in range(40)],
            prices={
                "AAPL": [100.0] * 40,
                "NVDA": [200.0] * 30,  # Different length
            },
        )

    # Invalid: Negative prices
    with pytest.raises(ValidationError):
        PortfolioPriceData(
            tickers=["AAPL", "NVDA"],
            dates=[start_date + timedelta(days=i) for i in range(40)],
            prices={
                "AAPL": [-100.0] * 40,  # Negative
                "NVDA": [200.0] * 40,
            },
        )


# ============================================================================
# Tests - Correlation Calculations
# ============================================================================

@pytest.mark.asyncio
async def test_perfect_positive_correlation(perfectly_correlated_data, standard_correlation_config):
    """
    Test correlation with perfectly correlated assets.

    BUSINESS VALIDATION:
    - Perfect correlation (1.0) = no diversification benefit
    - Should trigger concentration warning
    - Diversification score should be 0
    """
    calculator = CorrelationCalculator(standard_correlation_config)
    results = await calculator.calculate_portfolio_correlation(perfectly_correlated_data)

    # Verify output type
    assert isinstance(results, PortfolioCorrelationOutput)
    assert results.tickers == ["ASSET1", "ASSET2"]

    # Verify perfect correlation
    assert results.correlation_matrix.average_correlation > 0.95, "Should be nearly perfectly correlated"

    # Verify concentration warning
    assert results.concentration_warning is True, "Should warn about concentration"

    # Verify low diversification score
    assert results.diversification_score < 0.1, "Diversification score should be very low"


@pytest.mark.asyncio
async def test_negative_correlation(negatively_correlated_data, standard_correlation_config):
    """
    Test correlation with negatively correlated assets (hedge).

    BUSINESS VALIDATION:
    - Negative correlation = excellent hedge
    - Should NOT trigger concentration warning
    - Diversification score should be high
    """
    calculator = CorrelationCalculator(standard_correlation_config)
    results = await calculator.calculate_portfolio_correlation(negatively_correlated_data)

    # Verify output type
    assert isinstance(results, PortfolioCorrelationOutput)

    # Verify negative correlation
    assert results.correlation_matrix.average_correlation < -0.95, "Should be nearly perfectly negatively correlated"

    # Verify no concentration warning (negative correlation is good!)
    assert results.concentration_warning is False

    # Verify high diversification score
    assert results.diversification_score > 1.9, "Diversification score should be very high for hedge"


@pytest.mark.asyncio
async def test_uncorrelated_assets(uncorrelated_data, standard_correlation_config):
    """
    Test correlation with independent assets.

    BUSINESS VALIDATION:
    - Low correlation = good diversification
    - Should NOT trigger concentration warning
    - Diversification score should be high
    """
    calculator = CorrelationCalculator(standard_correlation_config)
    results = await calculator.calculate_portfolio_correlation(uncorrelated_data)

    # Verify output type
    assert isinstance(results, PortfolioCorrelationOutput)
    assert len(results.tickers) == 3

    # Verify low average correlation (independent)
    assert abs(results.correlation_matrix.average_correlation) < 0.3, "Should have low correlation"

    # Verify no concentration warning
    assert results.concentration_warning is False

    # Verify good diversification score
    assert results.diversification_score > 0.7, "Should have good diversification"


@pytest.mark.asyncio
async def test_correlation_matrix_structure(uncorrelated_data, standard_correlation_config):
    """
    Test that correlation matrix has correct structure.

    BUSINESS VALIDATION:
    - Diagonal should be 1.0 (asset correlates perfectly with itself)
    - Matrix should be symmetric (corr(A,B) = corr(B,A))
    - All values should be in range [-1, 1]
    """
    calculator = CorrelationCalculator(standard_correlation_config)
    results = await calculator.calculate_portfolio_correlation(uncorrelated_data)

    corr_matrix = results.correlation_matrix.correlation_matrix

    # Check diagonal is 1.0
    for ticker in results.tickers:
        assert abs(corr_matrix[ticker][ticker] - 1.0) < 0.01, f"{ticker} should have self-correlation of 1.0"

    # Check symmetry
    for ticker1 in results.tickers:
        for ticker2 in results.tickers:
            assert abs(corr_matrix[ticker1][ticker2] - corr_matrix[ticker2][ticker1]) < 0.01, \
                f"Correlation should be symmetric: {ticker1} vs {ticker2}"

    # Check range
    for ticker1 in results.tickers:
        for ticker2 in results.tickers:
            corr_value = corr_matrix[ticker1][ticker2]
            assert -1.0 <= corr_value <= 1.0, f"Correlation must be in [-1, 1], got {corr_value}"


# ============================================================================
# Tests - Covariance Calculations
# ============================================================================

@pytest.mark.asyncio
async def test_covariance_matrix(uncorrelated_data, standard_correlation_config):
    """
    Test covariance matrix calculation.

    BUSINESS VALIDATION:
    - Covariance matrix should exist
    - Diagonal elements (variance) should be positive
    """
    calculator = CorrelationCalculator(standard_correlation_config)
    results = await calculator.calculate_portfolio_correlation(uncorrelated_data)

    cov_matrix = results.covariance_matrix.covariance_matrix

    # Verify structure
    assert len(cov_matrix) == len(results.tickers)

    # Check diagonal elements (variance) are positive
    for ticker in results.tickers:
        variance = cov_matrix[ticker][ticker]
        assert variance > 0, f"Variance for {ticker} should be positive"


# ============================================================================
# Tests - Diversification Scoring
# ============================================================================

@pytest.mark.asyncio
async def test_diversification_score_bounds():
    """
    Test that diversification score stays within bounds [0, 1].

    Note: Score can exceed 1.0 if average correlation is negative (hedge).
    """
    config = CorrelationConfig()
    calculator = CorrelationCalculator(config)

    # Create data with various correlation levels
    start_date = date(2025, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(50)]

    # Test with perfect correlation (score should be 0)
    perfect_corr_data = PortfolioPriceData(
        tickers=["A", "B"],
        dates=dates,
        prices={
            "A": [100.0 + i for i in range(50)],
            "B": [200.0 + i * 2 for i in range(50)],  # Same pattern, different scale
        },
    )

    results = await calculator.calculate_portfolio_correlation(perfect_corr_data)
    assert 0.0 <= results.diversification_score <= 0.1, "Perfect correlation should give score ≈ 0"


# ============================================================================
# Integration Test - Full Workflow
# ============================================================================

@pytest.mark.asyncio
async def test_full_correlation_workflow(uncorrelated_data):
    """
    Integration test: Full correlation analysis workflow.

    BUSINESS CRITICAL: This simulates the actual MCP tool workflow.
    """
    config = CorrelationConfig(
        method="pearson",
        rolling_window=None,
        min_periods=30,
    )

    calculator = CorrelationCalculator(config)

    # Analyze portfolio correlation
    results = await calculator.calculate_portfolio_correlation(uncorrelated_data)

    # Verify all components are present
    assert results.correlation_matrix is not None
    assert results.covariance_matrix is not None
    assert results.diversification_score is not None
    assert results.concentration_warning is not None

    # Verify metadata
    assert results.calculation_date == uncorrelated_data.dates[-1]
    assert results.tickers == uncorrelated_data.tickers

    # Verify business metrics make sense
    assert 0.0 <= results.diversification_score <= 2.0
    assert isinstance(results.concentration_warning, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
