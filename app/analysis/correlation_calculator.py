"""
Correlation and Covariance Calculator for WealthPoint Analysis Intelligence

Adapted from Finance Guru™ correlation.py
Implements portfolio diversification analysis through correlation matrices.

Layer 2 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation
    Layer 2: Calculator Classes (THIS FILE) - Business logic
    Layer 3: MCP Tools - Agent integration

ANALYTICS:
- Pearson correlation matrices
- Covariance matrices
- Portfolio diversification scoring
- Concentration risk detection

IMPROVEMENTS OVER FINANCE-GURU:
- Async/await for MCP integration
- Direct yfinance integration helper
- Type hints for Python 3.10+
- Simplified for portfolio analysis use case
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from datetime import date, timedelta

from app.models.analysis import (
    CorrelationConfig,
    CorrelationMatrixOutput,
    CovarianceMatrixOutput,
    PortfolioCorrelationOutput,
    PortfolioPriceData,
)


class CorrelationCalculator:
    """
    Portfolio correlation and diversification calculator.

    Helps answer:
    1. Are my holdings diversified?
       - Low average correlation (<0.5) = Well diversified
       - High average correlation (>0.7) = Concentration risk

    2. Do I have effective hedges?
       - Negative correlations = Natural hedges

    3. How much risk am I taking?
       - Covariance matrix feeds portfolio variance calculations
    """

    def __init__(self, config: CorrelationConfig):
        """Initialize calculator with configuration."""
        self.config = config

    async def calculate_portfolio_correlation(
        self,
        data: PortfolioPriceData,
    ) -> PortfolioCorrelationOutput:
        """
        Calculate comprehensive correlation analysis for portfolio.

        This orchestrates all correlation calculations and returns
        a complete diversification assessment.

        Args:
            data: PortfolioPriceData with synchronized price series

        Returns:
            PortfolioCorrelationOutput with full correlation analysis
        """
        # Convert to DataFrame for calculations
        df = pd.DataFrame(data.prices, index=data.dates)

        # Calculate returns (correlation uses returns, not prices)
        returns = df.pct_change().dropna()

        # Calculate correlation matrix
        corr_matrix = await self._calculate_correlation_matrix(returns, data.tickers)

        # Calculate covariance matrix
        cov_matrix = await self._calculate_covariance_matrix(returns, data.tickers)

        # Calculate portfolio-level metrics
        div_score = self._calculate_diversification_score(corr_matrix.correlation_matrix)
        concentration_warning = corr_matrix.average_correlation > 0.7

        return PortfolioCorrelationOutput(
            calculation_date=data.dates[-1],
            tickers=data.tickers,
            correlation_matrix=corr_matrix,
            covariance_matrix=cov_matrix,
            diversification_score=div_score,
            concentration_warning=concentration_warning,
        )

    async def _calculate_correlation_matrix(
        self,
        returns: pd.DataFrame,
        tickers: list[str],
    ) -> CorrelationMatrixOutput:
        """
        Calculate correlation matrix between all assets.

        FORMULA:
        Pearson correlation between X and Y:
            ρ(X,Y) = Cov(X,Y) / (σ_X × σ_Y)

        INTERPRETATION:
        - 1.0: Perfect positive correlation (always move together)
        - 0.5-0.7: Strong positive correlation
        - 0.3-0.5: Moderate correlation
        - 0.0-0.3: Weak correlation
        - <0.0: Negative correlation (move opposite - HEDGE!)

        Args:
            returns: DataFrame of asset returns
            tickers: List of ticker symbols

        Returns:
            CorrelationMatrixOutput with full correlation matrix
        """
        # Calculate correlation matrix using pandas
        if self.config.method == "pearson":
            corr_df = returns.corr(method="pearson")
        else:  # spearman
            corr_df = returns.corr(method="spearman")

        # Convert to nested dict format
        corr_dict = {}
        for ticker1 in tickers:
            corr_dict[ticker1] = {}
            for ticker2 in tickers:
                corr_dict[ticker1][ticker2] = float(corr_df.loc[ticker1, ticker2])

        # Calculate average correlation (excluding diagonal)
        off_diagonal_values = []
        for i, ticker1 in enumerate(tickers):
            for j, ticker2 in enumerate(tickers):
                if i < j:  # Only upper triangle
                    off_diagonal_values.append(corr_dict[ticker1][ticker2])

        avg_corr = float(np.mean(off_diagonal_values)) if off_diagonal_values else 0.0

        # Clamp to [-1, 1] to handle floating point precision issues
        avg_corr = max(-1.0, min(1.0, avg_corr))

        # Get calculation date
        calc_date = returns.index[-1]
        if hasattr(calc_date, "date"):
            calc_date = calc_date.date()

        return CorrelationMatrixOutput(
            tickers=tickers,
            calculation_date=calc_date,
            correlation_matrix=corr_dict,
            average_correlation=avg_corr,
        )

    async def _calculate_covariance_matrix(
        self,
        returns: pd.DataFrame,
        tickers: list[str],
    ) -> CovarianceMatrixOutput:
        """
        Calculate covariance matrix between all assets.

        Covariance measures how two assets vary together in their actual units.

        WHY WE NEED THIS:
        Portfolio variance formula uses covariance matrix:
            σ²_portfolio = w^T × Σ × w

        This is used by portfolio optimizers to minimize risk.

        Args:
            returns: DataFrame of asset returns
            tickers: List of ticker symbols

        Returns:
            CovarianceMatrixOutput with full covariance matrix
        """
        # Calculate covariance matrix using pandas
        cov_df = returns.cov()

        # Convert to nested dict format
        cov_dict = {}
        for ticker1 in tickers:
            cov_dict[ticker1] = {}
            for ticker2 in tickers:
                cov_dict[ticker1][ticker2] = float(cov_df.loc[ticker1, ticker2])

        # Get calculation date
        calc_date = returns.index[-1]
        if hasattr(calc_date, "date"):
            calc_date = calc_date.date()

        return CovarianceMatrixOutput(
            tickers=tickers,
            calculation_date=calc_date,
            covariance_matrix=cov_dict,
        )

    def _calculate_diversification_score(
        self,
        correlation_matrix: dict[str, dict[str, float]],
    ) -> float:
        """
        Calculate portfolio diversification score.

        FORMULA:
        Diversification Score = 1 - average_correlation

        INTERPRETATION:
        - 1.0 = Perfect diversification (all correlations = 0)
        - 0.5 = Moderate diversification (average correlation = 0.5)
        - 0.0 = No diversification (all correlations = 1.0)

        GUIDELINE:
        - Score > 0.6: Excellent diversification
        - Score 0.4-0.6: Good diversification
        - Score 0.2-0.4: Moderate diversification
        - Score < 0.2: Poor diversification (concentration risk!)

        Args:
            correlation_matrix: Full correlation matrix

        Returns:
            Diversification score between 0 and 1
        """
        # Extract off-diagonal correlations
        tickers = list(correlation_matrix.keys())
        off_diagonal = []

        for i, ticker1 in enumerate(tickers):
            for j, ticker2 in enumerate(tickers):
                if i < j:
                    off_diagonal.append(correlation_matrix[ticker1][ticker2])

        if not off_diagonal:
            return 1.0  # Single asset = "perfectly diversified" by definition

        avg_corr = np.mean(off_diagonal)

        # Diversification score = 1 - average correlation
        # Higher score = better diversification
        div_score = float(1.0 - avg_corr)

        # Clamp to [0, 2] to handle floating point precision issues
        return max(0.0, min(2.0, div_score))

    @staticmethod
    async def fetch_portfolio_data_from_yfinance(
        tickers: list[str], days: int = 90
    ) -> PortfolioPriceData:
        """
        Fetch synchronized price data for multiple assets from yfinance.

        Args:
            tickers: List of stock ticker symbols
            days: Number of days of historical data (default: 90)

        Returns:
            PortfolioPriceData: Validated synchronized price data
        """
        try:
            import yfinance as yf

            # Calculate date range (1.5x to account for weekends)
            end_date = date.today()
            start_date = end_date - timedelta(days=int(days * 1.5))

            # Fetch data for all tickers
            data = yf.download(
                tickers,
                start=start_date,
                end=end_date,
                progress=False,
                group_by="ticker",
            )

            if data.empty:
                raise ValueError(f"No data found for tickers {tickers}")

            # Extract synchronized dates and prices
            dates_list = [d.date() for d in data.index]

            # Handle single vs multiple tickers
            prices_dict = {}
            if len(tickers) == 1:
                # Single ticker - yfinance returns simple structure
                ticker = tickers[0]
                prices_dict[ticker] = data["Close"].tolist()
            else:
                # Multiple tickers - yfinance returns multi-level structure
                for ticker in tickers:
                    if ticker in data:
                        prices_dict[ticker] = data[ticker]["Close"].tolist()
                    else:
                        # Try alternative structure
                        prices_dict[ticker] = data["Close"][ticker].tolist()

            if len(dates_list) < 30:
                raise ValueError(
                    f"Insufficient data: got {len(dates_list)} days, need at least 30"
                )

            return PortfolioPriceData(
                tickers=[t.upper() for t in tickers],
                dates=dates_list,
                prices={k.upper(): v for k, v in prices_dict.items()},
            )

        except ImportError as e:
            raise ImportError("yfinance not installed") from e
        except Exception as e:
            raise ValueError(f"Failed to fetch data for {tickers}: {e}") from e


__all__ = ["CorrelationCalculator"]
