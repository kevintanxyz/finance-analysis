"""
MCP Tools - Actions the LLM can perform.

Phase 1 tools:
- upload_portfolio: Parse PDF and save to database
- ask_portfolio: Q&A with intelligent routing

Phase 2-4 tools (to be added):
- get_market_data: Live market data for listed positions
- analyze_risk: VaR, Sharpe, Sortino, Beta, Alpha
- analyze_momentum: RSI, MACD, SMA, signals
- analyze_correlation: Correlation matrix + diversification
- price_options: Black-Scholes + Greeks
- optimize_portfolio: Allocation optimization
- backtest_strategy: Backtest vs benchmark
- check_compliance: Compliance violations
- analyze_dividends: Dividend analysis
- generate_full_report: Comprehensive report
"""
import base64
import json
import uuid
from datetime import datetime
from typing import Optional

from mcp_server.server import mcp
from app.database import get_session, Client, Portfolio
from app.parsers import parse_pdf
from app.services.qa_service_llm import QAService
from app.llm import create_llm


# ────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ────────────────────────────────────────────────────────────────────────────


def get_or_create_default_client(session) -> Client:
    """Get or create the default client."""
    client = session.get(Client, "default")
    if not client:
        client = Client(
            id="default",
            name="Default Client",
            risk_profile="moderate",
            notes="Auto-created default client for v1",
        )
        session.add(client)
        session.commit()
        session.refresh(client)
    return client


def get_portfolio_by_id(session_id: str) -> Optional[dict]:
    """
    Retrieve portfolio data from database.

    Args:
        session_id: Portfolio session ID

    Returns:
        Portfolio data as dict, or None if not found
    """
    with get_session() as session:
        portfolio = session.get(Portfolio, session_id)
        if not portfolio:
            return None

        # Parse JSON data
        data = json.loads(portfolio.data_json)
        return data


# ────────────────────────────────────────────────────────────────────────────
# Phase 1 Tools
# ────────────────────────────────────────────────────────────────────────────


@mcp.tool()
async def upload_portfolio(
    pdf_base64: str,
    filename: str = "valuation.pdf",
    client_id: str = "default",
    enable_llm_validation: bool = False,
) -> dict:
    """
    Parse a portfolio valuation PDF and extract structured financial data.

    **Version 1.2 — Claude Vision Router:**
    - Automatically detects bank format (NUMAN, UBS, Julius Baer, etc.)
    - Uses Claude Vision API to extract data intelligently (works with any format)
    - Validates extraction quality with cross-validation
    - Optional LLM validation layer for OCR corrections

    The PDF must be base64-encoded (the frontend encodes it before sending).
    Returns session_id — use this ID in ALL subsequent tool calls to reference
    this portfolio. The portfolio data is persisted in SQLite.

    **Multi-format support:**
    - NUMAN/Rothschild PDFs ✅
    - UBS PDFs ✅
    - Julius Baer PDFs ✅
    - Generic/unknown formats ✅

    Args:
        pdf_base64: Base64-encoded PDF file
        filename: Original filename (for reference)
        client_id: Client ID (defaults to "default")
        enable_llm_validation: Enable additional LLM validation layer (default: False)
                               Adds OCR correction and data enhancement

    Returns:
        dict with:
        - session_id: UUID to use in subsequent calls
        - summary: Quick overview (bank, total value, positions)
        - bank_detected: Detected bank/institution
        - strategy_used: Parsing strategy (llm_vision, pdfplumber, or hybrid)
        - confidence_score: Extraction confidence (0-1)
        - valuation_date: Date of valuation
        - total_value_chf: Total portfolio value
        - positions_count: Number of positions
        - validation_summary: Extraction warnings and corrections

    Example:
        # Claude Vision extraction (MVP default)
        result = upload_portfolio(pdf_base64, "portfolio.pdf")
        print(f"Bank: {result['bank_detected']}")
        print(f"Confidence: {result['confidence_score']}")

        # With additional LLM validation layer
        result = upload_portfolio(pdf_base64, "portfolio.pdf", enable_llm_validation=True)
        print(f"Corrections: {result['validation_summary']['corrections_applied']}")
    """
    try:
        # Decode PDF
        pdf_bytes = base64.b64decode(pdf_base64)

        # Create LLM provider (required for Claude Vision)
        llm = create_llm()

        # Parse with Claude Vision router
        from app.parsers.enhanced_parser import extract_positions_with_validation
        from app.parsers.valuation_pdf import ISIN_TICKER_MAP

        # Extract with Claude Vision + optional LLM validation
        try:
            validated_positions, validation_summary = await extract_positions_with_validation(
                pdf_bytes,
                ISIN_TICKER_MAP,
                total_value_chf=0.0,  # Will be calculated from positions
                llm=llm,
                enable_llm_validation=enable_llm_validation,
                verbose=False,
                filename=filename,
            )

            # Build PortfolioData from positions
            from app.models.portfolio import PortfolioData

            total_value = sum(p.value_chf for p in validated_positions)

            portfolio_data = PortfolioData(
                valuation_date=validation_summary.get("valuation_date", ""),
                total_value_chf=total_value,
                positions=validated_positions,
            )

        except Exception as e:
            # Claude Vision extraction failed - try basic fallback
            validation_summary = {
                "error": str(e),
                "fallback": "Claude Vision extraction failed, using basic parser",
                "bank_detected": "unknown",
                "strategy_used": "fallback",
                "confidence_score": 0.3,
            }

            # Fallback to basic parser
            portfolio_data = parse_pdf(pdf_bytes)

        # Generate session ID
        session_id = str(uuid.uuid4())

        # Store in database
        with get_session() as session:
            # Ensure client exists
            client = session.get(Client, client_id)
            if not client:
                client = get_or_create_default_client(session)

            # Create portfolio record
            portfolio = Portfolio(
                id=session_id,
                client_id=client.id,
                valuation_date=portfolio_data.valuation_date or "",
                total_value_chf=portfolio_data.total_value_chf,
                data_json=portfolio_data.model_dump_json(),
                pdf_filename=filename,
            )

            session.add(portfolio)
            session.commit()

        # Extract Claude Vision summary info
        bank_detected = validation_summary.get("bank_detected", "unknown")
        strategy_used = validation_summary.get("strategy_used", "llm_vision")
        confidence_score = validation_summary.get("confidence_score", 1.0)

        # Build response
        response = {
            "session_id": session_id,
            "summary": (
                f"Portfolio loaded successfully! "
                f"Bank: {bank_detected}, "
                f"{len(portfolio_data.positions)} positions, "
                f"CHF {portfolio_data.total_value_chf:,.2f}".replace(",", "'")
            ),
            "bank_detected": bank_detected,
            "strategy_used": strategy_used,
            "confidence_score": confidence_score,
            "valuation_date": portfolio_data.valuation_date or "",
            "total_value_chf": portfolio_data.total_value_chf,
            "positions_count": len(portfolio_data.positions),
        }

        # Add validation summary if enabled
        if enable_llm_validation and validation_summary:
            response["validation_summary"] = validation_summary

        return response

    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to parse PDF. Please ensure it's a valid NUMAN valuation PDF.",
        }


@mcp.tool()
async def ask_portfolio(session_id: str, question: str) -> dict:
    """
    Ask any question about a portfolio in natural language (French or English).

    The Q&A service automatically routes to the right analysis and returns
    both a text answer and structured data (charts, tables, KPIs) for the
    frontend to render.

    Args:
        session_id: Portfolio session ID (from upload_portfolio)
        question: User question in French or English

    Returns:
        dict with:
        - content: Text answer
        - display_type: How to display (text, kpi_cards, pie_chart, table, etc.)
        - charts: Array of chart data (optional)
        - tables: Array of table data (optional)
        - kpis: Array of KPI cards (optional)

    Examples:
        - "Quelle est l'allocation du portefeuille ?"
        - "Top performers YTD"
        - "Analyse le risque de Roche"
        - "Should I rebalance towards more bonds?"
    """
    # Get portfolio data
    portfolio_data = get_portfolio_by_id(session_id)
    if not portfolio_data:
        return {
            "content": f"Portfolio {session_id} not found. Please upload a PDF first.",
            "display_type": "text",
            "error": "portfolio_not_found",
        }

    # Create LLM provider
    llm = create_llm()

    # Create Q&A service
    qa_service = QAService(llm)

    # Process question
    try:
        response = await qa_service.ask(portfolio_data, question)
        return response

    except Exception as e:
        return {
            "content": f"Error processing question: {str(e)}",
            "display_type": "text",
            "error": str(e),
        }


# ────────────────────────────────────────────────────────────────────────────
# Phase 2-4 Tools (Placeholders)
# ────────────────────────────────────────────────────────────────────────────


@mcp.tool()
async def get_market_data(session_id: str) -> dict:
    """
    Get live market data for all listed positions.

    [PHASE 2] Not yet implemented.
    """
    return {
        "content": "Market data tool not yet implemented (Phase 2).",
        "display_type": "text",
    }


@mcp.tool()
async def analyze_risk(
    session_id: str,
    ticker: str,
    benchmark: str = "SPY",
    days: int = 90,
    confidence_level: float = 0.95,
) -> dict:
    """
    Compute comprehensive risk metrics for a listed position.

    Calculates: VaR, CVaR, Sharpe, Sortino, Beta, Alpha, Max Drawdown, Volatility.

    BUSINESS VALUE:
    - Data-driven investment decisions
    - Professional risk reports for clients
    - Quick comparison vs benchmark

    Args:
        session_id: Portfolio session ID
        ticker: Stock ticker (e.g., "ROG.SW", "AAPL", "TTE.PA")
        benchmark: Benchmark ticker for beta/alpha (default: SPY)
        days: Historical period in trading days (default: 90, ~3 months)
        confidence_level: VaR confidence level (default: 0.95 = 95%)

    Returns:
        Risk metrics as KPI cards + interpretation text

    Example:
        analyze_risk("abc-123", "ROG.SW", "SPY", 252)  # 1-year analysis
    """
    try:
        # ✨ IMPROVEMENT: Check cache first (5-minute TTL)
        from app.services.analysis_cache import AnalysisCacheService

        cache_params = {
            "benchmark": benchmark,
            "days": days,
            "confidence_level": confidence_level,
        }

        cached_result = AnalysisCacheService.get_cached_result(
            portfolio_id=session_id,
            analysis_type="risk_analysis",
            ticker=ticker,
            parameters=cache_params,
        )

        if cached_result:
            # Cache hit - return immediately (INSTANT + FREE) 💰
            cached_result["_from_cache"] = True
            cached_result["_cache_note"] = "⚡ Using cached result (< 5 min old)"
            return cached_result

        # Cache miss - proceed with calculation
        # Load portfolio to verify position exists
        with get_session() as db_session:
            portfolio = db_session.get(Portfolio, session_id)
            if not portfolio:
                return {
                    "content": f"Portfolio {session_id} not found.",
                    "display_type": "text",
                    "error": "Portfolio not found"
                }

            # Parse portfolio data
            from app.models.portfolio import PortfolioData
            portfolio_data = PortfolioData.model_validate_json(portfolio.data_json)

            # Check if ticker exists in portfolio (optional - warn but continue)
            position_in_portfolio = any(
                p.ticker == ticker for p in portfolio_data.positions if p.ticker
            )

        # Fetch price data from yfinance
        from app.analysis.risk_calculator import RiskCalculator
        from app.models.analysis import RiskCalculationConfig

        calculator = RiskCalculator(
            RiskCalculationConfig(
                confidence_level=confidence_level,
                var_method="historical",
                rolling_window=min(days, 252),
                risk_free_rate=0.045,
            )
        )

        # Fetch ticker data
        price_data = await calculator.fetch_price_data_from_yfinance(ticker, days)

        # Fetch benchmark data
        benchmark_data = await calculator.fetch_price_data_from_yfinance(benchmark, days)

        # Calculate risk metrics
        results = await calculator.calculate_risk_metrics(price_data, benchmark_data)

        # Build KPI cards for frontend
        kpis = [
            {
                "label": "Sharpe Ratio",
                "value": f"{results.sharpe_ratio:.2f}",
                "change": _interpret_sharpe(results.sharpe_ratio),
                "change_type": "positive" if results.sharpe_ratio > 1.0 else "neutral",
                "icon": "trending-up"
            },
            {
                "label": "Max Drawdown",
                "value": f"{results.max_drawdown:.2%}",
                "change": f"{abs(results.max_drawdown):.1%} worst decline",
                "change_type": "negative" if results.max_drawdown < -0.20 else "neutral",
                "icon": "trending-down"
            },
            {
                "label": "Annual Volatility",
                "value": f"{results.annual_volatility:.1%}",
                "change": _interpret_volatility(results.annual_volatility),
                "change_type": "neutral",
                "icon": "activity"
            },
            {
                "label": "Beta vs SPY",
                "value": f"{results.beta:.2f}" if results.beta else "N/A",
                "change": _interpret_beta(results.beta) if results.beta else "",
                "change_type": "neutral",
                "icon": "bar-chart"
            },
        ]

        # Build interpretation text
        interpretation = _build_risk_interpretation(results, ticker, benchmark, position_in_portfolio)

        response = {
            "content": interpretation,
            "display_type": "mixed",
            "kpis": kpis,
            "metrics": {
                "ticker": ticker,
                "calculation_date": str(results.calculation_date),
                "var_95": results.var_95,
                "cvar_95": results.cvar_95,
                "sharpe_ratio": results.sharpe_ratio,
                "sortino_ratio": results.sortino_ratio,
                "max_drawdown": results.max_drawdown,
                "calmar_ratio": results.calmar_ratio,
                "annual_volatility": results.annual_volatility,
                "beta": results.beta,
                "alpha": results.alpha,
            },
        }

        # ✨ IMPROVEMENT: Save to cache for future queries (5-min TTL)
        AnalysisCacheService.save_result(
            portfolio_id=session_id,
            analysis_type="risk_analysis",
            result=response,
            ticker=ticker,
            parameters=cache_params,
        )

        return response

    except ValueError as e:
        return {
            "content": f"Unable to fetch data for {ticker}: {str(e)}",
            "display_type": "text",
            "error": str(e)
        }
    except Exception as e:
        return {
            "content": f"Error analyzing risk for {ticker}: {str(e)}",
            "display_type": "text",
            "error": str(e)
        }


# ────────────────────────────────────────────────────────────────────────────
# Helper functions for risk interpretation
# ────────────────────────────────────────────────────────────────────────────

def _interpret_sharpe(sharpe: float) -> str:
    """Interpret Sharpe ratio for business users."""
    if sharpe < 1.0:
        return "Poor risk-adjusted return"
    elif sharpe < 2.0:
        return "Good risk-adjusted return"
    else:
        return "Excellent risk-adjusted return"


def _interpret_volatility(vol: float) -> str:
    """Interpret annual volatility for business users."""
    if vol < 0.20:
        return "Low volatility"
    elif vol < 0.40:
        return "Medium volatility"
    elif vol < 0.80:
        return "High volatility"
    else:
        return "Extreme volatility"


def _interpret_beta(beta: float) -> str:
    """Interpret beta for business users."""
    if beta < 0.5:
        return "Defensive (low market risk)"
    elif beta < 1.5:
        return "Average market risk"
    else:
        return "Aggressive (high market risk)"


def _build_risk_interpretation(
    results,
    ticker: str,
    benchmark: str,
    position_in_portfolio: bool
) -> str:
    """Build business-friendly interpretation of risk metrics."""
    lines = []

    # Header
    if position_in_portfolio:
        lines.append(f"✅ **Risk Analysis: {ticker}** (Position in your portfolio)")
    else:
        lines.append(f"⚠️  **Risk Analysis: {ticker}** (Not in your portfolio)")

    lines.append(f"📅 Data through: {results.calculation_date}")
    lines.append(f"💱 Note: Risk metrics are currency-independent percentages")
    lines.append("")

    # Sharpe interpretation
    sharpe_rating = _interpret_sharpe(results.sharpe_ratio)
    lines.append(f"**Risk-Adjusted Returns ({sharpe_rating})**")
    lines.append(f"- Sharpe Ratio: {results.sharpe_ratio:.2f}")
    lines.append(f"- Sortino Ratio: {results.sortino_ratio:.2f}")
    lines.append("")

    # Drawdown interpretation
    lines.append(f"**Downside Risk**")
    lines.append(f"- Maximum Drawdown: {results.max_drawdown:.2%} (worst decline from peak)")
    lines.append(f"- 95% VaR: {results.var_95:.2%} (daily loss threshold)")
    lines.append(f"- 95% CVaR: {results.cvar_95:.2%} (expected loss beyond VaR)")
    lines.append("")

    # Volatility
    vol_rating = _interpret_volatility(results.annual_volatility)
    lines.append(f"**Volatility ({vol_rating})**")
    lines.append(f"- Annual Volatility: {results.annual_volatility:.1%}")
    lines.append("")

    # Beta/Alpha (if available)
    if results.beta is not None and results.alpha is not None:
        beta_rating = _interpret_beta(results.beta)
        lines.append(f"**Market Relationship vs {benchmark}**")
        lines.append(f"- Beta: {results.beta:.2f} ({beta_rating})")

        if results.alpha > 0:
            lines.append(f"- Alpha: +{results.alpha:.2%} (outperforming)")
        else:
            lines.append(f"- Alpha: {results.alpha:.2%} (underperforming)")
        lines.append("")

    # Recommendation
    lines.append("**💡 Interpretation:**")
    if results.sharpe_ratio > 1.5 and results.max_drawdown > -0.30:
        lines.append("Good risk-adjusted returns with moderate drawdowns. Position looks healthy.")
    elif results.sharpe_ratio < 0.5:
        lines.append("Poor risk-adjusted returns. Consider reviewing this position.")
    elif results.max_drawdown < -0.40:
        lines.append("Significant historical drawdown. Assess if risk tolerance aligns with objectives.")
    else:
        lines.append("Standard risk profile. Monitor regularly and compare vs portfolio objectives.")

    return "\n".join(lines)


@mcp.tool()
async def analyze_momentum(
    session_id: str,
    ticker: str,
    days: int = 90,
    rsi_period: int = 14,
    macd_fast: int = 12,
    macd_slow: int = 26,
) -> dict:
    """
    Calculate momentum indicators to identify trading signals and trend strength.

    Calculates: RSI, MACD, Stochastic, Williams %R, ROC (Rate of Change).

    BUSINESS VALUE:
    - Identify overbought/oversold conditions
    - Spot trend changes and momentum shifts
    - Time entry/exit points for active positions

    Args:
        session_id: Portfolio session ID
        ticker: Stock ticker (e.g., "ROG.SW", "AAPL", "NVDA")
        days: Historical period in trading days (default: 90, ~3 months)
        rsi_period: RSI calculation period (default: 14 days, industry standard)
        macd_fast: MACD fast EMA period (default: 12 days)
        macd_slow: MACD slow EMA period (default: 26 days)

    Returns:
        Momentum indicators as KPI cards + confluence analysis

    Example:
        analyze_momentum("abc-123", "NVDA", 90)  # 3-month momentum analysis
    """
    try:
        # ✨ IMPROVEMENT: Check cache first (5-minute TTL)
        from app.services.analysis_cache import AnalysisCacheService

        cache_params = {
            "days": days,
            "rsi_period": rsi_period,
            "macd_fast": macd_fast,
            "macd_slow": macd_slow,
        }

        cached_result = AnalysisCacheService.get_cached_result(
            portfolio_id=session_id,
            analysis_type="momentum",
            ticker=ticker,
            parameters=cache_params,
        )

        if cached_result:
            # Cache hit - return immediately
            cached_result["_from_cache"] = True
            cached_result["_cache_note"] = "⚡ Using cached result (< 5 min old)"
            return cached_result

        # Cache miss - proceed with calculation
        # Load portfolio to verify position exists
        with get_session() as db_session:
            portfolio = db_session.get(Portfolio, session_id)
            if not portfolio:
                return {
                    "content": f"Portfolio {session_id} not found.",
                    "display_type": "text",
                    "error": "Portfolio not found"
                }

            # Parse portfolio data
            from app.models.portfolio import PortfolioData
            portfolio_data = PortfolioData.model_validate_json(portfolio.data_json)

            # Check if ticker exists in portfolio
            position_in_portfolio = any(
                p.ticker == ticker for p in portfolio_data.positions if p.ticker
            )

        # Fetch OHLC data from yfinance
        from app.analysis.momentum_calculator import MomentumIndicators
        from app.models.analysis import MomentumConfig

        calculator = MomentumIndicators(
            MomentumConfig(
                rsi_period=rsi_period,
                macd_fast=macd_fast,
                macd_slow=macd_slow,
                macd_signal=9,  # Standard
                stoch_k_period=14,  # Standard
                stoch_d_period=3,  # Standard
                williams_period=14,  # Standard
                roc_period=12,  # Standard
            )
        )

        # Fetch momentum data
        momentum_data = await calculator.fetch_momentum_data_from_yfinance(ticker, days)

        # Calculate all momentum indicators
        results = await calculator.calculate_all(momentum_data)

        # Build KPI cards for frontend
        kpis = [
            {
                "label": "RSI",
                "value": f"{results.rsi.current_rsi:.1f}",
                "change": _interpret_rsi_signal(results.rsi.rsi_signal),
                "change_type": _signal_to_change_type(results.rsi.rsi_signal),
                "icon": "activity"
            },
            {
                "label": "MACD",
                "value": f"{results.macd.histogram:.2f}",
                "change": results.macd.signal.title(),
                "change_type": "positive" if results.macd.signal == "bullish" else "negative",
                "icon": "trending-up"
            },
            {
                "label": "Stochastic %K",
                "value": f"{results.stochastic.k_value:.1f}",
                "change": _interpret_rsi_signal(results.stochastic.signal),
                "change_type": _signal_to_change_type(results.stochastic.signal),
                "icon": "bar-chart"
            },
            {
                "label": "ROC",
                "value": f"{results.roc.roc:+.1f}%",
                "change": results.roc.signal.title() + " momentum",
                "change_type": "positive" if results.roc.signal == "bullish" else "negative" if results.roc.signal == "bearish" else "neutral",
                "icon": "trending-up"
            },
        ]

        # Calculate confluence (how many indicators agree)
        confluence = _calculate_momentum_confluence(results)

        # Build interpretation text
        interpretation = _build_momentum_interpretation(
            results, ticker, position_in_portfolio, confluence
        )

        response = {
            "content": interpretation,
            "display_type": "mixed",
            "kpis": kpis,
            "indicators": {
                "ticker": ticker,
                "calculation_date": str(results.calculation_date),
                "rsi": {
                    "value": results.rsi.current_rsi,
                    "signal": results.rsi.rsi_signal,
                    "period": results.rsi.period,
                },
                "macd": {
                    "macd_line": results.macd.macd_line,
                    "signal_line": results.macd.signal_line,
                    "histogram": results.macd.histogram,
                    "signal": results.macd.signal,
                },
                "stochastic": {
                    "k_value": results.stochastic.k_value,
                    "d_value": results.stochastic.d_value,
                    "signal": results.stochastic.signal,
                },
                "williams_r": {
                    "value": results.williams_r.williams_r,
                    "signal": results.williams_r.signal,
                },
                "roc": {
                    "value": results.roc.roc,
                    "signal": results.roc.signal,
                },
                "confluence": confluence,
            },
        }

        # ✨ IMPROVEMENT: Save to cache (5-min TTL)
        AnalysisCacheService.save_result(
            portfolio_id=session_id,
            analysis_type="momentum",
            result=response,
            ticker=ticker,
            parameters=cache_params,
        )

        return response

    except ValueError as e:
        return {
            "content": f"Unable to fetch data for {ticker}: {str(e)}",
            "display_type": "text",
            "error": str(e)
        }
    except Exception as e:
        return {
            "content": f"Error analyzing momentum for {ticker}: {str(e)}",
            "display_type": "text",
            "error": str(e)
        }


# ────────────────────────────────────────────────────────────────────────────
# Helper functions for momentum interpretation
# ────────────────────────────────────────────────────────────────────────────

def _interpret_rsi_signal(signal: str) -> str:
    """Interpret RSI/Stochastic signal for business users."""
    if signal == "overbought":
        return "Overbought"
    elif signal == "oversold":
        return "Oversold"
    else:
        return "Neutral"


def _signal_to_change_type(signal: str) -> str:
    """Convert signal to change_type for KPI cards."""
    if signal == "oversold":
        return "positive"  # Potential buy opportunity
    elif signal == "overbought":
        return "negative"  # Potential sell pressure
    else:
        return "neutral"


def _calculate_momentum_confluence(results) -> dict:
    """Calculate how many indicators agree on bullish/bearish signals."""
    bullish_count = 0
    bearish_count = 0

    # RSI
    if results.rsi.rsi_signal == "oversold":
        bullish_count += 1
    elif results.rsi.rsi_signal == "overbought":
        bearish_count += 1

    # MACD
    if results.macd.signal == "bullish":
        bullish_count += 1
    else:
        bearish_count += 1

    # Stochastic
    if results.stochastic.signal == "oversold":
        bullish_count += 1
    elif results.stochastic.signal == "overbought":
        bearish_count += 1

    # Williams %R
    if results.williams_r.signal == "oversold":
        bullish_count += 1
    elif results.williams_r.signal == "overbought":
        bearish_count += 1

    # ROC
    if results.roc.signal == "bullish":
        bullish_count += 1
    elif results.roc.signal == "bearish":
        bearish_count += 1

    total_indicators = 5
    return {
        "bullish": bullish_count,
        "bearish": bearish_count,
        "total": total_indicators,
        "agreement": max(bullish_count, bearish_count) / total_indicators,
    }


def _build_momentum_interpretation(
    results,
    ticker: str,
    position_in_portfolio: bool,
    confluence: dict
) -> str:
    """Build business-friendly interpretation of momentum indicators."""
    lines = []

    # Header
    if position_in_portfolio:
        lines.append(f"✅ **Momentum Analysis: {ticker}** (Position in your portfolio)")
    else:
        lines.append(f"⚠️  **Momentum Analysis: {ticker}** (Not in your portfolio)")

    lines.append(f"📅 Data through: {results.calculation_date}")
    lines.append("")

    # RSI Section
    lines.append(f"**RSI (Relative Strength Index): {results.rsi.current_rsi:.1f}**")
    if results.rsi.rsi_signal == "overbought":
        lines.append("- 🔴 Overbought (>70): Potential selling pressure")
    elif results.rsi.rsi_signal == "oversold":
        lines.append("- 🟢 Oversold (<30): Potential buying opportunity")
    else:
        lines.append("- ⚪ Neutral (30-70): No extreme condition")
    lines.append("")

    # MACD Section
    lines.append(f"**MACD: {results.macd.histogram:.2f} Histogram**")
    if results.macd.signal == "bullish":
        lines.append("- 📈 Bullish: MACD above signal line (upward momentum)")
    else:
        lines.append("- 📉 Bearish: MACD below signal line (downward momentum)")
    lines.append("")

    # Stochastic Section
    lines.append(f"**Stochastic: %K={results.stochastic.k_value:.1f}, %D={results.stochastic.d_value:.1f}**")
    if results.stochastic.signal == "overbought":
        lines.append("- 🔴 Overbought (>80): Potential reversal down")
    elif results.stochastic.signal == "oversold":
        lines.append("- 🟢 Oversold (<20): Potential reversal up")
    else:
        lines.append("- ⚪ Neutral (20-80): No extreme condition")
    lines.append("")

    # Williams %R Section
    lines.append(f"**Williams %R: {results.williams_r.williams_r:.1f}**")
    if results.williams_r.signal == "overbought":
        lines.append("- 🔴 Overbought (>-20): Potential sell signal")
    elif results.williams_r.signal == "oversold":
        lines.append("- 🟢 Oversold (<-80): Potential buy signal")
    else:
        lines.append("- ⚪ Neutral (-20 to -80): Range-bound")
    lines.append("")

    # ROC Section
    lines.append(f"**Rate of Change (ROC): {results.roc.roc:+.1f}%**")
    if results.roc.signal == "bullish":
        lines.append(f"- 📈 Bullish: Positive momentum ({results.roc.roc:.1f}% gain)")
    elif results.roc.signal == "bearish":
        lines.append(f"- 📉 Bearish: Negative momentum ({abs(results.roc.roc):.1f}% loss)")
    else:
        lines.append("- ⚪ Neutral: No significant change")
    lines.append("")

    # Confluence Analysis
    lines.append("**🎯 Momentum Confluence**")
    lines.append(f"- Bullish Signals: {confluence['bullish']}/{confluence['total']}")
    lines.append(f"- Bearish Signals: {confluence['bearish']}/{confluence['total']}")
    lines.append("")

    # Recommendation based on confluence
    lines.append("**💡 Interpretation:**")
    if confluence['bullish'] >= 3:
        lines.append(f"✅ **Strong Bullish Confluence** ({confluence['bullish']}/5 indicators)")
        lines.append("Multiple indicators suggest potential upward momentum. Consider this a buying opportunity if position aligns with strategy.")
    elif confluence['bearish'] >= 3:
        lines.append(f"❌ **Strong Bearish Confluence** ({confluence['bearish']}/5 indicators)")
        lines.append("Multiple indicators suggest potential downward pressure. Consider taking profits or tightening stop losses.")
    else:
        lines.append("⚠️  **Mixed Signals: No Clear Confluence**")
        lines.append("Indicators are divided. Wait for clearer signals or use additional analysis before making decisions.")

    return "\n".join(lines)
