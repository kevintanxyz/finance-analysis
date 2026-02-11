"""
Momentum Indicators Calculator for NUMAN Portfolio Intelligence

Adapted from Finance Guru™ momentum.py
Implements comprehensive momentum indicator calculations.

Layer 2 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation
    Layer 2: Calculator Classes (THIS FILE) - Business logic
    Layer 3: MCP Tools - Agent integration

INDICATORS IMPLEMENTED:
1. RSI (Relative Strength Index) - 0-100 scale momentum
2. MACD (Moving Average Convergence Divergence) - Trend momentum
3. Stochastic Oscillator - Price range momentum
4. Williams %R - Inverted momentum oscillator
5. ROC (Rate of Change) - Percentage momentum

IMPROVEMENTS OVER FINANCE-GURU:
- Async/await for MCP integration
- Direct yfinance integration helper
- Type hints for Python 3.10+
- Simplified for portfolio analysis use case
"""

import pandas as pd
from datetime import date, timedelta
from typing import Literal

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


class MomentumIndicators:
    """Comprehensive momentum indicators calculator."""

    def __init__(self, config: MomentumConfig):
        """Initialize calculator with configuration."""
        self.config = config

    async def calculate_rsi(self, data: MomentumDataInput) -> RSIOutput:
        """
        Calculate Relative Strength Index.

        FORMULA:
            RS = Average Gain / Average Loss
            RSI = 100 - (100 / (1 + RS))

        INTERPRETATION:
            RSI > 70: Overbought (potential sell signal)
            RSI < 30: Oversold (potential buy signal)
            RSI = 50: Neutral momentum
        """
        prices = pd.Series(data.close, index=data.dates)

        if len(prices) < self.config.rsi_period + 1:
            raise ValueError(
                f"Need at least {self.config.rsi_period + 1} data points for RSI, "
                f"got {len(prices)}"
            )

        # Calculate price changes
        delta = prices.diff()

        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)

        # Calculate average gains and losses using Wilder's smoothing
        avg_gain = gains.rolling(window=self.config.rsi_period).mean()
        avg_loss = losses.rolling(window=self.config.rsi_period).mean()

        # Apply Wilder's smoothing
        for i in range(self.config.rsi_period, len(prices)):
            avg_gain.iloc[i] = (
                (avg_gain.iloc[i-1] * (self.config.rsi_period - 1) + gains.iloc[i])
                / self.config.rsi_period
            )
            avg_loss.iloc[i] = (
                (avg_loss.iloc[i-1] * (self.config.rsi_period - 1) + losses.iloc[i])
                / self.config.rsi_period
            )

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # Get current RSI
        current_rsi = float(rsi.iloc[-1])

        # Determine signal
        if current_rsi > 70:
            signal: Literal["overbought", "oversold", "neutral"] = "overbought"
        elif current_rsi < 30:
            signal = "oversold"
        else:
            signal = "neutral"

        return RSIOutput(
            ticker=data.ticker,
            calculation_date=data.dates[-1],
            current_rsi=current_rsi,
            rsi_signal=signal,
            period=self.config.rsi_period,
        )

    async def calculate_macd(self, data: MomentumDataInput) -> MACDOutput:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        FORMULA:
            MACD Line = EMA(fast) - EMA(slow)
            Signal Line = EMA(MACD Line, signal_period)
            Histogram = MACD Line - Signal Line

        INTERPRETATION:
            MACD > Signal: Bullish (buy signal)
            MACD < Signal: Bearish (sell signal)
        """
        prices = pd.Series(data.close, index=data.dates)

        min_periods = self.config.macd_slow + self.config.macd_signal
        if len(prices) < min_periods:
            raise ValueError(
                f"Need at least {min_periods} data points for MACD, got {len(prices)}"
            )

        # Calculate EMAs
        ema_fast = prices.ewm(span=self.config.macd_fast, adjust=False).mean()
        ema_slow = prices.ewm(span=self.config.macd_slow, adjust=False).mean()

        # Calculate MACD line
        macd_line = ema_fast - ema_slow

        # Calculate signal line
        signal_line = macd_line.ewm(span=self.config.macd_signal, adjust=False).mean()

        # Calculate histogram
        histogram = macd_line - signal_line

        # Get current values
        current_macd = float(macd_line.iloc[-1])
        current_signal = float(signal_line.iloc[-1])
        current_histogram = float(histogram.iloc[-1])

        # Determine signal
        signal_type: Literal["bullish", "bearish"] = (
            "bullish" if current_macd > current_signal else "bearish"
        )

        return MACDOutput(
            ticker=data.ticker,
            calculation_date=data.dates[-1],
            macd_line=current_macd,
            signal_line=current_signal,
            histogram=current_histogram,
            signal=signal_type,
            fast_period=self.config.macd_fast,
            slow_period=self.config.macd_slow,
            signal_period=self.config.macd_signal,
        )

    async def calculate_stochastic(self, data: MomentumDataInput) -> StochasticOutput:
        """
        Calculate Stochastic Oscillator.

        FORMULA:
            %K = 100 * (Close - Low_n) / (High_n - Low_n)
            %D = SMA(%K, d_period)

        INTERPRETATION:
            %K > 80: Overbought
            %K < 20: Oversold
        """
        if data.high is None or data.low is None:
            raise ValueError(
                "Stochastic requires high and low price data."
            )

        df = pd.DataFrame({
            'high': data.high,
            'low': data.low,
            'close': data.close,
        }, index=data.dates)

        if len(df) < self.config.stoch_k_period:
            raise ValueError(
                f"Need at least {self.config.stoch_k_period} data points for Stochastic"
            )

        # Calculate rolling high and low
        rolling_high = df['high'].rolling(window=self.config.stoch_k_period).max()
        rolling_low = df['low'].rolling(window=self.config.stoch_k_period).min()

        # Calculate %K
        k_values = 100 * (
            (df['close'] - rolling_low) / (rolling_high - rolling_low)
        )

        # Calculate %D
        d_values = k_values.rolling(window=self.config.stoch_d_period).mean()

        # Get current values
        current_k = float(k_values.iloc[-1])
        current_d = float(d_values.iloc[-1])

        # Determine signal
        if current_k > 80:
            signal: Literal["overbought", "oversold", "neutral"] = "overbought"
        elif current_k < 20:
            signal = "oversold"
        else:
            signal = "neutral"

        return StochasticOutput(
            ticker=data.ticker,
            calculation_date=data.dates[-1],
            k_value=current_k,
            d_value=current_d,
            signal=signal,
            k_period=self.config.stoch_k_period,
            d_period=self.config.stoch_d_period,
        )

    async def calculate_williams_r(self, data: MomentumDataInput) -> WilliamsROutput:
        """
        Calculate Williams %R.

        FORMULA:
            Williams %R = -100 * (High_n - Close) / (High_n - Low_n)

        INTERPRETATION:
            %R > -20: Overbought (sell signal)
            %R < -80: Oversold (buy signal)
        """
        if data.high is None or data.low is None:
            raise ValueError(
                "Williams %R requires high and low price data."
            )

        df = pd.DataFrame({
            'high': data.high,
            'low': data.low,
            'close': data.close,
        }, index=data.dates)

        if len(df) < self.config.williams_period:
            raise ValueError(
                f"Need at least {self.config.williams_period} data points for Williams %R"
            )

        # Calculate rolling high and low
        rolling_high = df['high'].rolling(window=self.config.williams_period).max()
        rolling_low = df['low'].rolling(window=self.config.williams_period).min()

        # Calculate Williams %R
        williams_r = -100 * (
            (rolling_high - df['close']) / (rolling_high - rolling_low)
        )

        # Get current value
        current_wr = float(williams_r.iloc[-1])

        # Determine signal
        if current_wr > -20:
            signal: Literal["overbought", "oversold", "neutral"] = "overbought"
        elif current_wr < -80:
            signal = "oversold"
        else:
            signal = "neutral"

        return WilliamsROutput(
            ticker=data.ticker,
            calculation_date=data.dates[-1],
            williams_r=current_wr,
            signal=signal,
            period=self.config.williams_period,
        )

    async def calculate_roc(self, data: MomentumDataInput) -> ROCOutput:
        """
        Calculate Rate of Change.

        FORMULA:
            ROC = ((Close - Close_n) / Close_n) * 100

        INTERPRETATION:
            ROC > 0: Bullish momentum (price increasing)
            ROC < 0: Bearish momentum (price decreasing)
        """
        prices = pd.Series(data.close, index=data.dates)

        if len(prices) < self.config.roc_period + 1:
            raise ValueError(
                f"Need at least {self.config.roc_period + 1} data points for ROC"
            )

        # Calculate ROC
        roc_series = prices.pct_change(periods=self.config.roc_period) * 100

        # Get current ROC
        current_roc = float(roc_series.iloc[-1])

        # Determine signal
        if current_roc > 0:
            signal: Literal["bullish", "bearish", "neutral"] = "bullish"
        elif current_roc < 0:
            signal = "bearish"
        else:
            signal = "neutral"

        return ROCOutput(
            ticker=data.ticker,
            calculation_date=data.dates[-1],
            roc=current_roc,
            signal=signal,
            period=self.config.roc_period,
        )

    async def calculate_all(self, data: MomentumDataInput) -> AllMomentumOutput:
        """Calculate all momentum indicators at once."""
        rsi_result = await self.calculate_rsi(data)
        macd_result = await self.calculate_macd(data)
        stoch_result = await self.calculate_stochastic(data)
        williams_result = await self.calculate_williams_r(data)
        roc_result = await self.calculate_roc(data)

        return AllMomentumOutput(
            ticker=data.ticker,
            calculation_date=data.dates[-1],
            rsi=rsi_result,
            macd=macd_result,
            stochastic=stoch_result,
            williams_r=williams_result,
            roc=roc_result,
        )

    @staticmethod
    async def fetch_momentum_data_from_yfinance(
        ticker: str, days: int = 90
    ) -> MomentumDataInput:
        """
        Fetch OHLC data from yfinance for momentum calculations.

        Args:
            ticker: Stock ticker symbol
            days: Number of days of historical data (default: 90)

        Returns:
            MomentumDataInput: Validated OHLC data
        """
        try:
            import yfinance as yf

            # Calculate date range (1.5x to account for weekends)
            end_date = date.today()
            start_date = end_date - timedelta(days=int(days * 1.5))

            # Fetch data
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(start=start_date, end=end_date)

            if hist.empty:
                raise ValueError(f"No data found for ticker {ticker}")

            # Extract OHLC data
            dates_list = [d.date() for d in hist.index]
            close_list = hist['Close'].tolist()
            high_list = hist['High'].tolist()
            low_list = hist['Low'].tolist()

            if len(dates_list) < 14:
                raise ValueError(
                    f"Insufficient data: got {len(dates_list)} days, need at least 14"
                )

            return MomentumDataInput(
                ticker=ticker.upper(),
                dates=dates_list,
                close=close_list,
                high=high_list,
                low=low_list,
            )

        except ImportError as e:
            raise ImportError("yfinance not installed") from e
        except Exception as e:
            raise ValueError(f"Failed to fetch data for {ticker}: {e}") from e


__all__ = ["MomentumIndicators"]
