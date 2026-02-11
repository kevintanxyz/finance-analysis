"""
Risk Analysis Pydantic Models for NUMAN

Adapted from Finance Guru™ risk_inputs.py
These models represent Layer 1 of our 3-layer architecture:
    Layer 1: Pydantic Models (THIS FILE) - Data validation
    Layer 2: Calculator Classes - Business logic
    Layer 3: MCP Tools - Agent integration
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class PriceDataInput(BaseModel):
    """
    Historical price data for risk calculations.

    Ensures price data is valid before risk calculations begin.
    Validates:
        - Prices are positive
        - Dates are chronologically sorted
        - Minimum 30 data points for statistical significance
        - Equal number of prices and dates
    """

    ticker: str = Field(
        ...,
        description="Stock ticker symbol (e.g., 'AAPL', 'ROG.SW', 'SPY')",
        min_length=1,
        max_length=15,
    )

    prices: list[float] = Field(
        ...,
        description="Historical closing prices (minimum 30 days)",
        min_length=30,
    )

    dates: list[date] = Field(
        ...,
        description="Corresponding dates in YYYY-MM-DD format",
        min_length=30,
    )

    @field_validator("prices")
    @classmethod
    def prices_must_be_positive(cls, v: list[float]) -> list[float]:
        """Ensure all prices are positive numbers."""
        if any(price <= 0 for price in v):
            raise ValueError(
                "All prices must be positive. Found zero or negative price."
            )
        return v

    @field_validator("dates")
    @classmethod
    def dates_must_be_sorted(cls, v: list[date]) -> list[date]:
        """Ensure dates are in chronological order."""
        if v != sorted(v):
            raise ValueError(
                "Dates must be in chronological order (earliest to latest)."
            )
        return v

    @model_validator(mode="after")
    def validate_price_date_alignment(self) -> "PriceDataInput":
        """Ensure equal number of prices and dates."""
        if len(self.prices) != len(self.dates):
            raise ValueError(
                f"Length mismatch: {len(self.prices)} prices but {len(self.dates)} dates."
            )
        return self

    @model_validator(mode="after")
    def check_for_duplicate_dates(self) -> "PriceDataInput":
        """Check for duplicate dates."""
        if len(self.dates) != len(set(self.dates)):
            raise ValueError("Duplicate dates found in price data.")
        return self


class RiskCalculationConfig(BaseModel):
    """
    Configuration parameters for risk metric calculations.

    Controls HOW we calculate risk. Different settings for different styles:
    - Day traders: Low rolling_window (30 days), high confidence_level
    - Long-term investors: High rolling_window (252 days), standard confidence
    """

    confidence_level: float = Field(
        default=0.95,
        ge=0.50,
        le=0.99,
        description="Confidence level for VaR calculation (0.95 = 95%)",
    )

    var_method: Literal["historical", "parametric"] = Field(
        default="historical",
        description="VaR calculation method (historical or parametric)",
    )

    rolling_window: int = Field(
        default=252,
        ge=30,
        le=756,
        description="Number of days for rolling calculations (252 = 1 trading year)",
    )

    risk_free_rate: float = Field(
        default=0.045,
        ge=0.0,
        le=0.20,
        description="Annual risk-free rate (0.045 = 4.5%)",
    )


class RiskMetricsOutput(BaseModel):
    """
    Comprehensive risk metrics output.

    Each metric tells you something different:
    - VaR/CVaR: "What can we lose?" (loss magnitude)
    - Sharpe/Sortino: "Are we being paid enough for this risk?"
    - Max Drawdown: "What was the worst decline?"
    - Volatility: "How much does this bounce around?"
    - Beta/Alpha: "How does this relate to the market?"
    """

    # Identification
    ticker: str = Field(..., description="Stock ticker symbol")
    calculation_date: date = Field(..., description="Date of calculation")

    # Value at Risk Metrics
    var_95: float = Field(
        ...,
        description="95% Value at Risk (daily loss threshold)"
    )

    cvar_95: float = Field(
        ...,
        description="95% Conditional VaR (expected loss beyond VaR)"
    )

    # Return-Based Risk Metrics
    sharpe_ratio: float = Field(
        ...,
        description="Sharpe Ratio (excess return per unit of total risk)"
    )

    sortino_ratio: float = Field(
        ...,
        description="Sortino Ratio (excess return per unit of downside risk)"
    )

    # Drawdown Metrics
    max_drawdown: float = Field(
        ...,
        le=0.0,
        description="Maximum peak-to-trough decline (always ≤ 0)"
    )

    calmar_ratio: float = Field(
        ...,
        description="Calmar Ratio (annual return / absolute max drawdown)"
    )

    # Volatility Metrics
    annual_volatility: float = Field(
        ...,
        ge=0.0,
        description="Annualized volatility (standard deviation of returns)"
    )

    # Market Relationship Metrics (Optional)
    beta: float | None = Field(
        default=None,
        description="Beta vs benchmark (sensitivity to market movements)"
    )

    alpha: float | None = Field(
        default=None,
        description="Alpha vs benchmark (excess return above what beta predicts)"
    )

    @field_validator("max_drawdown")
    @classmethod
    def drawdown_must_be_non_positive(cls, v: float) -> float:
        """Ensure max drawdown is negative or zero."""
        if v > 0:
            raise ValueError(
                f"Max drawdown must be ≤ 0 (found {v:.4f}). "
                "Drawdown represents decline and cannot be positive."
            )
        return v


# ============================================================================
# Momentum Analysis Models
# ============================================================================


class MomentumDataInput(BaseModel):
    """
    Price data for momentum indicator calculations.

    Momentum indicators need OHLC (Open, High, Low, Close) data.
    Different indicators use different price components:
    - RSI, MACD, ROC: Close prices only
    - Stochastic, Williams %R: High, Low, Close prices
    """

    ticker: str = Field(
        ...,
        description="Stock ticker symbol",
        min_length=1,
        max_length=15,
    )

    dates: list[date] = Field(
        ...,
        description="Trading dates in chronological order",
        min_length=14,  # Minimum for RSI with 14-day period
    )

    close: list[float] = Field(
        ...,
        description="Closing prices (required for all indicators)",
        min_length=14,
    )

    high: list[float] | None = Field(
        default=None,
        description="High prices (required for Stochastic, Williams %R)",
    )

    low: list[float] | None = Field(
        default=None,
        description="Low prices (required for Stochastic, Williams %R)",
    )

    @field_validator("close", "high", "low")
    @classmethod
    def prices_must_be_positive(cls, v: list[float] | None) -> list[float] | None:
        """Ensure all prices are positive."""
        if v is None:
            return v
        if any(price <= 0 for price in v):
            raise ValueError("All prices must be positive.")
        return v

    @field_validator("dates")
    @classmethod
    def dates_must_be_sorted(cls, v: list[date]) -> list[date]:
        """Ensure dates are chronologically ordered."""
        if v != sorted(v):
            raise ValueError("Dates must be in chronological order.")
        return v

    @model_validator(mode="after")
    def validate_data_alignment(self) -> "MomentumDataInput":
        """Ensure all price arrays have the same length as dates."""
        n_dates = len(self.dates)

        if len(self.close) != n_dates:
            raise ValueError(
                f"Close prices length ({len(self.close)}) must match dates length ({n_dates})"
            )

        if self.high is not None and len(self.high) != n_dates:
            raise ValueError(
                f"High prices length ({len(self.high)}) must match dates length ({n_dates})"
            )

        if self.low is not None and len(self.low) != n_dates:
            raise ValueError(
                f"Low prices length ({len(self.low)}) must match dates length ({n_dates})"
            )

        return self

    @model_validator(mode="after")
    def validate_high_low_relationship(self) -> "MomentumDataInput":
        """Ensure High >= Low for each day."""
        if self.high is not None and self.low is not None:
            for i, (h, l) in enumerate(zip(self.high, self.low)):
                if h < l:
                    raise ValueError(
                        f"High price ({h}) < Low price ({l}) at index {i} (date: {self.dates[i]})"
                    )
        return self


class MomentumConfig(BaseModel):
    """Configuration for momentum indicator calculations."""

    rsi_period: int = Field(default=14, ge=2, le=100)
    macd_fast: int = Field(default=12, ge=5, le=50)
    macd_slow: int = Field(default=26, ge=10, le=100)
    macd_signal: int = Field(default=9, ge=5, le=50)
    stoch_k_period: int = Field(default=14, ge=5, le=100)
    stoch_d_period: int = Field(default=3, ge=2, le=20)
    williams_period: int = Field(default=14, ge=5, le=100)
    roc_period: int = Field(default=12, ge=1, le=100)

    @model_validator(mode="after")
    def validate_macd_periods(self) -> "MomentumConfig":
        """Ensure MACD fast < slow for proper convergence/divergence."""
        if self.macd_fast >= self.macd_slow:
            raise ValueError(
                f"MACD fast period ({self.macd_fast}) must be less than "
                f"slow period ({self.macd_slow})"
            )
        return self


class RSIOutput(BaseModel):
    """Relative Strength Index output (0-100 scale momentum)."""

    ticker: str
    calculation_date: date
    current_rsi: float = Field(..., ge=0.0, le=100.0)
    rsi_signal: Literal["overbought", "oversold", "neutral"]
    period: int


class MACDOutput(BaseModel):
    """MACD (Moving Average Convergence Divergence) output."""

    ticker: str
    calculation_date: date
    macd_line: float
    signal_line: float
    histogram: float
    signal: Literal["bullish", "bearish"]
    fast_period: int
    slow_period: int
    signal_period: int


class StochasticOutput(BaseModel):
    """Stochastic Oscillator output."""

    ticker: str
    calculation_date: date
    k_value: float = Field(..., ge=0.0, le=100.0)
    d_value: float = Field(..., ge=0.0, le=100.0)
    signal: Literal["overbought", "oversold", "neutral"]
    k_period: int
    d_period: int


class WilliamsROutput(BaseModel):
    """Williams %R output (-100 to 0 scale)."""

    ticker: str
    calculation_date: date
    williams_r: float = Field(..., ge=-100.0, le=0.0)
    signal: Literal["overbought", "oversold", "neutral"]
    period: int


class ROCOutput(BaseModel):
    """Rate of Change output (percentage momentum)."""

    ticker: str
    calculation_date: date
    roc: float
    signal: Literal["bullish", "bearish", "neutral"]
    period: int


class AllMomentumOutput(BaseModel):
    """Combined output for all momentum indicators."""

    ticker: str
    calculation_date: date
    rsi: RSIOutput
    macd: MACDOutput
    stochastic: StochasticOutput
    williams_r: WilliamsROutput
    roc: ROCOutput


__all__ = [
    "PriceDataInput",
    "RiskCalculationConfig",
    "RiskMetricsOutput",
    "MomentumDataInput",
    "MomentumConfig",
    "RSIOutput",
    "MACDOutput",
    "StochasticOutput",
    "WilliamsROutput",
    "ROCOutput",
    "AllMomentumOutput",
]
