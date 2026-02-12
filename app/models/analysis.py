"""
Risk Analysis Pydantic Models for WealthPoint

Adapted from Finance Guru™ risk_inputs.py
These models represent Layer 1 of our 3-layer architecture:
    Layer 1: Pydantic Models (THIS FILE) - Data validation
    Layer 2: Calculator Classes - Business logic
    Layer 3: MCP Tools - Agent integration
"""

from __future__ import annotations

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


# ============================================================================
# Correlation Analysis Models
# ============================================================================


class PortfolioPriceData(BaseModel):
    """
    Historical price data for multiple assets (correlation analysis).

    For correlation, we need synchronized price data across all assets.
    """

    tickers: list[str] = Field(
        ...,
        min_length=2,
        description="Asset ticker symbols (minimum 2 for correlation)",
    )

    dates: list[date] = Field(
        ...,
        min_length=30,
        description="Trading dates (must be same for all assets)",
    )

    prices: dict[str, list[float]] = Field(
        ...,
        description="Price series for each ticker",
    )

    @field_validator("prices")
    @classmethod
    def validate_prices_structure(cls, v: dict[str, list[float]], info) -> dict[str, list[float]]:
        """Validate that all price series have same length and positive values."""
        if not v:
            raise ValueError("Prices dictionary cannot be empty")

        # Check all prices are positive
        for ticker, price_list in v.items():
            if any(p <= 0 for p in price_list):
                raise ValueError(f"All prices for {ticker} must be positive")

        # Check all series have same length
        lengths = [len(price_list) for price_list in v.values()]
        if len(set(lengths)) > 1:
            raise ValueError(
                f"All price series must have same length. Found: {dict(zip(v.keys(), lengths))}"
            )

        # Check tickers match
        tickers_in_data = info.data.get("tickers", [])
        if tickers_in_data:
            for ticker in tickers_in_data:
                if ticker not in v:
                    raise ValueError(f"Ticker {ticker} listed but no price data provided")

        return v


class CorrelationConfig(BaseModel):
    """Configuration for correlation analysis."""

    method: Literal["pearson", "spearman"] = Field(
        default="pearson",
        description="Correlation method (pearson for linear)",
    )

    rolling_window: int | None = Field(
        default=None,
        ge=20,
        le=252,
        description="Rolling window for time-varying correlation (None = full period)",
    )

    min_periods: int = Field(
        default=30,
        ge=10,
        description="Minimum periods required for rolling correlation",
    )


class CorrelationMatrixOutput(BaseModel):
    """Correlation matrix results showing pairwise correlations."""

    tickers: list[str]
    calculation_date: date
    correlation_matrix: dict[str, dict[str, float]]
    average_correlation: float = Field(..., ge=-1.0, le=1.0)


class CovarianceMatrixOutput(BaseModel):
    """Covariance matrix results (used for portfolio optimization)."""

    tickers: list[str]
    calculation_date: date
    covariance_matrix: dict[str, dict[str, float]]


class PortfolioCorrelationOutput(BaseModel):
    """Complete correlation analysis output for portfolio diversification."""

    calculation_date: date
    tickers: list[str]
    correlation_matrix: CorrelationMatrixOutput
    covariance_matrix: CovarianceMatrixOutput
    diversification_score: float = Field(
        ...,
        ge=0.0,
        le=2.0,  # Can exceed 1.0 for hedges (negative correlation)
        description="Diversification score (0=none, 1=perfect, >1=hedge)",
    )
    concentration_warning: bool


# ============================================================================
# Options Pricing Models (Black-Scholes + Greeks)
# ============================================================================


class BlackScholesInput(BaseModel):
    """
    Inputs for Black-Scholes option pricing model.

    Black-Scholes is the standard model for European options pricing.
    Calculates theoretical fair value and Greeks (sensitivities).

    ASSUMPTIONS:
    - European exercise (only at expiry)
    - Constant volatility and interest rate
    - Log-normal price distribution
    - No dividends during option life (or constant dividend yield)
    """

    spot_price: float = Field(
        ..., gt=0.0, description="Current stock price"
    )
    strike: float = Field(
        ..., gt=0.0, description="Option strike price"
    )
    time_to_expiry: float = Field(
        ...,
        gt=0.0,
        le=10.0,
        description="Time to expiry in years (e.g., 0.25 = 3 months)",
    )
    volatility: float = Field(
        ...,
        ge=0.01,
        le=3.0,
        description="Annual volatility as decimal (e.g., 0.35 = 35%)",
    )
    risk_free_rate: float = Field(
        default=0.045,
        ge=0.0,
        le=0.20,
        description="Annual risk-free rate (default: 4.5%)",
    )
    dividend_yield: float = Field(
        default=0.0,
        ge=0.0,
        le=0.20,
        description="Annual dividend yield (default: 0%)",
    )
    option_type: Literal["call", "put"] = Field(
        ..., description="Option type: call or put"
    )

    @field_validator("volatility")
    @classmethod
    def validate_volatility_reasonable(cls, v: float) -> float:
        """Warn if volatility is extreme."""
        if v > 1.5:
            import warnings

            warnings.warn(
                f"Volatility of {v:.0%} is very high (>150%). "
                "Verify this is correct for your asset."
            )
        return v


class GreeksOutput(BaseModel):
    """
    Option price and Greeks (sensitivities) output.

    Greeks measure how option price changes with market variables:
    - Delta: Price sensitivity to $1 stock move
    - Gamma: Rate of Delta change (second derivative)
    - Theta: Time decay ($ lost per day)
    - Vega: Volatility sensitivity ($ change per 1% volatility change)
    - Rho: Interest rate sensitivity

    INTERPRETATION:
    - Delta 0.50 means: $1 stock up → $0.50 option up
    - Gamma 0.05 means: $1 stock up → Delta increases by 0.05
    - Theta -0.10 means: Lose $0.10 per day from time decay
    - Vega 0.20 means: 1% volatility up → $0.20 option up
    """

    # Identification
    ticker: str = Field(..., description="Underlying asset ticker")
    option_type: Literal["call", "put"] = Field(..., description="Option type")
    calculation_date: date = Field(..., description="Date of calculation")

    # Pricing
    option_price: float = Field(
        ..., ge=0.0, description="Theoretical option price"
    )
    intrinsic_value: float = Field(
        ..., ge=0.0, description="Intrinsic value (immediate exercise value)"
    )
    time_value: float = Field(
        ..., ge=0.0, description="Time value (option_price - intrinsic_value)"
    )

    # Greeks (First Order)
    delta: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Delta: Price sensitivity to $1 stock move",
    )
    gamma: float = Field(
        ..., ge=0.0, description="Gamma: Rate of Delta change (always positive)"
    )
    theta: float = Field(
        ..., le=0.0, description="Theta: Daily time decay (always negative)"
    )
    vega: float = Field(
        ..., ge=0.0, description="Vega: Sensitivity to 1% volatility change"
    )
    rho: float = Field(
        ..., description="Rho: Sensitivity to 1% interest rate change"
    )

    # Moneyness
    moneyness: Literal["ITM", "ATM", "OTM"] = Field(
        ..., description="Moneyness: In/At/Out of the money"
    )

    # Input parameters (for reference)
    spot_price: float = Field(..., description="Spot price used")
    strike: float = Field(..., description="Strike price")
    time_to_expiry: float = Field(..., description="Time to expiry (years)")
    volatility: float = Field(..., description="Volatility used")


# ============================================================================
# Portfolio Optimization Models (Phase 2.5)
# ============================================================================


class PortfolioDataInput(BaseModel):
    """
    Historical price data for portfolio optimization.

    WHAT: Multi-asset price history for optimization calculations
    WHY: Enables calculation of expected returns, volatilities, and correlations
    VALIDATES:
        - At least 2 assets (need multiple assets for portfolio optimization)
        - Minimum 30 days for reliable estimates (252 recommended)
        - All price series have same length (synchronized data)
        - Prices are positive

    EDUCATIONAL NOTE:
    Portfolio optimization requires historical data to estimate:
    1. Expected returns (average future returns)
    2. Volatilities (risk of each asset)
    3. Correlations (how assets move together)

    The quality of optimization depends on data quality and length.
    Generally, 1-3 years of daily data is ideal for retail portfolios.
    """

    tickers: list[str] = Field(
        ...,
        min_length=2,
        description="Asset ticker symbols (minimum 2 for portfolio optimization)",
    )

    dates: list[date] = Field(
        ...,
        min_length=30,
        description="Trading dates (minimum 30 days, 252 recommended for reliable estimates)",
    )

    prices: dict[str, list[float]] = Field(
        ..., description="Price history for each ticker {ticker: [prices]}"
    )

    expected_returns: dict[str, float] | None = Field(
        default=None,
        description="Optional expected annual returns per asset (if None, estimated from history)",
    )

    @field_validator("tickers")
    @classmethod
    def tickers_must_be_uppercase(cls, v: list[str]) -> list[str]:
        """Ensure ticker symbols are uppercase and valid format."""
        for ticker in v:
            if ticker != ticker.upper():
                raise ValueError(f"Ticker '{ticker}' must be uppercase (e.g., 'TSLA')")
            if not ticker.replace(".", "").replace("-", "").replace("_", "").isalnum():
                raise ValueError(
                    f"Ticker '{ticker}' must contain only letters, numbers, dots, hyphens, and underscores"
                )
        return v

    @field_validator("prices")
    @classmethod
    def validate_prices_structure(
        cls, v: dict[str, list[float]], info
    ) -> dict[str, list[float]]:
        """Validate that all price series have same length and positive values."""
        if not v:
            raise ValueError("Prices dictionary cannot be empty")

        # Check all prices are positive
        for ticker, price_list in v.items():
            if any(p <= 0 for p in price_list):
                raise ValueError(f"All prices for {ticker} must be positive")

        # Check all series have same length
        lengths = [len(price_list) for price_list in v.values()]
        if len(set(lengths)) > 1:
            raise ValueError(
                f"All price series must have same length. Found: {dict(zip(v.keys(), lengths))}"
            )

        # Check minimum length (30 days minimum, 252 recommended)
        if lengths[0] < 30:
            raise ValueError(
                f"Price series must have at least 30 days. Found: {lengths[0]} days. "
                f"Note: 252 days (1 year) recommended for reliable optimization."
            )

        # Check tickers match
        tickers_in_data = info.data.get("tickers", [])
        if tickers_in_data:
            for ticker in tickers_in_data:
                if ticker not in v:
                    raise ValueError(
                        f"Ticker {ticker} listed but no price data provided"
                    )

        return v

    @field_validator("expected_returns")
    @classmethod
    def validate_expected_returns(
        cls, v: dict[str, float] | None, info
    ) -> dict[str, float] | None:
        """Validate expected returns if provided."""
        if v is None:
            return v

        # Check all returns are reasonable
        for ticker, ret in v.items():
            if ret < -0.90:
                raise ValueError(
                    f"Expected return for {ticker} is {ret:.1%}. "
                    "Returns below -90% are unrealistic (total loss)."
                )
            if ret > 2.0:
                raise ValueError(
                    f"Expected return for {ticker} is {ret:.1%}. "
                    "Returns above 200% per year are extremely aggressive. Verify this forecast."
                )

        # Check tickers match
        tickers_in_data = info.data.get("tickers", [])
        if tickers_in_data:
            for ticker in tickers_in_data:
                if ticker not in v:
                    raise ValueError(
                        f"Expected return provided but missing ticker {ticker}"
                    )

        return v


class OptimizationConfig(BaseModel):
    """
    Configuration for portfolio optimization.

    WHAT: Settings that control the optimization process
    WHY: Different optimization methods suit different investment goals

    EDUCATIONAL NOTE:
    Five optimization methods available:

    1. **Mean-Variance** (Markowitz): Balances return vs risk
       - Best for: Investors with specific return targets
       - Requires: Return forecasts (uncertain!)

    2. **Risk Parity**: Each asset contributes equally to portfolio risk
       - Best for: "All-weather" portfolios, no return forecasts needed
       - Used by: Bridgewater Associates (Ray Dalio)

    3. **Minimum Variance**: Lowest risk allocation
       - Best for: Conservative investors, capital preservation
       - Ignores returns, focuses purely on risk reduction

    4. **Maximum Sharpe**: Best risk-adjusted return
       - Best for: Aggressive growth with risk awareness
       - Most popular among quantitative investors

    5. **Black-Litterman**: Market equilibrium + investor views
       - Best for: Incorporating specific investment opinions
       - Handles uncertainty better than pure Markowitz
    """

    method: Literal[
        "mean_variance", "risk_parity", "min_variance", "max_sharpe", "black_litterman"
    ] = Field(default="max_sharpe", description="Optimization method to use")

    risk_free_rate: float = Field(
        default=0.045,
        ge=0.0,
        le=0.20,
        description="Annual risk-free rate for Sharpe calculation (0.045 = 4.5%)",
    )

    target_return: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Target annual return for mean-variance optimization (None = unconstrained)",
    )

    allow_short: bool = Field(
        default=False,
        description="Allow short positions (False = long-only, appropriate for most retail investors)",
    )

    position_limits: tuple[float, float] = Field(
        default=(0.0, 1.0),
        description="Min and max position size per asset (0.0, 1.0) = 0-100%",
    )

    views: dict[str, float] | None = Field(
        default=None,
        description="Investor views on expected returns for Black-Litterman (ticker: annual_return)",
    )

    @field_validator("position_limits")
    @classmethod
    def validate_position_limits(cls, v: tuple[float, float]) -> tuple[float, float]:
        """Validate position limit constraints."""
        min_pos, max_pos = v

        if min_pos >= max_pos:
            raise ValueError(
                f"Minimum position ({min_pos:.1%}) must be less than maximum ({max_pos:.1%})"
            )

        if max_pos > 1.0:
            raise ValueError(
                f"Maximum position {max_pos:.1%} exceeds 100%. "
                "Cannot allocate more than 100% to a single asset."
            )

        if min_pos < -1.0:
            raise ValueError(
                f"Minimum position {min_pos:.1%} below -100%. "
                "Cannot short more than 100% of portfolio value."
            )

        return v

    @model_validator(mode="after")
    def validate_method_specific_requirements(self) -> "OptimizationConfig":
        """Validate that required parameters are present for each method."""
        if self.method == "black_litterman" and self.views is None:
            raise ValueError(
                "Black-Litterman optimization requires 'views' parameter. "
                "Specify expected returns for assets: views={'TSLA': 0.15, 'PLTR': 0.20}"
            )

        return self


class OptimizationOutput(BaseModel):
    """
    Results from portfolio optimization.

    WHAT: Optimal portfolio weights and expected metrics
    WHY: Provides actionable allocation for capital deployment

    EDUCATIONAL NOTE:
    The optimal weights tell you how to allocate your capital.
    For a $100k portfolio with weights:
        {"AAPL": 0.25, "NVDA": 0.30, "TSLA": 0.20, "SPY": 0.25}

    Your allocation would be:
        - AAPL: $25,000 (25%)
        - NVDA: $30,000 (30%)
        - TSLA: $20,000 (20%)
        - SPY:  $25,000 (25%)
    """

    tickers: list[str] = Field(..., description="Asset ticker symbols")

    method: str = Field(..., description="Optimization method used")

    optimal_weights: dict[str, float] = Field(
        ..., description="Optimal allocation per asset (must sum to 1.0)"
    )

    expected_return: float = Field(
        ..., description="Expected annual portfolio return"
    )

    expected_volatility: float = Field(
        ..., ge=0.0, description="Expected annual portfolio volatility (standard deviation)"
    )

    sharpe_ratio: float = Field(
        ..., description="Expected Sharpe ratio (return per unit of risk)"
    )

    diversification_ratio: float = Field(
        ..., ge=1.0, description="Diversification ratio (portfolio_risk / weighted_avg_risk)"
    )

    @field_validator("optimal_weights")
    @classmethod
    def weights_must_sum_to_one(cls, v: dict[str, float]) -> dict[str, float]:
        """Ensure weights sum to 1.0 (fully invested)."""
        weight_sum = sum(v.values())
        if abs(weight_sum - 1.0) > 0.001:
            raise ValueError(
                f"Weights must sum to 1.0 (fully invested). Found sum = {weight_sum:.6f}"
            )
        return v

    @field_validator("diversification_ratio")
    @classmethod
    def diversification_ratio_must_be_valid(cls, v: float) -> float:
        """Validate diversification ratio is >= 1.0."""
        if v < 1.0:
            raise ValueError(
                f"Diversification ratio {v:.2f} is less than 1.0. "
                "This indicates a calculation error (ratio must be >= 1.0)."
            )
        return v


class EfficientFrontierOutput(BaseModel):
    """
    Efficient frontier data for visualization.

    WHAT: Collection of optimal portfolios across risk levels
    WHY: Shows risk-return tradeoff, helps choose risk tolerance

    EDUCATIONAL NOTE:
    The efficient frontier is a curve showing the best possible portfolios.
    Every point on the curve represents a portfolio with the highest return
    for its risk level (or lowest risk for its return level).

    Portfolios BELOW the curve are sub-optimal (same risk, less return).
    Portfolios ABOVE the curve are impossible (too good to be true!).

    The optimal portfolio for most investors is where the line from the
    risk-free rate is tangent to the frontier (Maximum Sharpe Ratio point).
    """

    returns: list[float] = Field(
        ...,
        min_length=10,
        description="Expected annual returns for frontier portfolios",
    )

    volatilities: list[float] = Field(
        ...,
        min_length=10,
        description="Expected annual volatilities for frontier portfolios",
    )

    sharpe_ratios: list[float] = Field(
        ..., min_length=10, description="Sharpe ratios for frontier portfolios"
    )

    optimal_portfolio_index: int = Field(
        ...,
        ge=0,
        description="Index of maximum Sharpe ratio portfolio in the frontier",
    )

    @model_validator(mode="after")
    def validate_frontier_consistency(self) -> "EfficientFrontierOutput":
        """Ensure all frontier arrays have same length."""
        n_returns = len(self.returns)
        n_vols = len(self.volatilities)
        n_sharpes = len(self.sharpe_ratios)

        if not (n_returns == n_vols == n_sharpes):
            raise ValueError(
                f"Frontier arrays must have same length. "
                f"Found: returns={n_returns}, volatilities={n_vols}, sharpe_ratios={n_sharpes}"
            )

        if self.optimal_portfolio_index >= n_returns:
            raise ValueError(
                f"Optimal portfolio index {self.optimal_portfolio_index} "
                f"exceeds frontier length {n_returns}"
            )

        return self


# ═══════════════════════════════════════════════════════════════════════════
# COMPLIANCE CHECKING MODELS
# ═══════════════════════════════════════════════════════════════════════════


class ComplianceConfig(BaseModel):
    """
    Configuration for portfolio compliance checks.

    Defines limits and thresholds for concentration risk, diversification,
    and other regulatory or policy constraints.
    """

    max_single_position_pct: float = Field(
        default=20.0,
        ge=0.0,
        le=100.0,
        description="Maximum % of portfolio in a single position (default 20%)"
    )

    max_asset_class_pct: float = Field(
        default=70.0,
        ge=0.0,
        le=100.0,
        description="Maximum % of portfolio in a single asset class (default 70%)"
    )

    max_currency_pct: float = Field(
        default=80.0,
        ge=0.0,
        le=100.0,
        description="Maximum % of portfolio in a single currency (default 80%)"
    )

    min_positions_count: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Minimum number of positions for diversification (default 5)"
    )

    min_cash_pct: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Minimum cash allocation % (default 0%)"
    )

    max_cash_pct: float = Field(
        default=25.0,
        ge=0.0,
        le=100.0,
        description="Maximum cash allocation % (default 25%)"
    )

    @model_validator(mode="after")
    def validate_cash_limits(self) -> "ComplianceConfig":
        """Ensure min_cash <= max_cash."""
        if self.min_cash_pct > self.max_cash_pct:
            raise ValueError(
                f"Minimum cash ({self.min_cash_pct}%) must be <= maximum cash ({self.max_cash_pct}%)"
            )
        return self


class ComplianceViolation(BaseModel):
    """A single compliance violation or warning."""

    severity: Literal["critical", "high", "medium", "low"] = Field(
        ..., description="Severity level of the violation"
    )

    rule_id: str = Field(
        ..., description="Unique identifier for the rule (e.g., 'POS-01', 'CASH-01')"
    )

    rule_name: str = Field(
        ..., description="Human-readable rule name"
    )

    message: str = Field(
        ..., description="Detailed description of the violation"
    )

    current_value: float = Field(
        ..., description="Current value that violates the rule"
    )

    limit_value: float = Field(
        ..., description="The limit that was exceeded"
    )

    affected_positions: list[str] = Field(
        default_factory=list,
        description="List of position names or identifiers affected by this violation"
    )

    recommendation: str = Field(
        ..., description="Suggested action to remediate the violation"
    )


class ComplianceCheckOutput(BaseModel):
    """
    Complete compliance check results.

    Includes all violations, warnings, and a summary of compliance status.
    """

    timestamp: str = Field(
        ..., description="ISO timestamp when compliance check was performed"
    )

    portfolio_value_chf: float = Field(
        ..., description="Total portfolio value in CHF at time of check"
    )

    total_positions: int = Field(
        ..., description="Total number of positions in portfolio"
    )

    is_compliant: bool = Field(
        ..., description="Whether portfolio passes all critical and high-severity rules"
    )

    violations: list[ComplianceViolation] = Field(
        default_factory=list, description="List of all violations found"
    )

    critical_count: int = Field(
        default=0, description="Number of critical violations"
    )

    high_count: int = Field(
        default=0, description="Number of high-severity violations"
    )

    medium_count: int = Field(
        default=0, description="Number of medium-severity violations"
    )

    low_count: int = Field(
        default=0, description="Number of low-severity violations (warnings)"
    )

    summary: str = Field(
        ..., description="Human-readable summary of compliance status"
    )

    recommendations: list[str] = Field(
        default_factory=list,
        description="Top 3-5 priority actions to improve compliance"
    )

    @model_validator(mode="after")
    def compute_counts(self) -> "ComplianceCheckOutput":
        """Count violations by severity."""
        self.critical_count = sum(1 for v in self.violations if v.severity == "critical")
        self.high_count = sum(1 for v in self.violations if v.severity == "high")
        self.medium_count = sum(1 for v in self.violations if v.severity == "medium")
        self.low_count = sum(1 for v in self.violations if v.severity == "low")

        # Mark as non-compliant if critical or high violations exist
        if self.critical_count > 0 or self.high_count > 0:
            self.is_compliant = False

        return self


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
    "PortfolioPriceData",
    "CorrelationConfig",
    "CorrelationMatrixOutput",
    "CovarianceMatrixOutput",
    "PortfolioCorrelationOutput",
    "BlackScholesInput",
    "GreeksOutput",
    "PortfolioDataInput",
    "OptimizationConfig",
    "OptimizationOutput",
    "EfficientFrontierOutput",
    "ComplianceConfig",
    "ComplianceViolation",
    "ComplianceCheckOutput",
]
