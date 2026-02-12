"""
Portfolio Optimization Calculator for WealthPoint Analysis Intelligence

Adapted from Finance Guru™ optimizer.py
Implements Modern Portfolio Theory optimization methods.

Layer 2 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation
    Layer 2: Calculator Classes (THIS FILE) - Business logic
    Layer 3: MCP Tools - Agent integration

OPTIMIZATION METHODS:
1. Mean-Variance (Markowitz) - Balance return vs risk with target
2. Risk Parity - Equal risk contribution from each asset
3. Minimum Variance - Lowest risk portfolio (defensive)
4. Maximum Sharpe - Best risk-adjusted return (aggressive)
5. Black-Litterman - Market equilibrium + investor views

IMPROVEMENTS OVER FINANCE-GURU:
- Async/await for MCP integration
- Direct yfinance integration for price data
- Type hints for Python 3.9+
- Simplified for portfolio hedging use case
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from app.models.analysis import (
    EfficientFrontierOutput,
    OptimizationConfig,
    OptimizationOutput,
    PortfolioDataInput,
)


class PortfolioOptimizer:
    """
    Multi-method portfolio optimizer.

    WHAT: Calculates optimal asset allocation using various optimization techniques
    WHY: Provides validated, type-safe portfolio optimization for WealthPoint agents
    HOW: Uses Pydantic models for inputs/outputs, scipy for optimization, numpy/pandas for calculations

    EDUCATIONAL NOTE:
    Portfolio optimization is the science of allocating capital to maximize
    risk-adjusted returns. Different methods suit different investment goals:

    1. **Mean-Variance**: For investors with specific return targets
       - Pro: Intuitive, balances return vs risk
       - Con: Requires return forecasts (notoriously unreliable!)

    2. **Risk Parity**: For "all-weather" portfolios
       - Pro: No return forecasts needed, stable allocations
       - Con: Ignores return expectations, may underperform in bull markets

    3. **Minimum Variance**: For conservative capital preservation
       - Pro: Lowest risk, stable in volatile markets
       - Con: May sacrifice returns, can be too defensive

    4. **Maximum Sharpe**: For aggressive risk-adjusted growth
       - Pro: Optimal risk-adjusted returns, mathematically elegant
       - Con: Sensitive to input estimates, can be concentrated

    5. **Black-Litterman**: For incorporating specific views
       - Pro: Handles uncertainty well, combines equilibrium + views
       - Con: Complex, requires understanding of market equilibrium
    """

    def __init__(self, config: OptimizationConfig):
        """
        Initialize portfolio optimizer with configuration.

        Args:
            config: OptimizationConfig with method and constraints
        """
        self.config = config

    async def optimize(self, data: PortfolioDataInput) -> OptimizationOutput:
        """
        Optimize portfolio using configured method.

        This is the main entry point. It routes to the appropriate
        optimization method based on config.method.

        Args:
            data: PortfolioDataInput with price history

        Returns:
            OptimizationOutput with optimal weights and metrics

        Raises:
            ValueError: If optimization fails or constraints are infeasible
        """
        # Route to appropriate optimization method
        if self.config.method == "mean_variance":
            return await self.optimize_mean_variance(data)
        elif self.config.method == "risk_parity":
            return await self.optimize_risk_parity(data)
        elif self.config.method == "min_variance":
            return await self.optimize_min_variance(data)
        elif self.config.method == "max_sharpe":
            return await self.optimize_max_sharpe(data)
        elif self.config.method == "black_litterman":
            return await self.optimize_black_litterman(data)
        else:
            raise ValueError(f"Unknown optimization method: {self.config.method}")

    async def optimize_mean_variance(
        self, data: PortfolioDataInput
    ) -> OptimizationOutput:
        """
        Markowitz Mean-Variance Optimization.

        FORMULA:
        Minimize: w^T Σ w  (portfolio variance)
        Subject to:
            - w^T μ >= target_return (if specified)
            - Σw_i = 1 (fully invested)
            - position_limits constraints

        EDUCATIONAL NOTE:
        This is the Nobel Prize-winning approach (Markowitz, 1952).
        It finds the portfolio with the lowest risk for a given return target.

        Args:
            data: PortfolioDataInput

        Returns:
            OptimizationOutput with optimal allocation
        """
        # Calculate inputs
        returns = self._calculate_expected_returns(data)
        cov_matrix = self._calculate_covariance_matrix(data)
        n_assets = len(data.tickers)

        # Objective: minimize portfolio variance
        def objective(weights):
            return weights @ cov_matrix @ weights

        # Constraints
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

        # Add return constraint if target specified
        if self.config.target_return is not None:
            constraints.append(
                {
                    "type": "ineq",
                    "fun": lambda w: w @ returns - self.config.target_return,
                }
            )

        # Bounds (position limits)
        bounds = [self.config.position_limits for _ in range(n_assets)]

        # Initial guess (equal weight)
        x0 = np.array([1.0 / n_assets] * n_assets)

        # Optimize
        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000},
        )

        if not result.success:
            raise ValueError(f"Optimization failed: {result.message}")

        # Validate and return
        weights = self._validate_weights(result.x, data.tickers)
        return self._create_output(weights, data, returns, cov_matrix)

    async def optimize_risk_parity(
        self, data: PortfolioDataInput
    ) -> OptimizationOutput:
        """
        Risk Parity Optimization (Equal Risk Contribution).

        CONCEPT:
        Each asset contributes EQUALLY to total portfolio risk.

        EDUCATIONAL NOTE:
        Risk Parity was popularized by Bridgewater's "All Weather" portfolio.
        The key insight: equal DOLLAR allocation ≠ equal RISK allocation.

        Args:
            data: PortfolioDataInput

        Returns:
            OptimizationOutput with risk-balanced allocation
        """
        returns = self._calculate_expected_returns(data)
        cov_matrix = self._calculate_covariance_matrix(data)
        n_assets = len(data.tickers)

        # Objective: minimize variance of risk contributions
        def objective(weights):
            # Avoid division by zero
            portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
            if portfolio_vol < 1e-10:
                return 1e10

            marginal_contrib = cov_matrix @ weights
            risk_contrib = weights * marginal_contrib / portfolio_vol

            # Minimize sum of squared deviations from equal risk
            target_contrib = 1.0 / n_assets
            return np.sum((risk_contrib - target_contrib) ** 2)

        # Constraints
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

        # Bounds
        bounds = [self.config.position_limits for _ in range(n_assets)]

        # Initial guess (equal weight)
        x0 = np.array([1.0 / n_assets] * n_assets)

        # Optimize
        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000},
        )

        if not result.success:
            raise ValueError(f"Risk Parity optimization failed: {result.message}")

        weights = self._validate_weights(result.x, data.tickers)
        return self._create_output(weights, data, returns, cov_matrix)

    async def optimize_min_variance(
        self, data: PortfolioDataInput
    ) -> OptimizationOutput:
        """
        Minimum Variance Portfolio Optimization.

        FORMULA:
        Minimize: w^T Σ w  (portfolio variance)
        Subject to:
            - Σw_i = 1 (fully invested)
            - position_limits constraints
            - NO return constraint (pure risk minimization)

        EDUCATIONAL NOTE:
        This finds the lowest-risk allocation possible, ignoring returns entirely.

        Args:
            data: PortfolioDataInput

        Returns:
            OptimizationOutput with minimum-risk allocation
        """
        returns = self._calculate_expected_returns(data)
        cov_matrix = self._calculate_covariance_matrix(data)
        n_assets = len(data.tickers)

        # Objective: minimize portfolio variance
        def objective(weights):
            return weights @ cov_matrix @ weights

        # Constraints
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

        # Bounds
        bounds = [self.config.position_limits for _ in range(n_assets)]

        # Initial guess (equal weight)
        x0 = np.array([1.0 / n_assets] * n_assets)

        # Optimize
        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000},
        )

        if not result.success:
            raise ValueError(
                f"Minimum Variance optimization failed: {result.message}"
            )

        weights = self._validate_weights(result.x, data.tickers)
        return self._create_output(weights, data, returns, cov_matrix)

    async def optimize_max_sharpe(self, data: PortfolioDataInput) -> OptimizationOutput:
        """
        Maximum Sharpe Ratio Optimization.

        FORMULA:
        Maximize: (w^T μ - r_f) / √(w^T Σ w)

        Where:
            - μ = expected returns vector
            - r_f = risk-free rate
            - Σ = covariance matrix
            - w = portfolio weights

        EDUCATIONAL NOTE:
        The Sharpe ratio measures return per unit of risk. Maximizing it finds
        the portfolio with the best risk-adjusted returns.

        Args:
            data: PortfolioDataInput

        Returns:
            OptimizationOutput with maximum Sharpe allocation
        """
        returns = self._calculate_expected_returns(data)
        cov_matrix = self._calculate_covariance_matrix(data)
        n_assets = len(data.tickers)

        # Objective: maximize Sharpe ratio (minimize negative Sharpe)
        def objective(weights):
            portfolio_return = weights @ returns
            portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)

            # Avoid division by zero
            if portfolio_vol < 1e-10:
                return 1e10

            sharpe = (portfolio_return - self.config.risk_free_rate) / portfolio_vol
            return -sharpe  # Minimize negative = maximize

        # Constraints
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

        # Bounds
        bounds = [self.config.position_limits for _ in range(n_assets)]

        # Initial guess (equal weight)
        x0 = np.array([1.0 / n_assets] * n_assets)

        # Optimize
        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000},
        )

        if not result.success:
            raise ValueError(f"Maximum Sharpe optimization failed: {result.message}")

        weights = self._validate_weights(result.x, data.tickers)
        return self._create_output(weights, data, returns, cov_matrix)

    async def optimize_black_litterman(
        self, data: PortfolioDataInput
    ) -> OptimizationOutput:
        """
        Black-Litterman Model Optimization.

        CONCEPT:
        Combines market equilibrium returns with investor-specific views
        to produce more stable, intuitive allocations than pure Markowitz.

        EDUCATIONAL NOTE:
        Black-Litterman solves a major problem with Markowitz:
        Small changes in return estimates → huge changes in allocations

        Args:
            data: PortfolioDataInput

        Returns:
            OptimizationOutput with Black-Litterman allocation

        Raises:
            ValueError: If views are not provided in config
        """
        if self.config.views is None:
            raise ValueError("Black-Litterman requires views in config")

        # Calculate covariance matrix
        cov_matrix = self._calculate_covariance_matrix(data)
        n_assets = len(data.tickers)

        # Step 1: Calculate market equilibrium returns (reverse optimization)
        market_weights = np.array([1.0 / n_assets] * n_assets)
        risk_aversion = 2.5
        equilibrium_returns = risk_aversion * cov_matrix @ market_weights

        # Step 2: Incorporate investor views
        tau = 0.025

        # Build view matrix P and view vector Q
        view_tickers = list(self.config.views.keys())
        P = np.zeros((len(view_tickers), n_assets))
        Q = np.zeros(len(view_tickers))

        for i, view_ticker in enumerate(view_tickers):
            ticker_idx = data.tickers.index(view_ticker)
            P[i, ticker_idx] = 1.0
            Q[i] = self.config.views[view_ticker]

        # View uncertainty (omega)
        Omega = np.diag([P[i] @ cov_matrix @ P[i].T for i in range(len(view_tickers))])

        # Step 3: Compute posterior (blended) returns
        tau_cov_inv = np.linalg.inv(tau * cov_matrix)
        omega_inv = np.linalg.inv(Omega)

        posterior_precision = tau_cov_inv + P.T @ omega_inv @ P
        posterior_cov = np.linalg.inv(posterior_precision)

        posterior_returns = posterior_cov @ (
            tau_cov_inv @ equilibrium_returns + P.T @ omega_inv @ Q
        )

        # Step 4: Optimize using posterior returns
        def objective(weights):
            return weights @ cov_matrix @ weights

        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

        bounds = [self.config.position_limits for _ in range(n_assets)]

        x0 = np.array([1.0 / n_assets] * n_assets)

        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000},
        )

        if not result.success:
            raise ValueError(f"Black-Litterman optimization failed: {result.message}")

        weights = self._validate_weights(result.x, data.tickers)
        return self._create_output(weights, data, posterior_returns, cov_matrix)

    async def generate_efficient_frontier(
        self, data: PortfolioDataInput, n_points: int = 50
    ) -> EfficientFrontierOutput:
        """
        Generate efficient frontier for visualization.

        EDUCATIONAL NOTE:
        The efficient frontier shows all optimal portfolios across risk levels.
        Each point represents maximum return for a given risk level.

        Args:
            data: PortfolioDataInput
            n_points: Number of points on frontier

        Returns:
            EfficientFrontierOutput with frontier data
        """
        returns = self._calculate_expected_returns(data)
        cov_matrix = self._calculate_covariance_matrix(data)
        n_assets = len(data.tickers)

        # Find min and max possible returns on frontier
        min_var_weights = self._find_min_variance_weights(cov_matrix, n_assets)
        min_return = min_var_weights @ returns

        # Max return (subject to constraints)
        max_return = np.max(returns)

        # Generate target returns across range
        target_returns = np.linspace(min_return, max_return * 0.95, n_points)

        frontier_returns = []
        frontier_vols = []
        frontier_sharpes = []

        for target_ret in target_returns:
            try:
                # Optimize for this target return
                weights = self._optimize_for_target_return(
                    returns, cov_matrix, target_ret, n_assets
                )

                port_ret = weights @ returns
                port_vol = np.sqrt(weights @ cov_matrix @ weights)
                port_sharpe = (port_ret - self.config.risk_free_rate) / port_vol

                frontier_returns.append(float(port_ret))
                frontier_vols.append(float(port_vol))
                frontier_sharpes.append(float(port_sharpe))

            except Exception:
                # Skip infeasible points
                continue

        if len(frontier_returns) == 0:
            raise ValueError("Failed to generate efficient frontier")

        # Find optimal (max Sharpe) portfolio
        optimal_idx = int(np.argmax(frontier_sharpes))

        return EfficientFrontierOutput(
            returns=frontier_returns,
            volatilities=frontier_vols,
            sharpe_ratios=frontier_sharpes,
            optimal_portfolio_index=optimal_idx,
        )

    # Helper Methods

    def _calculate_expected_returns(self, data: PortfolioDataInput) -> np.ndarray:
        """
        Calculate or use provided expected returns.

        EDUCATIONAL NOTE:
        Expected returns are FUTURE returns, not historical averages.
        If not provided, we estimate from historical data using geometric mean.

        Args:
            data: PortfolioDataInput

        Returns:
            Array of expected annual returns
        """
        if data.expected_returns is not None:
            return np.array([data.expected_returns[t] for t in data.tickers])

        # Estimate from historical data
        df = pd.DataFrame(data.prices, index=data.dates)
        returns = df.pct_change().dropna()

        # Use geometric mean (more conservative)
        expected = []
        for ticker in data.tickers:
            mean_daily = returns[ticker].mean()
            annual_return = (1 + mean_daily) ** 252 - 1
            expected.append(annual_return)

        return np.array(expected)

    def _calculate_covariance_matrix(self, data: PortfolioDataInput) -> np.ndarray:
        """
        Calculate covariance matrix from price data.

        EDUCATIONAL NOTE:
        Covariance matrix captures:
        1. Individual asset volatilities (diagonal)
        2. Co-movement between assets (off-diagonal)

        Args:
            data: PortfolioDataInput

        Returns:
            Annualized covariance matrix
        """
        df = pd.DataFrame(data.prices, index=data.dates)
        returns = df.pct_change().dropna()

        # Calculate covariance matrix (daily)
        cov_daily = returns.cov().values

        # Annualize (multiply by 252 trading days)
        cov_annual = cov_daily * 252

        return cov_annual

    def _validate_weights(
        self, weights: np.ndarray, tickers: list[str]
    ) -> dict[str, float]:
        """
        Validate and convert weights array to dictionary.

        Args:
            weights: Array of weights
            tickers: List of ticker symbols

        Returns:
            Dictionary of {ticker: weight}
        """
        # Normalize to exactly 1.0 (handle numerical precision)
        weights = weights / weights.sum()

        # Convert to dictionary
        return {ticker: float(weight) for ticker, weight in zip(tickers, weights)}

    def _calculate_portfolio_metrics(
        self,
        weights: dict[str, float],
        returns: np.ndarray,
        cov_matrix: np.ndarray,
        tickers: list[str],
    ) -> tuple[float, float, float, float]:
        """
        Calculate portfolio return, volatility, Sharpe, and diversification ratio.

        Args:
            weights: Portfolio weights
            returns: Expected returns array
            cov_matrix: Covariance matrix
            tickers: Ticker symbols

        Returns:
            Tuple of (return, volatility, sharpe, diversification_ratio)
        """
        w = np.array([weights[t] for t in tickers])

        # Portfolio return
        port_return = float(w @ returns)

        # Portfolio volatility
        port_variance = w @ cov_matrix @ w
        port_vol = float(np.sqrt(port_variance))

        # Sharpe ratio
        sharpe = (port_return - self.config.risk_free_rate) / port_vol

        # Diversification ratio = weighted_avg_vol / portfolio_vol
        individual_vols = np.sqrt(np.diag(cov_matrix))
        weighted_avg_vol = w @ individual_vols
        diversification_ratio = weighted_avg_vol / port_vol

        return port_return, port_vol, sharpe, float(diversification_ratio)

    def _create_output(
        self,
        weights: dict[str, float],
        data: PortfolioDataInput,
        returns: np.ndarray,
        cov_matrix: np.ndarray,
    ) -> OptimizationOutput:
        """
        Create OptimizationOutput from weights.

        Args:
            weights: Optimal weights
            data: Input data
            returns: Expected returns
            cov_matrix: Covariance matrix

        Returns:
            OptimizationOutput
        """
        port_return, port_vol, sharpe, div_ratio = self._calculate_portfolio_metrics(
            weights, returns, cov_matrix, data.tickers
        )

        return OptimizationOutput(
            tickers=data.tickers,
            method=self.config.method,
            optimal_weights=weights,
            expected_return=port_return,
            expected_volatility=port_vol,
            sharpe_ratio=sharpe,
            diversification_ratio=div_ratio,
        )

    def _find_min_variance_weights(
        self, cov_matrix: np.ndarray, n_assets: int
    ) -> np.ndarray:
        """Helper to find minimum variance portfolio weights."""

        def objective(weights):
            return weights @ cov_matrix @ weights

        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
        bounds = [self.config.position_limits for _ in range(n_assets)]
        x0 = np.array([1.0 / n_assets] * n_assets)

        result = minimize(
            objective, x0, method="SLSQP", bounds=bounds, constraints=constraints
        )
        return result.x

    def _optimize_for_target_return(
        self,
        returns: np.ndarray,
        cov_matrix: np.ndarray,
        target_return: float,
        n_assets: int,
    ) -> np.ndarray:
        """Helper to optimize for specific target return."""

        def objective(weights):
            return weights @ cov_matrix @ weights

        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
            {"type": "eq", "fun": lambda w: w @ returns - target_return},
        ]
        bounds = [self.config.position_limits for _ in range(n_assets)]
        x0 = np.array([1.0 / n_assets] * n_assets)

        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000},
        )

        if not result.success:
            raise ValueError(f"Cannot achieve target return {target_return}")

        return result.x

    @staticmethod
    async def fetch_portfolio_data(
        tickers: list[str], days: int = 252
    ) -> PortfolioDataInput:
        """
        Fetch synchronized price data for portfolio optimization from yfinance.

        Args:
            tickers: List of ticker symbols
            days: Number of days of historical data (default: 252 = 1 year)

        Returns:
            PortfolioDataInput with synchronized prices

        Raises:
            ValueError: If data cannot be fetched or insufficient overlap
        """
        try:
            import yfinance as yf
        except ImportError as e:
            raise ImportError(
                "yfinance not installed. Install with: uv add yfinance"
            ) from e

        # Fetch extra days to account for weekends/holidays
        start_date = date.today() - timedelta(days=int(days * 1.5))
        end_date = date.today()

        # Download all tickers at once for alignment
        data = yf.download(
            tickers, start=start_date, end=end_date, progress=False, group_by="ticker"
        )

        if data.empty:
            raise ValueError(f"No data found for tickers: {tickers}")

        # Extract close prices for each ticker
        prices_dict = {}

        if len(tickers) == 1:
            # Single ticker - yfinance returns different structure
            ticker = tickers[0]
            if "Close" not in data.columns:
                raise ValueError(f"No close price data for {ticker}")
            prices_dict[ticker] = data["Close"].dropna().tolist()
            dates = data["Close"].dropna().index.tolist()
        else:
            # Multiple tickers
            for ticker in tickers:
                if ticker not in data:
                    raise ValueError(f"No data found for {ticker}")

                closes = data[ticker]["Close"].dropna()
                if len(closes) < min(days, 30):
                    raise ValueError(
                        f"Insufficient data for {ticker}. Need at least {min(days, 30)} days"
                    )

                prices_dict[ticker] = closes.tolist()

            # Get common dates
            common_index = data[tickers[0]]["Close"].dropna().index
            for ticker in tickers[1:]:
                ticker_index = data[ticker]["Close"].dropna().index
                common_index = common_index.intersection(ticker_index)

            if len(common_index) < min(days, 30):
                raise ValueError(
                    f"Insufficient overlapping dates. Need at least {min(days, 30)}"
                )

            # Truncate to common dates
            dates = common_index[-days:].tolist()
            for ticker in tickers:
                prices_dict[ticker] = data[ticker]["Close"].loc[dates].tolist()

        # Take only requested number of days
        if len(tickers) == 1:
            dates = dates[-days:]
            prices_dict[tickers[0]] = prices_dict[tickers[0]][-days:]
        else:
            dates = dates[-days:]

        # Convert datetime to date
        dates = [d.date() for d in dates]

        return PortfolioDataInput(
            tickers=tickers, dates=dates, prices=prices_dict
        )


__all__ = ["PortfolioOptimizer"]
