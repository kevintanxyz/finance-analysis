"""
Market Data Service — fetches live data for listed positions.

Uses yfinance to get current prices, metrics, and historical data.
This is the bridge to Finance-Guru: it provides the same data
that Finance-Guru's CLI tools would compute.
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

from app.models.portfolio import MarketAnalysis, Position

logger = logging.getLogger(__name__)


class MarketDataService:
    """Fetch and compute market data for listed positions."""

    def get_analysis(self, position: Position) -> MarketAnalysis:
        """Get full market analysis for a listed position."""
        if not position.ticker:
            return MarketAnalysis(
                ticker="",
                name=position.name,
                currency=position.currency,
                weight_pct=position.weight_pct,
                value_chf=position.value_chf,
                error="No ticker available",
            )

        try:
            stock = yf.Ticker(position.ticker)
            info = stock.info or {}
            hist = stock.history(period="3mo")

            # Price changes
            price_1d = price_5d = price_1m = None
            if len(hist) >= 2:
                price_1d = (
                    (hist["Close"].iloc[-1] - hist["Close"].iloc[-2])
                    / hist["Close"].iloc[-2] * 100
                )
            if len(hist) >= 6:
                price_5d = (
                    (hist["Close"].iloc[-1] - hist["Close"].iloc[-6])
                    / hist["Close"].iloc[-6] * 100
                )
            if len(hist) >= 22:
                price_1m = (
                    (hist["Close"].iloc[-1] - hist["Close"].iloc[-22])
                    / hist["Close"].iloc[-22] * 100
                )

            return MarketAnalysis(
                ticker=position.ticker,
                name=position.name,
                currency=position.currency,
                weight_pct=position.weight_pct,
                value_chf=position.value_chf,
                perf_ytd_pct=position.perf_ytd_pct,
                current_price=info.get("currentPrice") or info.get("regularMarketPrice"),
                price_change_1d_pct=round(price_1d, 2) if price_1d else None,
                price_change_5d_pct=round(price_5d, 2) if price_5d else None,
                price_change_1m_pct=round(price_1m, 2) if price_1m else None,
                volume=info.get("volume"),
                market_cap=info.get("marketCap"),
                pe_ratio=info.get("trailingPE"),
                dividend_yield=info.get("dividendYield"),
                beta=info.get("beta"),
                fifty_two_week_high=info.get("fiftyTwoWeekHigh"),
                fifty_two_week_low=info.get("fiftyTwoWeekLow"),
            )
        except Exception as e:
            logger.error(f"Error fetching data for {position.ticker}: {e}")
            return MarketAnalysis(
                ticker=position.ticker,
                name=position.name,
                currency=position.currency,
                weight_pct=position.weight_pct,
                value_chf=position.value_chf,
                error=str(e),
            )

    def get_risk_metrics(self, ticker: str, benchmark: str = "SPY", days: int = 90) -> dict:
        """
        Compute risk metrics for a ticker (Finance-Guru compatible).

        Returns: sharpe, sortino, max_drawdown, var_95, beta, alpha, volatility
        """
        try:
            stock = yf.Ticker(ticker)
            bench = yf.Ticker(benchmark)

            hist = stock.history(period=f"{days}d")
            bench_hist = bench.history(period=f"{days}d")

            if hist.empty or bench_hist.empty:
                return {"error": f"No data for {ticker} or {benchmark}"}

            returns = hist["Close"].pct_change().dropna()
            bench_returns = bench_hist["Close"].pct_change().dropna()

            # Align dates
            common_idx = returns.index.intersection(bench_returns.index)
            returns = returns.loc[common_idx]
            bench_returns = bench_returns.loc[common_idx]

            if len(returns) < 5:
                return {"error": "Insufficient data"}

            # Annualization factor
            ann = np.sqrt(252)
            rf_daily = 0.05 / 252  # ~5% risk-free rate

            # Volatility
            vol = returns.std() * ann

            # Sharpe Ratio
            excess = returns - rf_daily
            sharpe = (excess.mean() / excess.std()) * ann if excess.std() > 0 else 0

            # Sortino Ratio
            downside = returns[returns < 0]
            sortino = (
                (excess.mean() / downside.std()) * ann
                if len(downside) > 0 and downside.std() > 0 else 0
            )

            # Max Drawdown
            cumulative = (1 + returns).cumprod()
            rolling_max = cumulative.cummax()
            drawdown = (cumulative - rolling_max) / rolling_max
            max_dd = drawdown.min()

            # VaR 95%
            var_95 = np.percentile(returns, 5)

            # Beta & Alpha
            if len(returns) == len(bench_returns) and len(returns) > 1:
                cov = np.cov(returns, bench_returns)
                beta = cov[0, 1] / cov[1, 1] if cov[1, 1] != 0 else 0
                alpha = (returns.mean() - rf_daily - beta * (bench_returns.mean() - rf_daily)) * 252
            else:
                beta = alpha = 0

            return {
                "ticker": ticker,
                "benchmark": benchmark,
                "period_days": days,
                "annualized_volatility": round(float(vol), 4),
                "sharpe_ratio": round(float(sharpe), 4),
                "sortino_ratio": round(float(sortino), 4),
                "max_drawdown": round(float(max_dd), 4),
                "var_95_daily": round(float(var_95), 4),
                "beta": round(float(beta), 4),
                "alpha_annualized": round(float(alpha), 4),
            }
        except Exception as e:
            logger.error(f"Risk metrics error for {ticker}: {e}")
            return {"error": str(e)}

    def get_momentum(self, ticker: str, days: int = 90) -> dict:
        """
        Compute momentum indicators (Finance-Guru compatible).

        Returns: RSI, MACD, signal, price vs SMA.
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=f"{days + 30}d")  # Extra for SMA calc

            if hist.empty or len(hist) < 30:
                return {"error": f"Insufficient data for {ticker}"}

            close = hist["Close"]

            # RSI (14-period)
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # MACD
            ema12 = close.ewm(span=12).mean()
            ema26 = close.ewm(span=26).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9).mean()

            # SMA
            sma20 = close.rolling(20).mean()
            sma50 = close.rolling(50).mean()

            current = close.iloc[-1]

            return {
                "ticker": ticker,
                "current_price": round(float(current), 2),
                "rsi_14": round(float(rsi.iloc[-1]), 2),
                "rsi_signal": (
                    "overbought" if rsi.iloc[-1] > 70
                    else "oversold" if rsi.iloc[-1] < 30
                    else "neutral"
                ),
                "macd": round(float(macd.iloc[-1]), 4),
                "macd_signal": round(float(signal.iloc[-1]), 4),
                "macd_histogram": round(float(macd.iloc[-1] - signal.iloc[-1]), 4),
                "macd_trend": "bullish" if macd.iloc[-1] > signal.iloc[-1] else "bearish",
                "sma_20": round(float(sma20.iloc[-1]), 2) if not pd.isna(sma20.iloc[-1]) else None,
                "sma_50": round(float(sma50.iloc[-1]), 2) if not pd.isna(sma50.iloc[-1]) else None,
                "price_vs_sma20": (
                    round((current / sma20.iloc[-1] - 1) * 100, 2)
                    if not pd.isna(sma20.iloc[-1]) else None
                ),
            }
        except Exception as e:
            logger.error(f"Momentum error for {ticker}: {e}")
            return {"error": str(e)}

    def get_correlation_matrix(self, tickers: list[str], days: int = 90) -> dict:
        """Compute correlation matrix between tickers."""
        try:
            data = yf.download(tickers, period=f"{days}d", progress=False)
            if data.empty:
                return {"error": "No data available"}

            if len(tickers) == 1:
                return {"tickers": tickers, "correlation": [[1.0]]}

            closes = data["Close"] if "Close" in data.columns else data
            returns = closes.pct_change().dropna()
            corr = returns.corr()

            return {
                "tickers": tickers,
                "correlation": corr.values.round(4).tolist(),
                "interpretation": self._interpret_correlation(corr, tickers),
            }
        except Exception as e:
            logger.error(f"Correlation error: {e}")
            return {"error": str(e)}

    @staticmethod
    def _interpret_correlation(corr: pd.DataFrame, tickers: list[str]) -> list[str]:
        """Human-readable correlation insights."""
        insights = []
        for i in range(len(tickers)):
            for j in range(i + 1, len(tickers)):
                val = corr.iloc[i, j]
                pair = f"{tickers[i]}/{tickers[j]}"
                if abs(val) > 0.8:
                    insights.append(f"{pair}: très corrélés ({val:.2f}) — faible diversification")
                elif abs(val) < 0.3:
                    insights.append(f"{pair}: faible corrélation ({val:.2f}) — bonne diversification")
                else:
                    insights.append(f"{pair}: corrélation modérée ({val:.2f})")
        return insights
