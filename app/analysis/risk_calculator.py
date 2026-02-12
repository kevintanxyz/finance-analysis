"""
Risk Metrics Calculator for WealthPoint Analysis Intelligence

Adapted from Finance Guru™ src/analysis/risk_metrics.py
Implements comprehensive risk calculations with validated Pydantic models.

IMPROVEMENTS over Finance-Guru:
1. Async/await support for MCP integration
2. Direct yfinance integration helper methods
3. Enhanced error messages for portfolio context
4. Type hints for Python 3.10+
5. Better handling of edge cases

ARCHITECTURE:
This is Layer 2 of our 3-layer architecture:
    Layer 1: Pydantic Models (app/models/analysis.py)
    Layer 2: Calculator Classes (THIS FILE)
    Layer 3: MCP Tools (mcp_server/tools.py)

RISK METRICS IMPLEMENTED:
1. Value at Risk (VaR) - Historical & Parametric
2. Conditional VaR (CVaR) - Expected Shortfall
3. Sharpe Ratio - Risk-adjusted return
4. Sortino Ratio - Downside risk-adjusted return
5. Maximum Drawdown - Worst peak-to-trough decline
6. Calmar Ratio - Return per unit of max drawdown
7. Annual Volatility - Annualized standard deviation
8. Beta - Market sensitivity
9. Alpha - Excess return vs benchmark
"""

from __future__ import annotations

import warnings
from datetime import date, timedelta

import numpy as np
import pandas as pd
from scipy import stats

from app.models.analysis import (
    PriceDataInput,
    RiskCalculationConfig,
    RiskMetricsOutput,
)


class RiskCalculator:
    """
    Comprehensive risk metrics calculator for portfolio analysis.

    USAGE:
        config = RiskCalculationConfig(
            confidence_level=0.95,
            var_method="historical",
            rolling_window=252,
            risk_free_rate=0.045
        )

        calculator = RiskCalculator(config)
        results = await calculator.calculate_risk_metrics(price_data)

        # Access validated results
        print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
        print(f"Max Drawdown: {results.max_drawdown:.2%}")
    """

    def __init__(self, config: RiskCalculationConfig | None = None):
        """
        Initialize calculator with configuration.

        Args:
            config: Risk calculation configuration (defaults to standard settings)
        """
        self.config = config or RiskCalculationConfig()

    async def calculate_risk_metrics(
        self,
        price_data: PriceDataInput,
        benchmark_data: PriceDataInput | None = None,
    ) -> RiskMetricsOutput:
        """
        Calculate all risk metrics for a given price series.

        Args:
            price_data: Historical price data (validated by Pydantic)
            benchmark_data: Optional benchmark for beta/alpha (e.g., SPY)

        Returns:
            RiskMetricsOutput: All calculated metrics (validated structure)

        IMPROVEMENT: Made async for MCP compatibility
        """
        # Convert to pandas DataFrame
        df = pd.DataFrame({
            'date': price_data.dates,
            'price': price_data.prices,
        })
        df = df.set_index('date')

        # Calculate daily returns
        returns = df['price'].pct_change().dropna()

        # Calculate each risk metric
        var_95 = self._calculate_var(returns, self.config.confidence_level)
        cvar_95 = self._calculate_cvar(returns, self.config.confidence_level)
        sharpe = self._calculate_sharpe(returns, self.config.risk_free_rate)
        sortino = self._calculate_sortino(returns, self.config.risk_free_rate)
        max_dd = self._calculate_max_drawdown(df['price'])
        calmar = self._calculate_calmar(returns, max_dd, self.config.risk_free_rate)
        vol = self._calculate_annual_volatility(returns)

        # Calculate beta/alpha if benchmark provided
        beta_val = None
        alpha_val = None
        if benchmark_data is not None:
            beta_val, alpha_val = self._calculate_beta_alpha(
                returns,
                benchmark_data,
                self.config.risk_free_rate,
            )

        # Return validated output
        return RiskMetricsOutput(
            ticker=price_data.ticker,
            calculation_date=price_data.dates[-1],
            var_95=var_95,
            cvar_95=cvar_95,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_dd,
            calmar_ratio=calmar,
            annual_volatility=vol,
            beta=beta_val,
            alpha=alpha_val,
        )

    # ============================================================================
    # HELPER: Fetch data from yfinance
    # ============================================================================

    @staticmethod
    async def fetch_price_data_from_yfinance(
        ticker: str,
        days: int = 252,
    ) -> PriceDataInput:
        """
        Fetch historical price data from yfinance.

        IMPROVEMENT: Helper method for direct yfinance integration

        Args:
            ticker: Stock ticker symbol
            days: Number of trading days to fetch

        Returns:
            Validated PriceDataInput

        Raises:
            ValueError: If unable to fetch data
        """
        try:
            import yfinance as yf

            end_date = date.today()
            start_date = end_date - timedelta(days=int(days * 1.5))

            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(start=start_date, end=end_date)

            if hist.empty:
                raise ValueError(f"No data found for ticker {ticker}")

            prices = hist['Close'].tolist()
            dates = [d.date() for d in hist.index]

            if len(prices) < 30:
                raise ValueError(
                    f"Insufficient data: got {len(prices)} days, need at least 30"
                )

            return PriceDataInput(
                ticker=ticker.upper(),
                prices=prices,
                dates=dates,
            )

        except ImportError as e:
            raise ImportError("yfinance not installed. Run: uv add yfinance") from e
        except Exception as e:
            raise ValueError(f"Failed to fetch data for {ticker}: {e}") from e

    # ============================================================================
    # RISK CALCULATIONS (Adapted from Finance-Guru)
    # ============================================================================

    def _calculate_var(self, returns: pd.Series, confidence: float) -> float:
        """
        Calculate Value at Risk.

        FORMULA (Historical): VaR = percentile(returns, (1 - confidence) * 100)
        FORMULA (Parametric): VaR = mean + (z-score * std_dev)
        """
        if self.config.var_method == "historical":
            var = float(np.percentile(returns, (1 - confidence) * 100))
        else:
            mean_return = returns.mean()
            std_return = returns.std()
            z_score = stats.norm.ppf(1 - confidence)
            var = float(mean_return + (z_score * std_return))

        return var

    def _calculate_cvar(self, returns: pd.Series, confidence: float) -> float:
        """
        Calculate Conditional VaR (Expected Shortfall).

        FORMULA: CVaR = mean(returns where returns <= VaR)
        """
        var = self._calculate_var(returns, confidence)
        tail_returns = returns[returns <= var]

        if len(tail_returns) == 0:
            warnings.warn(
                f"No returns beyond VaR threshold of {var:.4f}. "
                "Insufficient data or unusual distribution."
            )
            return var

        return float(tail_returns.mean())

    def _calculate_sharpe(self, returns: pd.Series, risk_free_rate: float) -> float:
        """
        Calculate Sharpe Ratio.

        FORMULA: Sharpe = (mean_return - risk_free_rate) / std_dev * sqrt(252)
        """
        daily_rf = risk_free_rate / 252
        excess_returns = returns - daily_rf
        sharpe = excess_returns.mean() / returns.std()
        annualized_sharpe = sharpe * np.sqrt(252)

        return float(annualized_sharpe)

    def _calculate_sortino(self, returns: pd.Series, risk_free_rate: float) -> float:
        """
        Calculate Sortino Ratio.

        FORMULA: Sortino = (mean_return - risk_free_rate) / downside_std * sqrt(252)
        """
        daily_rf = risk_free_rate / 252
        excess_returns = returns - daily_rf
        downside_returns = returns[returns < 0]

        if len(downside_returns) == 0:
            warnings.warn(
                "No negative returns found. Sortino ratio may be unreliable."
            )
            return self._calculate_sharpe(returns, risk_free_rate)

        downside_std = downside_returns.std()
        sortino = excess_returns.mean() / downside_std
        annualized_sortino = sortino * np.sqrt(252)

        return float(annualized_sortino)

    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """
        Calculate Maximum Drawdown.

        FORMULA: drawdown = (price - running_max) / running_max
                 max_drawdown = min(all drawdowns)
        """
        running_max = prices.expanding().max()
        drawdowns = (prices - running_max) / running_max
        max_dd = float(drawdowns.min())

        return max_dd

    def _calculate_calmar(
        self,
        returns: pd.Series,
        max_drawdown: float,
        risk_free_rate: float
    ) -> float:
        """
        Calculate Calmar Ratio.

        FORMULA: Calmar = annualized_return / abs(max_drawdown)
        """
        annualized_return = returns.mean() * 252

        if max_drawdown == 0:
            warnings.warn("Max drawdown is zero. Calmar ratio undefined.")
            return float('inf')

        calmar = annualized_return / abs(max_drawdown)

        return float(calmar)

    def _calculate_annual_volatility(self, returns: pd.Series) -> float:
        """
        Calculate annualized volatility.

        FORMULA: annual_volatility = daily_std * sqrt(252)
        """
        daily_std = returns.std()
        annual_vol = daily_std * np.sqrt(252)

        return float(annual_vol)

    def _calculate_beta_alpha(
        self,
        returns: pd.Series,
        benchmark_data: PriceDataInput,
        risk_free_rate: float,
    ) -> tuple[float, float]:
        """
        Calculate Beta and Alpha vs benchmark.

        FORMULAS:
            Beta = covariance(asset, benchmark) / variance(benchmark)
            Alpha = mean_return - (risk_free_rate + beta * benchmark_excess_return)
        """
        # Convert benchmark to returns
        benchmark_df = pd.DataFrame({
            'date': benchmark_data.dates,
            'price': benchmark_data.prices,
        })
        benchmark_df = benchmark_df.set_index('date')
        benchmark_returns = benchmark_df['price'].pct_change().dropna()

        # Align dates
        aligned_data = pd.DataFrame({
            'asset': returns,
            'benchmark': benchmark_returns,
        }).dropna()

        if len(aligned_data) < 30:
            warnings.warn(
                f"Only {len(aligned_data)} overlapping points for beta/alpha. "
                "Results may be unreliable."
            )

        asset_returns = aligned_data['asset']
        bench_returns = aligned_data['benchmark']

        # Calculate Beta
        covariance = asset_returns.cov(bench_returns)
        benchmark_variance = bench_returns.var()
        beta = float(covariance / benchmark_variance)

        # Calculate Alpha (CAPM)
        daily_rf = risk_free_rate / 252
        asset_excess_return = (asset_returns.mean() - daily_rf) * 252
        benchmark_excess_return = (bench_returns.mean() - daily_rf) * 252
        expected_return = daily_rf * 252 + beta * benchmark_excess_return
        alpha = float(asset_excess_return - expected_return)

        return beta, alpha


__all__ = ["RiskCalculator"]
