"""
Options Pricing Calculator for WealthPoint Analysis Intelligence

Adapted from Finance Guru™ options.py
Implements Black-Scholes option pricing and Greeks calculations.

Layer 2 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation
    Layer 2: Calculator Classes (THIS FILE) - Business logic
    Layer 3: MCP Tools - Agent integration

ANALYTICS:
- Black-Scholes-Merton option pricing
- Greeks: Delta, Gamma, Theta, Vega, Rho
- Moneyness classification (ITM/ATM/OTM)
- Intrinsic and time value decomposition

IMPROVEMENTS OVER FINANCE-GURU:
- Async/await for MCP integration
- Direct yfinance integration for stock price and volatility
- Type hints for Python 3.10+
- Simplified for portfolio hedging use case
"""

from __future__ import annotations

from datetime import date, timedelta
from math import exp, log, sqrt

import numpy as np
from scipy.stats import norm

from app.models.analysis import BlackScholesInput, GreeksOutput


class OptionsCalculator:
    """
    Black-Scholes options pricing and Greeks calculator.

    Calculates theoretical option prices and sensitivities for:
    1. Portfolio hedging (protective puts, covered calls)
    2. Options strategy analysis
    3. Risk management with Greeks

    EDUCATIONAL NOTE:
    The Black-Scholes model (1973) revolutionized derivatives pricing.
    It provides theoretical fair value for European options using:
    - Stock price, strike, time, volatility, interest rate

    FORMULA (Call):
        C = S * e^(-qT) * N(d1) - K * e^(-rT) * N(d2)
        where:
            d1 = [ln(S/K) + (r - q + σ²/2)T] / (σ√T)
            d2 = d1 - σ√T
            N() = cumulative normal distribution
    """

    async def price_option(self, params: BlackScholesInput, ticker: str = "UNKNOWN") -> GreeksOutput:
        """
        Calculate option price and all Greeks.

        Args:
            params: Validated Black-Scholes parameters
            ticker: Stock ticker symbol (for reference in output)

        Returns:
            GreeksOutput: Price and all sensitivities

        EDUCATIONAL NOTE:
        This method calculates EVERYTHING in one pass:
        1. d1 and d2 (intermediate values)
        2. Option price using Black-Scholes formula
        3. All five Greeks
        4. Intrinsic and time value
        5. Moneyness classification
        """
        # Extract parameters
        S = params.spot_price
        K = params.strike
        T = params.time_to_expiry
        sigma = params.volatility
        r = params.risk_free_rate
        q = params.dividend_yield
        is_call = params.option_type == "call"

        # Calculate d1 and d2
        d1, d2 = self._calculate_d1_d2(S, K, T, sigma, r, q)

        # Calculate option price
        if is_call:
            price = self._call_price(S, K, T, r, q, d1, d2)
        else:
            price = self._put_price(S, K, T, r, q, d1, d2)

        # Calculate Greeks
        delta = self._calculate_delta(is_call, d1, T, q)
        gamma = self._calculate_gamma(S, d1, T, sigma, q)
        theta = self._calculate_theta(is_call, S, K, T, r, q, sigma, d1, d2)
        vega = self._calculate_vega(S, T, d1, q)
        rho = self._calculate_rho(is_call, K, T, r, d2)

        # Calculate intrinsic and time value
        if is_call:
            intrinsic = max(S - K, 0.0)
        else:
            intrinsic = max(K - S, 0.0)
        time_value = price - intrinsic

        # Determine moneyness
        if is_call:
            if S > K * 1.02:
                moneyness = "ITM"
            elif S < K * 0.98:
                moneyness = "OTM"
            else:
                moneyness = "ATM"
        else:
            if S < K * 0.98:
                moneyness = "ITM"
            elif S > K * 1.02:
                moneyness = "OTM"
            else:
                moneyness = "ATM"

        return GreeksOutput(
            ticker=ticker,
            option_type=params.option_type,
            calculation_date=date.today(),
            option_price=float(price),
            intrinsic_value=float(intrinsic),
            time_value=float(time_value),
            delta=float(delta),
            gamma=float(gamma),
            theta=float(theta),
            vega=float(vega),
            rho=float(rho),
            moneyness=moneyness,  # type: ignore
            spot_price=S,
            strike=K,
            time_to_expiry=T,
            volatility=sigma,
        )

    @staticmethod
    async def fetch_stock_data_for_options(
        ticker: str, days: int = 90
    ) -> tuple[float, float]:
        """
        Fetch current stock price and historical volatility from yfinance.

        Args:
            ticker: Stock ticker symbol
            days: Number of days for volatility calculation (default: 90)

        Returns:
            Tuple of (current_price, annual_volatility)

        Raises:
            ValueError: If data cannot be fetched or ticker is invalid
        """
        try:
            import yfinance as yf

            # Calculate date range
            end_date = date.today()
            start_date = end_date - timedelta(days=int(days * 1.5))

            # Fetch data
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)

            if hist.empty:
                raise ValueError(f"No data found for ticker {ticker}")

            # Current price (last close)
            current_price = float(hist["Close"].iloc[-1])

            # Calculate historical volatility (annualized)
            # Volatility = std(daily returns) * sqrt(252 trading days)
            returns = hist["Close"].pct_change().dropna()
            daily_vol = float(returns.std())
            annual_vol = daily_vol * np.sqrt(252)

            # Sanity check
            if annual_vol < 0.01:
                import warnings
                warnings.warn(
                    f"Calculated volatility ({annual_vol:.1%}) is very low. "
                    "Consider using a longer time period or manual volatility input."
                )

            return current_price, annual_vol

        except ImportError as e:
            raise ImportError("yfinance not installed") from e
        except Exception as e:
            raise ValueError(f"Failed to fetch data for {ticker}: {e}") from e

    # Private helper methods

    def _calculate_d1_d2(
        self, S: float, K: float, T: float, sigma: float, r: float, q: float
    ) -> tuple[float, float]:
        """
        Calculate d1 and d2 for Black-Scholes.

        FORMULAS:
            d1 = [ln(S/K) + (r - q + σ²/2)T] / (σ√T)
            d2 = d1 - σ√T
        """
        d1 = (log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
        d2 = d1 - sigma * sqrt(T)
        return d1, d2

    def _call_price(
        self, S: float, K: float, T: float, r: float, q: float, d1: float, d2: float
    ) -> float:
        """
        Calculate call option price.

        FORMULA:
            C = S * e^(-qT) * N(d1) - K * e^(-rT) * N(d2)
        """
        call = S * exp(-q * T) * norm.cdf(d1) - K * exp(-r * T) * norm.cdf(d2)
        return max(call, 0.0)  # Price can't be negative

    def _put_price(
        self, S: float, K: float, T: float, r: float, q: float, d1: float, d2: float
    ) -> float:
        """
        Calculate put option price.

        FORMULA:
            P = K * e^(-rT) * N(-d2) - S * e^(-qT) * N(-d1)
        """
        put = K * exp(-r * T) * norm.cdf(-d2) - S * exp(-q * T) * norm.cdf(-d1)
        return max(put, 0.0)

    def _calculate_delta(self, is_call: bool, d1: float, T: float, q: float) -> float:
        """
        Calculate delta.

        FORMULAS:
            Call: Δ = e^(-qT) * N(d1)
            Put:  Δ = e^(-qT) * [N(d1) - 1] = -e^(-qT) * N(-d1)

        INTERPRETATION:
            Delta = 0.65 means: $1 stock up → $0.65 option up
        """
        if is_call:
            return exp(-q * T) * norm.cdf(d1)
        else:
            return exp(-q * T) * (norm.cdf(d1) - 1)

    def _calculate_gamma(
        self, S: float, d1: float, T: float, sigma: float, q: float
    ) -> float:
        """
        Calculate gamma.

        FORMULA:
            Γ = e^(-qT) * n(d1) / (S * σ * √T)
            where n() = standard normal PDF

        INTERPRETATION:
            Gamma = 0.05 means: $1 stock up → Delta increases by 0.05

        EDUCATIONAL NOTE:
        Gamma is highest for ATM options near expiry.
        This is when options are most sensitive to price changes.
        """
        gamma = exp(-q * T) * norm.pdf(d1) / (S * sigma * sqrt(T))
        return max(gamma, 0.0)

    def _calculate_theta(
        self,
        is_call: bool,
        S: float,
        K: float,
        T: float,
        r: float,
        q: float,
        sigma: float,
        d1: float,
        d2: float,
    ) -> float:
        """
        Calculate theta (time decay).

        EDUCATIONAL NOTE:
        Theta is ALWAYS negative (options lose value over time).
        Theta accelerates as expiry approaches.
        ATM options have highest theta.

        INTERPRETATION:
            Theta = -0.10 means: Lose $0.10 per day from time decay
        """
        term1 = -(S * norm.pdf(d1) * sigma * exp(-q * T)) / (2 * sqrt(T))

        if is_call:
            term2 = -r * K * exp(-r * T) * norm.cdf(d2)
            term3 = q * S * exp(-q * T) * norm.cdf(d1)
            theta = term1 + term2 + term3
        else:
            term2 = r * K * exp(-r * T) * norm.cdf(-d2)
            term3 = -q * S * exp(-q * T) * norm.cdf(-d1)
            theta = term1 + term2 + term3

        # Convert to per-day theta (divide by 365)
        return theta / 365

    def _calculate_vega(self, S: float, T: float, d1: float, q: float) -> float:
        """
        Calculate vega.

        FORMULA:
            V = S * e^(-qT) * √T * n(d1)

        INTERPRETATION:
            Vega = 0.22 means: 1% volatility up → $0.22 option price up

        EDUCATIONAL NOTE:
        Vega is highest for ATM options with time remaining.
        Short-dated and far OTM/ITM options have low vega.
        """
        vega = S * exp(-q * T) * sqrt(T) * norm.pdf(d1)
        # Divide by 100 to get per-1% change
        return vega / 100

    def _calculate_rho(self, is_call: bool, K: float, T: float, r: float, d2: float) -> float:
        """
        Calculate rho.

        FORMULAS:
            Call: ρ = K * T * e^(-rT) * N(d2)
            Put:  ρ = -K * T * e^(-rT) * N(-d2)

        INTERPRETATION:
            Rho = 0.18 means: 1% rate up → $0.18 option price up
        """
        if is_call:
            rho = K * T * exp(-r * T) * norm.cdf(d2)
        else:
            rho = -K * T * exp(-r * T) * norm.cdf(-d2)

        # Divide by 100 to get per-1% change
        return rho / 100


__all__ = ["OptionsCalculator"]
