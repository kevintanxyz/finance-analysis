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
import logging
import time
import uuid
from datetime import datetime
from typing import Optional

from mcp_server import mcp
from app.database import get_session, Client, Portfolio
from app.parsers import parse_pdf
from app.services.qa_service_llm import QAService
from app.llm import create_llm

# Initialize logger
logger = logging.getLogger(__name__)

# In-memory cache for expensive operations (portfolio optimization)
CACHE: dict = {}
CACHE_DURATION = 300  # 5 minutes in seconds

# Debug: Verify mcp object
import sys as _sys
print(f"[TOOLS DEBUG] mcp object id: {id(mcp)}", file=_sys.stderr)


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
    pdf_base64: str = "",
    pdf_path: str = "",
    filename: str = "valuation.pdf",
    client_id: str = "default",
    enable_llm_validation: bool = False,
) -> dict:
    """
    Parse a portfolio valuation PDF and extract structured financial data.

    **Version 1.3 — File Path Support:**
    - Accepts EITHER base64-encoded PDF OR file path (not both)
    - File path mode is recommended for large PDFs to avoid context limits
    - Automatically detects bank format (WealthPoint, UBS, Julius Baer, etc.)
    - Uses Claude Vision API to extract data intelligently (works with any format)
    - Validates extraction quality with cross-validation
    - Optional LLM validation layer for OCR corrections

    Returns session_id — use this ID in ALL subsequent tool calls to reference
    this portfolio. The portfolio data is persisted in SQLite.

    **Multi-format support:**
    - WealthPoint/Rothschild PDFs ✅
    - UBS PDFs ✅
    - Julius Baer PDFs ✅
    - Generic/unknown formats ✅

    Args:
        pdf_base64: Base64-encoded PDF file (use this OR pdf_path, not both)
        pdf_path: Absolute path to PDF file (recommended for large files)
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
        # Get PDF bytes from either base64 or file path
        if pdf_path and pdf_base64:
            return {
                "error": "Provide either pdf_base64 OR pdf_path, not both",
                "message": "Please specify only one input method",
            }

        if pdf_path:
            # Read from file path (recommended for large PDFs)
            import os
            if not os.path.exists(pdf_path):
                return {
                    "error": f"File not found: {pdf_path}",
                    "message": "Please provide a valid file path",
                }

            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()

            # Extract filename from path if not provided
            if filename == "valuation.pdf":
                filename = os.path.basename(pdf_path)

        elif pdf_base64:
            # Decode from base64 (for small PDFs or frontend uploads)
            pdf_bytes = base64.b64decode(pdf_base64)

        else:
            return {
                "error": "No PDF provided",
                "message": "Please provide either pdf_base64 or pdf_path",
            }

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
            "message": "Failed to parse PDF. Please ensure it's a valid portfolio valuation PDF.",
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
    Get live market data for all listed positions in the portfolio.

    Fetches real-time market data from yfinance for every position with a ticker:
    - Current price and price changes (1d, 5d, 1m)
    - Market fundamentals (PE ratio, dividend yield, beta)
    - Market cap, volume, 52-week high/low

    Returns data formatted as a table with actionable insights.

    Args:
        session_id: Portfolio session ID from upload_portfolio

    Returns:
        Dictionary with market data table and summary KPI cards
    """
    # Load portfolio
    session = get_session()
    portfolio = session.get(Portfolio, session_id)

    if not portfolio:
        return {
            "content": f"Portfolio with session_id '{session_id}' not found.",
            "display_type": "text",
            "error": "Portfolio not found",
        }

    # Parse portfolio data
    from app.models.portfolio import PortfolioData
    portfolio_data = PortfolioData.model_validate_json(portfolio.data_json)

    # Filter listed positions only
    listed_positions = [p for p in portfolio_data.positions if p.ticker and p.is_listed]

    if not listed_positions:
        return {
            "content": "No listed positions found in this portfolio. Market data is only available for positions with tickers (stocks, ETFs).",
            "display_type": "text",
        }

    # Fetch market data for each listed position
    from app.services.market_service import MarketDataService
    market_service = MarketDataService()

    market_data_list = []
    total_value = 0
    total_1d_change_value = 0

    for position in listed_positions:
        analysis = market_service.get_analysis(position)

        # Calculate value change 1d
        value_1d_change = 0
        if analysis.price_change_1d_pct is not None:
            value_1d_change = position.value_chf * (analysis.price_change_1d_pct / 100)
            total_1d_change_value += value_1d_change

        total_value += position.value_chf

        market_data_list.append({
            "ticker": analysis.ticker,
            "name": analysis.name,
            "current_price": analysis.current_price,
            "currency": analysis.currency,
            "value_chf": position.value_chf,
            "weight_pct": position.weight_pct,
            "change_1d_pct": analysis.price_change_1d_pct,
            "change_5d_pct": analysis.price_change_5d_pct,
            "change_1m_pct": analysis.price_change_1m_pct,
            "pe_ratio": analysis.pe_ratio,
            "dividend_yield": analysis.dividend_yield,
            "beta": analysis.beta,
            "market_cap": analysis.market_cap,
            "volume": analysis.volume,
            "52w_high": analysis.fifty_two_week_high,
            "52w_low": analysis.fifty_two_week_low,
            "error": analysis.error,
        })

    # Build summary KPIs
    total_1d_change_pct = (total_1d_change_value / total_value * 100) if total_value > 0 else 0

    kpis = [
        {
            "label": "Listed Positions Value",
            "value": f"CHF {total_value:,.2f}",
            "icon": "trending-up",
        },
        {
            "label": "Today's Change",
            "value": f"CHF {total_1d_change_value:+,.2f}",
            "change": f"{total_1d_change_pct:+.2f}%",
            "change_type": "positive" if total_1d_change_value >= 0 else "negative",
            "icon": "activity",
        },
        {
            "label": "Positions Tracked",
            "value": str(len(listed_positions)),
            "icon": "list",
        },
    ]

    # Build table data
    table_columns = [
        {"key": "ticker", "label": "Ticker", "type": "text"},
        {"key": "name", "label": "Name", "type": "text"},
        {"key": "current_price", "label": "Price", "type": "currency"},
        {"key": "change_1d_pct", "label": "1D %", "type": "percent"},
        {"key": "change_5d_pct", "label": "5D %", "type": "percent"},
        {"key": "change_1m_pct", "label": "1M %", "type": "percent"},
        {"key": "value_chf", "label": "Value CHF", "type": "currency"},
        {"key": "weight_pct", "label": "Weight %", "type": "percent"},
        {"key": "pe_ratio", "label": "P/E", "type": "number"},
        {"key": "dividend_yield", "label": "Div Yield", "type": "percent"},
        {"key": "beta", "label": "Beta", "type": "number"},
    ]

    # Generate insights
    positive_movers = [d for d in market_data_list if d.get("change_1d_pct") and d["change_1d_pct"] > 0]
    negative_movers = [d for d in market_data_list if d.get("change_1d_pct") and d["change_1d_pct"] < 0]

    insights = []
    if positive_movers:
        top_gainer = max(positive_movers, key=lambda x: x["change_1d_pct"])
        insights.append(f"📈 Top gainer today: {top_gainer['ticker']} ({top_gainer['change_1d_pct']:+.2f}%)")

    if negative_movers:
        top_loser = min(negative_movers, key=lambda x: x["change_1d_pct"])
        insights.append(f"📉 Top loser today: {top_loser['ticker']} ({top_loser['change_1d_pct']:+.2f}%)")

    high_pe = [d for d in market_data_list if d.get("pe_ratio") and d["pe_ratio"] > 30]
    if high_pe:
        insights.append(f"⚠️ High P/E ratios (>30): {', '.join([d['ticker'] for d in high_pe])}")

    # Build response
    content_parts = [
        f"Live market data for {len(listed_positions)} listed positions:",
        "",
    ]

    if insights:
        content_parts.append("**Key Insights:**")
        content_parts.extend([f"- {insight}" for insight in insights])
        content_parts.append("")

    content_parts.append("Scroll right to see all metrics (P/E, dividend yield, beta, etc.)")

    return {
        "content": "\n".join(content_parts),
        "display_type": "mixed",
        "kpis": kpis,
        "tables": [{
            "title": "Live Market Data",
            "columns": table_columns,
            "rows": market_data_list,
            "sortable": True,
        }],
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


@mcp.tool()
async def analyze_correlation(
    session_id: str,
    tickers: list[str],
    days: int = 90,
) -> dict:
    """
    Calculate portfolio correlation matrix and diversification analysis.

    Calculates: Correlation matrix, Covariance matrix, Diversification score,
    Concentration risk warnings, Pairwise correlations.

    BUSINESS VALUE:
    - Assess portfolio diversification quality
    - Identify concentration risks (highly correlated positions)
    - Find hedge opportunities (negative correlations)
    - Understand how portfolio behaves during market stress

    Args:
        session_id: Portfolio session ID
        tickers: List of stock tickers to analyze (minimum 2, e.g., ["AAPL", "NVDA", "TSLA"])
        days: Historical period in trading days (default: 90, ~3 months)

    Returns:
        Correlation matrix + diversification metrics as KPI cards + interpretation

    Example:
        analyze_correlation("abc-123", ["ROG.SW", "NESN.SW", "NOVN.SW"], 252)  # 1-year Swiss portfolio
        analyze_correlation("abc-123", ["AAPL", "NVDA", "TSLA"], 90)  # 3-month tech portfolio
    """
    try:
        # Validate input
        if len(tickers) < 2:
            return {
                "content": "Correlation analysis requires at least 2 tickers. Please provide 2 or more assets.",
                "display_type": "text",
                "error": "Insufficient tickers (need at least 2)"
            }

        # ✨ IMPROVEMENT: Check cache first (5-minute TTL)
        from app.services.analysis_cache import AnalysisCacheService

        # Create cache key from sorted tickers for consistency
        cache_key = ",".join(sorted(tickers))
        cache_params = {
            "tickers": cache_key,
            "days": days,
        }

        cached_result = AnalysisCacheService.get_cached_result(
            portfolio_id=session_id,
            analysis_type="correlation",
            ticker=cache_key,  # Use sorted ticker list as key
            parameters=cache_params,
        )

        if cached_result:
            # Cache hit - return immediately
            cached_result["_from_cache"] = True
            cached_result["_cache_note"] = "⚡ Using cached result (< 5 min old)"
            return cached_result

        # Cache miss - proceed with calculation
        # Load portfolio (optional verification)
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

            # Check which tickers are in the portfolio
            portfolio_tickers = {p.ticker for p in portfolio_data.positions if p.ticker}
            tickers_in_portfolio = [t for t in tickers if t in portfolio_tickers]
            tickers_not_in_portfolio = [t for t in tickers if t not in portfolio_tickers]

        # Fetch synchronized portfolio data from yfinance
        from app.analysis.correlation_calculator import CorrelationCalculator
        from app.models.analysis import CorrelationConfig

        calculator = CorrelationCalculator(
            CorrelationConfig(
                method="pearson",
                rolling_window=None,  # Full period correlation
                min_periods=30,
            )
        )

        # Fetch synchronized data for all tickers
        portfolio_price_data = await calculator.fetch_portfolio_data_from_yfinance(
            tickers, days
        )

        # Calculate correlation analysis
        results = await calculator.calculate_portfolio_correlation(portfolio_price_data)

        # Build KPI cards for frontend
        kpis = [
            {
                "label": "Diversification Score",
                "value": f"{results.diversification_score:.2f}",
                "change": _interpret_diversification(results.diversification_score),
                "change_type": _diversification_change_type(results.diversification_score),
                "icon": "shield"
            },
            {
                "label": "Average Correlation",
                "value": f"{results.correlation_matrix.average_correlation:.2f}",
                "change": f"Portfolio-wide correlation",
                "change_type": "negative" if results.concentration_warning else "positive",
                "icon": "link"
            },
            {
                "label": "Concentration Risk",
                "value": "⚠️ High" if results.concentration_warning else "✓ Low",
                "change": f"Avg corr: {results.correlation_matrix.average_correlation:.2f}",
                "change_type": "negative" if results.concentration_warning else "positive",
                "icon": "alert-triangle" if results.concentration_warning else "check-circle"
            },
            {
                "label": "Assets Analyzed",
                "value": f"{len(results.tickers)}",
                "change": f"{len(tickers_in_portfolio)} in portfolio",
                "change_type": "neutral",
                "icon": "bar-chart"
            },
        ]

        # Find highest correlation pair (for interpretation)
        highest_corr = -2.0
        highest_pair = None
        lowest_corr = 2.0
        lowest_pair = None

        for i, ticker1 in enumerate(results.tickers):
            for j, ticker2 in enumerate(results.tickers):
                if i < j:
                    corr = results.correlation_matrix.correlation_matrix[ticker1][ticker2]
                    if corr > highest_corr:
                        highest_corr = corr
                        highest_pair = (ticker1, ticker2)
                    if corr < lowest_corr:
                        lowest_corr = corr
                        lowest_pair = (ticker1, ticker2)

        # Build interpretation text
        interpretation = _build_correlation_interpretation(
            results,
            tickers,
            tickers_in_portfolio,
            tickers_not_in_portfolio,
            highest_pair,
            highest_corr,
            lowest_pair,
            lowest_corr,
        )

        response = {
            "content": interpretation,
            "display_type": "mixed",
            "kpis": kpis,
            "correlation_data": {
                "tickers": results.tickers,
                "calculation_date": str(results.calculation_date),
                "correlation_matrix": results.correlation_matrix.correlation_matrix,
                "average_correlation": results.correlation_matrix.average_correlation,
                "diversification_score": results.diversification_score,
                "concentration_warning": results.concentration_warning,
                "covariance_matrix": results.covariance_matrix.covariance_matrix,
                "highest_correlation": {
                    "pair": highest_pair,
                    "value": highest_corr,
                } if highest_pair else None,
                "lowest_correlation": {
                    "pair": lowest_pair,
                    "value": lowest_corr,
                } if lowest_pair else None,
            },
        }

        # ✨ IMPROVEMENT: Save to cache (5-min TTL)
        AnalysisCacheService.save_result(
            portfolio_id=session_id,
            analysis_type="correlation",
            result=response,
            ticker=cache_key,
            parameters=cache_params,
        )

        return response

    except ValueError as e:
        return {
            "content": f"Unable to fetch data for {', '.join(tickers)}: {str(e)}",
            "display_type": "text",
            "error": str(e)
        }
    except Exception as e:
        return {
            "content": f"Error analyzing correlation: {str(e)}",
            "display_type": "text",
            "error": str(e)
        }


# ────────────────────────────────────────────────────────────────────────────
# Helper functions for correlation interpretation
# ────────────────────────────────────────────────────────────────────────────

def _interpret_diversification(score: float) -> str:
    """Interpret diversification score for business users."""
    if score > 0.6:
        return "Excellent diversification"
    elif score > 0.4:
        return "Good diversification"
    elif score > 0.2:
        return "Moderate diversification"
    else:
        return "Poor diversification"


def _diversification_change_type(score: float) -> str:
    """Convert diversification score to change_type for KPI cards."""
    if score > 0.6:
        return "positive"
    elif score > 0.4:
        return "neutral"
    else:
        return "negative"


def _build_correlation_interpretation(
    results,
    tickers: list[str],
    tickers_in_portfolio: list[str],
    tickers_not_in_portfolio: list[str],
    highest_pair: tuple,
    highest_corr: float,
    lowest_pair: tuple,
    lowest_corr: float,
) -> str:
    """Build business-friendly interpretation of correlation analysis."""
    lines = []

    # Header
    lines.append(f"**📊 Correlation & Diversification Analysis**")
    lines.append(f"📅 Data through: {results.calculation_date}")
    lines.append(f"🔗 Analyzing {len(results.tickers)} assets: {', '.join(results.tickers)}")

    if tickers_in_portfolio:
        lines.append(f"✅ In your portfolio: {', '.join(tickers_in_portfolio)}")
    if tickers_not_in_portfolio:
        lines.append(f"⚠️  Not in your portfolio: {', '.join(tickers_not_in_portfolio)}")

    lines.append("")

    # Diversification Score
    div_rating = _interpret_diversification(results.diversification_score)
    lines.append(f"**🎯 Diversification Score: {results.diversification_score:.2f}** ({div_rating})")

    if results.diversification_score > 0.6:
        lines.append("- ✅ Excellent diversification! Your assets have low correlation, providing good protection against market moves.")
    elif results.diversification_score > 0.4:
        lines.append("- 🟢 Good diversification. Consider adding more uncorrelated assets for further risk reduction.")
    elif results.diversification_score > 0.2:
        lines.append("- 🟡 Moderate diversification. The assets are somewhat correlated - consider adding uncorrelated positions.")
    else:
        lines.append("- 🔴 Poor diversification! The assets are highly correlated and will likely move together during market stress.")

    lines.append("")

    # Average Correlation
    lines.append(f"**📈 Average Correlation: {results.correlation_matrix.average_correlation:.2f}**")

    if results.concentration_warning:
        lines.append(f"- ⚠️  **Concentration Risk Alert**: Average correlation >{0.7:.1f} indicates your positions tend to move together.")
        lines.append("- This reduces diversification benefits during market downturns.")
    else:
        lines.append("- ✅ No concentration risk detected. Your positions show healthy independence.")

    lines.append("")

    # Pairwise Correlation Highlights
    lines.append("**🔍 Key Correlations**")

    # Highest correlation
    if highest_pair:
        ticker1, ticker2 = highest_pair
        lines.append(f"- **Highest**: {ticker1} vs {ticker2} = {highest_corr:.2f}")
        if highest_corr > 0.7:
            lines.append(f"  → Strong positive correlation (move together)")
        elif highest_corr > 0.5:
            lines.append(f"  → Moderate positive correlation")
        elif highest_corr > 0.3:
            lines.append(f"  → Weak positive correlation")
        else:
            lines.append(f"  → Low correlation (mostly independent)")

    # Lowest correlation
    if lowest_pair:
        ticker1, ticker2 = lowest_pair
        lines.append(f"- **Lowest**: {ticker1} vs {ticker2} = {lowest_corr:.2f}")
        if lowest_corr < -0.3:
            lines.append(f"  → 🛡️ Negative correlation (natural hedge!)")
        elif lowest_corr < 0.0:
            lines.append(f"  → Slight negative correlation (mild hedge)")
        else:
            lines.append(f"  → Low positive correlation (independent)")

    lines.append("")

    # Correlation Matrix Display
    lines.append("**📊 Correlation Matrix**")
    lines.append("```")

    # Header row
    header = "        "
    for ticker in results.tickers:
        header += f"{ticker:>8}"
    lines.append(header)

    # Matrix rows
    for ticker1 in results.tickers:
        row = f"{ticker1:>8}"
        for ticker2 in results.tickers:
            corr = results.correlation_matrix.correlation_matrix[ticker1][ticker2]
            row += f"{corr:>8.2f}"
        lines.append(row)

    lines.append("```")
    lines.append("")

    # Recommendations
    lines.append("**💡 Interpretation:**")

    if results.diversification_score > 0.6:
        lines.append("Your portfolio demonstrates excellent diversification. The low correlation between")
        lines.append("assets provides robust protection during market volatility. Continue monitoring to")
        lines.append("ensure diversification is maintained as market conditions change.")
    elif results.diversification_score > 0.4:
        lines.append("Your portfolio shows good diversification, though there's room for improvement.")
        lines.append("Consider adding assets with negative or low correlation to your existing positions")
        lines.append("to further reduce portfolio risk.")
    elif results.diversification_score > 0.2:
        lines.append("Your portfolio has moderate diversification. Several positions move together,")
        lines.append("which could amplify losses during market downturns. Consider rebalancing toward")
        lines.append("uncorrelated or negatively correlated assets.")
    else:
        lines.append("⚠️  **Portfolio Concentration Risk**: Your positions are highly correlated and will")
        lines.append("likely move together during market stress. This significantly reduces diversification")
        lines.append("benefits. Strongly consider adding uncorrelated assets or hedges to reduce risk.")

    return "\n".join(lines)


@mcp.tool()
async def price_options(
    session_id: str,
    ticker: str,
    strike: float,
    days_to_expiry: int,
    option_type: str = "call",
    volatility_days: int = 90,
    risk_free_rate: float = 0.045,
    dividend_yield: float = 0.0,
) -> dict:
    """
    Calculate option price and Greeks using Black-Scholes model.

    Calculates: Theoretical option price, Delta, Gamma, Theta, Vega, Rho,
    Intrinsic value, Time value, Moneyness classification.

    BUSINESS VALUE:
    - Price options for hedging strategies (protective puts, covered calls)
    - Understand option sensitivities (Greeks) for risk management
    - Compare theoretical value vs market price for trading opportunities
    - Plan options strategies with clear risk/reward metrics

    Args:
        session_id: Portfolio session ID
        ticker: Stock ticker (e.g., "AAPL", "ROG.SW")
        strike: Option strike price
        days_to_expiry: Days until option expiration
        option_type: "call" or "put" (default: "call")
        volatility_days: Days to calculate historical volatility (default: 90)
        risk_free_rate: Annual risk-free rate (default: 0.045 = 4.5%)
        dividend_yield: Annual dividend yield (default: 0.0 = 0%)

    Returns:
        Option price, Greeks, and business interpretation

    Example:
        price_options("abc-123", "AAPL", 175.0, 30, "put")  # 30-day protective put
        price_options("abc-123", "NVDA", 500.0, 60, "call")  # 60-day call option
    """
    try:
        # Validate option type
        if option_type not in ["call", "put"]:
            return {
                "content": f"Invalid option_type '{option_type}'. Must be 'call' or 'put'.",
                "display_type": "text",
                "error": "Invalid option type"
            }

        # ✨ IMPROVEMENT: Check cache first (5-minute TTL)
        from app.services.analysis_cache import AnalysisCacheService

        cache_params = {
            "strike": strike,
            "days_to_expiry": days_to_expiry,
            "option_type": option_type,
            "volatility_days": volatility_days,
            "risk_free_rate": risk_free_rate,
            "dividend_yield": dividend_yield,
        }

        cached_result = AnalysisCacheService.get_cached_result(
            portfolio_id=session_id,
            analysis_type="options_pricing",
            ticker=ticker,
            parameters=cache_params,
        )

        if cached_result:
            # Cache hit - return immediately
            cached_result["_from_cache"] = True
            cached_result["_cache_note"] = "⚡ Using cached result (< 5 min old)"
            return cached_result

        # Cache miss - proceed with calculation
        # Load portfolio to verify it exists
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

        # Fetch stock data from yfinance
        from app.analysis.options_calculator import OptionsCalculator
        from app.models.analysis import BlackScholesInput

        calculator = OptionsCalculator()

        # Fetch current price and historical volatility
        current_price, historical_vol = await calculator.fetch_stock_data_for_options(
            ticker, volatility_days
        )

        # Create Black-Scholes input
        bs_input = BlackScholesInput(
            spot_price=current_price,
            strike=strike,
            time_to_expiry=days_to_expiry / 365,  # Convert days to years
            volatility=historical_vol,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            option_type=option_type,  # type: ignore
        )

        # Calculate option price and Greeks
        results = await calculator.price_option(bs_input, ticker)

        # Build KPI cards for frontend
        kpis = [
            {
                "label": "Option Price",
                "value": f"${results.option_price:.2f}",
                "change": f"{results.moneyness} ({_interpret_moneyness(results.moneyness, option_type)})",
                "change_type": "neutral",
                "icon": "dollar-sign"
            },
            {
                "label": "Delta",
                "value": f"{results.delta:.3f}",
                "change": _interpret_delta(results.delta, option_type),
                "change_type": "neutral",
                "icon": "trending-up"
            },
            {
                "label": "Theta (Daily Decay)",
                "value": f"${results.theta:.2f}",
                "change": f"Loses {abs(results.theta):.2f}/day",
                "change_type": "negative",
                "icon": "clock"
            },
            {
                "label": "Vega (Vol Sensitivity)",
                "value": f"${results.vega:.2f}",
                "change": f"Per 1% vol change",
                "change_type": "neutral",
                "icon": "activity"
            },
        ]

        # Build interpretation text
        interpretation = _build_options_interpretation(
            results,
            ticker,
            current_price,
            strike,
            days_to_expiry,
            option_type,
            position_in_portfolio,
        )

        response = {
            "content": interpretation,
            "display_type": "mixed",
            "kpis": kpis,
            "options_data": {
                "ticker": ticker,
                "calculation_date": str(results.calculation_date),
                "option_type": option_type,
                "option_price": results.option_price,
                "intrinsic_value": results.intrinsic_value,
                "time_value": results.time_value,
                "greeks": {
                    "delta": results.delta,
                    "gamma": results.gamma,
                    "theta": results.theta,
                    "vega": results.vega,
                    "rho": results.rho,
                },
                "moneyness": results.moneyness,
                "inputs": {
                    "spot_price": current_price,
                    "strike": strike,
                    "days_to_expiry": days_to_expiry,
                    "volatility": historical_vol,
                    "risk_free_rate": risk_free_rate,
                    "dividend_yield": dividend_yield,
                },
            },
        }

        # ✨ IMPROVEMENT: Save to cache (5-min TTL)
        AnalysisCacheService.save_result(
            portfolio_id=session_id,
            analysis_type="options_pricing",
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
            "content": f"Error calculating option price for {ticker}: {str(e)}",
            "display_type": "text",
            "error": str(e)
        }


# ────────────────────────────────────────────────────────────────────────────
# Helper functions for options interpretation
# ────────────────────────────────────────────────────────────────────────────

def _interpret_moneyness(moneyness: str, option_type: str) -> str:
    """Interpret moneyness for business users."""
    if moneyness == "ITM":
        return "In the money" if option_type == "call" else "In the money"
    elif moneyness == "ATM":
        return "At the money"
    else:
        return "Out of the money"


def _interpret_delta(delta: float, option_type: str) -> str:
    """Interpret delta for business users."""
    abs_delta = abs(delta)
    if abs_delta > 0.7:
        return f"Deep {option_type.upper()} (moves with stock)"
    elif abs_delta > 0.5:
        return f"Strong {option_type.upper()} exposure"
    elif abs_delta > 0.3:
        return f"Moderate {option_type.upper()} exposure"
    else:
        return "Low probability/weak exposure"


def _build_options_interpretation(
    results,
    ticker: str,
    current_price: float,
    strike: float,
    days_to_expiry: int,
    option_type: str,
    position_in_portfolio: bool,
) -> str:
    """Build business-friendly interpretation of option pricing."""
    lines = []

    # Header
    if position_in_portfolio:
        lines.append(f"✅ **Options Analysis: {ticker} {option_type.upper()}** (Position in your portfolio)")
    else:
        lines.append(f"⚠️  **Options Analysis: {ticker} {option_type.upper()}** (Not in your portfolio)")

    lines.append(f"📅 Calculation Date: {results.calculation_date}")
    lines.append(f"💱 Current Price: ${current_price:.2f}")
    lines.append("")

    # Option Basics
    lines.append(f"**📋 Option Specifications**")
    lines.append(f"- Type: {option_type.upper()} option")
    lines.append(f"- Strike Price: ${strike:.2f}")
    lines.append(f"- Days to Expiry: {days_to_expiry} days ({days_to_expiry/365:.2f} years)")
    lines.append(f"- Moneyness: {results.moneyness} ({_interpret_moneyness(results.moneyness, option_type)})")
    lines.append("")

    # Pricing Breakdown
    lines.append(f"**💰 Option Pricing**")
    lines.append(f"- Theoretical Price: ${results.option_price:.2f}")
    lines.append(f"- Intrinsic Value: ${results.intrinsic_value:.2f}")
    lines.append(f"- Time Value: ${results.time_value:.2f}")
    if results.time_value > results.intrinsic_value:
        lines.append(f"  → Mostly time value (will decay as expiry approaches)")
    else:
        lines.append(f"  → Mostly intrinsic value (less time decay risk)")
    lines.append("")

    # Greeks Explanation
    lines.append(f"**📊 Greeks (Sensitivities)**")
    lines.append(f"- **Delta: {results.delta:.3f}** - ${abs(results.delta):.2f} option move per $1 stock move")
    lines.append(f"  → {_interpret_delta(results.delta, option_type)}")
    lines.append(f"- **Gamma: {results.gamma:.4f}** - Delta changes by {results.gamma:.4f} per $1 stock move")
    if results.gamma > 0.02:
        lines.append(f"  → High gamma: Delta changes rapidly (near ATM or near expiry)")
    else:
        lines.append(f"  → Low gamma: Delta is relatively stable")
    lines.append(f"- **Theta: ${results.theta:.2f}/day** - Loses ${abs(results.theta):.2f} per day from time decay")
    if abs(results.theta) > 0.05:
        lines.append(f"  → High time decay: Monitor closely as expiry approaches")
    else:
        lines.append(f"  → Low time decay: Longer-dated option")
    lines.append(f"- **Vega: ${results.vega:.2f}** - ${abs(results.vega):.2f} change per 1% volatility change")
    if results.vega > 0.15:
        lines.append(f"  → High vega: Very sensitive to volatility changes")
    else:
        lines.append(f"  → Low vega: Less affected by volatility")
    lines.append("")

    # Trading Insights
    lines.append(f"**💡 Insights & Recommendations**")

    if option_type == "call":
        lines.append(f"**Call Option Strategy:**")
        if results.moneyness == "OTM":
            lines.append(f"- This is a speculative bet that {ticker} will rise above ${strike:.2f}")
            lines.append(f"- Currently ${abs(current_price - strike):.2f} out of the money")
            lines.append(f"- Risk: Option expires worthless if stock stays below ${strike:.2f}")
        elif results.moneyness == "ATM":
            lines.append(f"- Stock is near the strike price - option is sensitive to moves")
            lines.append(f"- High gamma means delta will change rapidly with stock price")
        else:
            lines.append(f"- This is an in-the-money call with ${results.intrinsic_value:.2f} intrinsic value")
            lines.append(f"- Moves closely with the stock (Delta: {results.delta:.2f})")
    else:
        lines.append(f"**Put Option Strategy:**")
        if results.moneyness == "OTM":
            lines.append(f"- Protective put: Insurance against downside below ${strike:.2f}")
            lines.append(f"- Currently ${abs(current_price - strike):.2f} out of the money")
            lines.append(f"- Cost: ${results.option_price:.2f} per share (${results.option_price * 100:.0f} per contract)")
        elif results.moneyness == "ATM":
            lines.append(f"- Stock is near the strike - option is very sensitive to moves")
            lines.append(f"- Good hedge level for current price protection")
        else:
            lines.append(f"- This is an in-the-money put with ${results.intrinsic_value:.2f} intrinsic value")
            lines.append(f"- Already has protection value")

    lines.append("")
    lines.append(f"**⏰ Time Decay:**")
    days_until_30pct_decay = abs(0.30 * results.option_price / results.theta) if results.theta < 0 else 999
    if days_until_30pct_decay < days_to_expiry:
        lines.append(f"- In ~{int(days_until_30pct_decay)} days, option will lose ~30% of time value to decay")
    lines.append(f"- Total time decay until expiry: ${abs(results.theta * days_to_expiry):.2f}")

    lines.append("")
    lines.append("**⚠️  DISCLAIMER:** This is a theoretical price based on Black-Scholes model.")
    lines.append("Actual market prices may differ due to supply/demand, market sentiment, and other factors.")
    lines.append("Options involve substantial risk and are not suitable for all investors.")

    return "\n".join(lines)


# ============================================================================
# Portfolio Optimization Tool (Phase 2.5)
# ============================================================================


@mcp.tool()
async def optimize_portfolio(
    session_id: str,
    tickers: list[str],
    method: str = "max_sharpe",
    days: int = 252,
    max_position: float = 1.0,
    target_return: float | None = None,
    views: dict[str, float] | None = None,
) -> dict:
    """
    Optimize portfolio allocation using Modern Portfolio Theory.

    WHAT: Calculates optimal asset weights for given portfolio
    WHY: Scientific portfolio construction for maximum risk-adjusted returns
    WHEN TO USE: Before capital deployment or portfolio rebalancing

    Args:
        session_id: Session ID for tracking
        tickers: List of asset ticker symbols (minimum 2)
        method: Optimization method - one of:
            - "max_sharpe": Maximum risk-adjusted return (default, aggressive)
            - "min_variance": Minimum risk (defensive, capital preservation)
            - "risk_parity": Equal risk contribution (all-weather, balanced)
            - "mean_variance": Target return with minimum risk
            - "black_litterman": Market equilibrium + investor views
        days: Days of historical data (default: 252 = 1 year)
        max_position: Maximum position size per asset 0.0-1.0 (default: 1.0 = no limit)
        target_return: Target annual return for mean_variance (e.g., 0.12 = 12%)
        views: Investor views for black_litterman (e.g., {"AAPL": 0.15, "NVDA": 0.20})

    Returns:
        Dict with:
            - success: bool
            - data: Optimization results and allocation
            - kpis: Key performance indicators
            - interpretation: Business-friendly analysis

    Examples:
        # Aggressive growth
        await optimize_portfolio(session_id, ["AAPL", "NVDA", "TSLA", "SPY"], method="max_sharpe")

        # Defensive portfolio
        await optimize_portfolio(session_id, ["SPY", "BND", "AAPL"], method="min_variance")

        # Diversified (max 25% per position)
        await optimize_portfolio(session_id, ["AAPL", "NVDA", "TSLA", "SPY"],
                                method="max_sharpe", max_position=0.25)

        # With return target
        await optimize_portfolio(session_id, ["AAPL", "NVDA", "TSLA"],
                                method="mean_variance", target_return=0.15)
    """
    logger.info(f"[{session_id}] Portfolio optimization request: {tickers}, method={method}")

    try:
        # Validate inputs
        if len(tickers) < 2:
            return {
                "success": False,
                "error": "Portfolio optimization requires at least 2 assets",
            }

        # Check cache
        cache_key = f"portfolio_{'-'.join(sorted(tickers))}_{method}_{max_position}_{days}"
        if cache_key in CACHE:
            cached_data = CACHE[cache_key]
            if time.time() - cached_data["timestamp"] < CACHE_DURATION:
                logger.info(f"[{session_id}] Using cached portfolio optimization")
                return cached_data["data"]

        # Fetch portfolio data
        from app.analysis.portfolio_optimizer import PortfolioOptimizer
        from app.models.analysis import OptimizationConfig

        logger.info(f"[{session_id}] Fetching {days} days of data for {len(tickers)} assets...")
        data = await PortfolioOptimizer.fetch_portfolio_data(tickers, days=days)

        # Configure optimization
        config = OptimizationConfig(
            method=method,
            risk_free_rate=0.045,
            position_limits=(0.0, max_position),
            target_return=target_return,
            views=views,
        )

        # Run optimization
        logger.info(f"[{session_id}] Running {method} optimization...")
        optimizer = PortfolioOptimizer(config)
        result = await optimizer.optimize(data)

        logger.info(f"[{session_id}] Optimization complete: Sharpe={result.sharpe_ratio:.2f}")

        # Build KPI cards
        kpis = [
            {
                "label": "Expected Return",
                "value": f"{result.expected_return:.2%}",
                "sublabel": "Annual (estimated)",
                "trend": "up" if result.expected_return > 0.10 else "neutral",
            },
            {
                "label": "Expected Volatility",
                "value": f"{result.expected_volatility:.2%}",
                "sublabel": "Annual (risk)",
                "trend": "down" if result.expected_volatility < 0.25 else "up",
            },
            {
                "label": "Sharpe Ratio",
                "value": f"{result.sharpe_ratio:.2f}",
                "sublabel": "Return per unit risk",
                "trend": (
                    "up" if result.sharpe_ratio > 1.0 else (
                        "neutral" if result.sharpe_ratio > 0.5 else "down"
                    )
                ),
            },
            {
                "label": "Diversification Ratio",
                "value": f"{result.diversification_ratio:.2f}",
                "sublabel": "Portfolio benefit",
                "trend": "up" if result.diversification_ratio > 1.3 else "neutral",
            },
        ]

        # Build interpretation
        interpretation = _build_portfolio_interpretation(result, tickers, method, max_position)

        # Response data
        response_data = {
            "success": True,
            "data": {
                "method": result.method,
                "tickers": result.tickers,
                "optimal_weights": result.optimal_weights,
                "expected_return": result.expected_return,
                "expected_volatility": result.expected_volatility,
                "sharpe_ratio": result.sharpe_ratio,
                "diversification_ratio": result.diversification_ratio,
                "data_period": {
                    "start_date": str(data.dates[0]),
                    "end_date": str(data.dates[-1]),
                    "days": len(data.dates),
                },
            },
            "kpis": kpis,
            "interpretation": interpretation,
        }

        # Cache results
        CACHE[cache_key] = {"timestamp": time.time(), "data": response_data}

        return response_data

    except Exception as e:
        logger.error(f"[{session_id}] Portfolio optimization error: {e}")
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e)}


def _build_portfolio_interpretation(
    result, tickers: list[str], method: str, max_position: float
) -> str:
    """
    Build business-friendly interpretation of portfolio optimization.

    Args:
        result: OptimizationOutput
        tickers: List of tickers
        method: Optimization method used
        max_position: Position limit

    Returns:
        Markdown formatted interpretation
    """
    lines = []

    # Header
    lines.append(f"# 📊 Portfolio Optimization Results")
    lines.append("")
    lines.append(f"**Method:** {result.method.replace('_', ' ').title()}")
    lines.append(f"**Assets:** {', '.join(tickers)}")
    lines.append("")

    # Performance Metrics
    lines.append("## 📈 Expected Performance")
    lines.append("")
    lines.append(f"- **Annual Return:** {result.expected_return:.2%}")
    lines.append(f"- **Annual Volatility:** {result.expected_volatility:.2%}")
    lines.append(f"- **Sharpe Ratio:** {result.sharpe_ratio:.2f}")
    lines.append(f"- **Diversification Ratio:** {result.diversification_ratio:.2f}")
    lines.append("")

    # Sharpe interpretation
    if result.sharpe_ratio > 2.0:
        sharpe_label = "**EXCELLENT** - Outstanding risk-adjusted returns"
    elif result.sharpe_ratio > 1.0:
        sharpe_label = "**GOOD** - Solid risk-adjusted returns"
    elif result.sharpe_ratio > 0.5:
        sharpe_label = "**FAIR** - Acceptable but could improve"
    else:
        sharpe_label = "**POOR** - Not enough return for risk taken"

    lines.append(f"**Sharpe Ratio Assessment:** {sharpe_label}")
    lines.append("")

    # Diversification interpretation
    if result.diversification_ratio > 1.8:
        div_label = "**EXCELLENT** - Strong diversification benefit"
    elif result.diversification_ratio > 1.4:
        div_label = "**GOOD** - Meaningful diversification"
    elif result.diversification_ratio > 1.2:
        div_label = "**MODERATE** - Some diversification"
    else:
        div_label = "**LIMITED** - Concentrated portfolio"

    lines.append(f"**Diversification Assessment:** {div_label}")
    lines.append("")

    # Optimal Allocation
    lines.append("## 💰 Optimal Allocation")
    lines.append("")
    lines.append("| Asset | Weight | $100k Portfolio |")
    lines.append("|-------|--------|----------------|")

    sorted_weights = sorted(
        result.optimal_weights.items(), key=lambda x: x[1], reverse=True
    )

    for ticker, weight in sorted_weights:
        allocation = weight * 100000
        lines.append(f"| **{ticker}** | {weight:.2%} | ${allocation:,.0f} |")

    lines.append(f"| **TOTAL** | {sum(result.optimal_weights.values()):.2%} | $100,000 |")
    lines.append("")

    # Position limits check
    max_weight = max(result.optimal_weights.values())
    if max_weight > 0.40:
        lines.append("⚠️  **Concentration Risk:** Largest position exceeds 40% of portfolio.")
        lines.append("   Consider using position limits (max_position) for better diversification.")
        lines.append("")

    # Method-specific guidance
    lines.append("## 🎯 Strategy Guidance")
    lines.append("")

    if method == "max_sharpe":
        lines.append("**Maximum Sharpe Ratio Strategy:**")
        lines.append("- **Goal:** Best risk-adjusted returns (aggressive growth)")
        lines.append("- **Character:** May concentrate in highest-performing assets")
        lines.append("- **Best for:** Growth-oriented investors comfortable with concentration")
        lines.append("- **Rebalance:** Quarterly or when weights drift >5%")

    elif method == "min_variance":
        lines.append("**Minimum Variance Strategy:**")
        lines.append("- **Goal:** Lowest risk allocation (defensive)")
        lines.append("- **Character:** Favors stable, low-volatility assets")
        lines.append("- **Best for:** Conservative investors, capital preservation")
        lines.append("- **Rebalance:** Semi-annually or during high volatility")

    elif method == "risk_parity":
        lines.append("**Risk Parity Strategy:**")
        lines.append("- **Goal:** Equal risk contribution from each asset")
        lines.append("- **Character:** \"All-weather\" portfolio, stable across regimes")
        lines.append("- **Best for:** Balanced exposure without return forecasts")
        lines.append("- **Rebalance:** Annually or when risk contributions drift >10%")

    elif method == "mean_variance":
        lines.append("**Mean-Variance Strategy:**")
        lines.append("- **Goal:** Target return with minimum risk")
        lines.append("- **Character:** Balances return target vs risk")
        lines.append("- **Best for:** Investors with specific return goals")
        lines.append("- **Rebalance:** Quarterly")

    elif method == "black_litterman":
        lines.append("**Black-Litterman Strategy:**")
        lines.append("- **Goal:** Market equilibrium + your views")
        lines.append("- **Character:** Incorporates specific investment opinions")
        lines.append("- **Best for:** Investors with strong convictions on certain assets")
        lines.append("- **Rebalance:** When views change or quarterly")

    lines.append("")

    # Action items
    lines.append("## ✅ Implementation Checklist")
    lines.append("")
    lines.append("1. **Review Allocation:** Ensure alignment with risk tolerance and goals")
    lines.append("2. **Check Current Prices:** Verify prices before executing trades")
    lines.append("3. **Consider Tax Impact:** Account for capital gains/losses")
    lines.append("4. **Use Limit Orders:** Minimize slippage on large positions")
    lines.append("5. **Set Rebalancing Schedule:** Calendar reminders based on strategy")
    lines.append("6. **Monitor Performance:** Track actual vs expected returns")
    lines.append("")

    # Disclaimers
    lines.append("---")
    lines.append("")
    lines.append("**⚠️  Important Disclaimers:**")
    lines.append("")
    lines.append("- Expected returns and volatilities are **estimates** based on historical data")
    lines.append("- Past performance **does not guarantee** future results")
    lines.append("- Optimization assumes **normal market conditions** (not crashes/bubbles)")
    lines.append("- **Rebalance periodically** as market conditions change")
    lines.append("- Consult a **financial advisor** before making investment decisions")

    return "\n".join(lines)


# ────────────────────────────────────────────────────────────────────────────
# NEW PORTFOLIO-LEVEL TOOLS
# ────────────────────────────────────────────────────────────────────────────


@mcp.tool()
async def get_portfolio_allocation(session_id: str) -> dict:
    """
    Get portfolio allocation aggregated by asset class.

    Returns breakdown by asset classes (Equities, Bonds, Cash, Others, etc.)
    with values and percentages.

    Args:
        session_id: Portfolio session ID

    Returns:
        Dict with allocation by asset class, KPIs, and pie chart data

    Example:
        allocation = await get_portfolio_allocation("abc123")
        # Returns: Equities 38%, Bonds 18%, etc.
    """
    logger.info(f"[{session_id}] Getting portfolio allocation by asset class")

    try:
        with get_session() as db_session:
            portfolio = db_session.get(Portfolio, session_id)
            if not portfolio:
                return {
                    "success": False,
                    "error": f"Portfolio {session_id} not found.",
                    "display_type": "text"
                }

            # Parse portfolio data
            from app.models.portfolio import PortfolioData
            portfolio_data = PortfolioData.model_validate_json(portfolio.data_json)

            # Aggregate by asset class
            allocation_by_class = {}
            for position in portfolio_data.positions:
                asset_class = position.asset_class or "Unclassified"
                value_chf = position.value_chf or 0.0

                if asset_class not in allocation_by_class:
                    allocation_by_class[asset_class] = 0.0
                allocation_by_class[asset_class] += value_chf

            # Calculate total and percentages
            total_value = sum(allocation_by_class.values())

            if total_value == 0:
                return {
                    "success": False,
                    "error": "Portfolio has zero total value.",
                    "display_type": "text"
                }

            # Build allocation list sorted by value descending
            allocation_list = []
            for asset_class, value_chf in sorted(
                allocation_by_class.items(),
                key=lambda x: x[1],
                reverse=True
            ):
                weight_pct = (value_chf / total_value) * 100
                allocation_list.append({
                    "asset_class": asset_class,
                    "value_chf": round(value_chf, 2),
                    "weight_pct": round(weight_pct, 2)
                })

            # Build KPIs
            kpis = [
                {
                    "label": "Total Value",
                    "value": f"CHF {total_value:,.2f}",
                    "icon": "dollar-sign"
                },
                {
                    "label": "Asset Classes",
                    "value": str(len(allocation_by_class)),
                    "icon": "layers"
                },
                {
                    "label": "Positions",
                    "value": str(len(portfolio_data.positions)),
                    "icon": "briefcase"
                }
            ]

            # Build table data
            table_data = {
                "headers": ["Asset Class", "Value (CHF)", "Weight (%)"],
                "rows": [
                    [
                        item["asset_class"],
                        f"CHF {item['value_chf']:,.2f}",
                        f"{item['weight_pct']:.1f}%"
                    ]
                    for item in allocation_list
                ]
            }

            return {
                "success": True,
                "content": f"Portfolio allocation for {len(portfolio_data.positions)} positions across {len(allocation_by_class)} asset classes.",
                "display_type": "mixed",
                "kpis": kpis,
                "allocation": allocation_list,
                "table": table_data,
                "total_value_chf": total_value,
                "num_positions": len(portfolio_data.positions),
                "num_asset_classes": len(allocation_by_class)
            }

    except Exception as e:
        logger.error(f"[{session_id}] Error getting portfolio allocation: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "display_type": "text"
        }


# ────────────────────────────────────────────────────────────────────────────
# DISABLED TEMPORARILY — BUGS DOCUMENTED IN PORTFOLIO_TOOLS_BUGS.md
# ────────────────────────────────────────────────────────────────────────────
# Bug #4 (CRITICAL): Bond values showing -99% loss (PDF parsing extracts accrued interest instead of total value)
# Bug #5 (MEDIUM): Currency conversion issues (USD cost basis vs CHF current value)
# Will be re-enabled after fixes — see PORTFOLIO_TOOLS_BUGS.md for details
# ────────────────────────────────────────────────────────────────────────────

# @mcp.tool()
# async def get_portfolio_performance(
#     session_id: str,
#     top_n: int = 3
# ) -> dict:
#     """
#     Get portfolio performance with unrealized gains/losses.

#     Calculates P&L for all positions and returns top/bottom performers.
# 
#     Args:
#         session_id: Portfolio session ID
#         top_n: Number of top/bottom performers to return (default: 3)
# 
#     Returns:
#         Dict with top performers, worst performers, total P&L
# 
#     Example:
#         performance = await get_portfolio_performance("abc123", top_n=5)
#         # Returns: Top 5 gainers, Bottom 5 losers, aggregate P&L
#     """
#     logger.info(f"[{session_id}] Getting portfolio performance (top {top_n})")
# 
#     try:
#         with get_session() as db_session:
#             portfolio = db_session.get(Portfolio, session_id)
#             if not portfolio:
#                 return {
#                     "success": False,
#                     "error": f"Portfolio {session_id} not found.",
#                     "display_type": "text"
#                 }
# 
#             # Parse portfolio data
#             from app.models.portfolio import PortfolioData
#             portfolio_data = PortfolioData.model_validate_json(portfolio.data_json)
# 
#             # Calculate P&L for each position
#             performance_list = []
#             total_unrealized_pnl = 0.0
#             total_cost = 0.0
# 
#             for position in portfolio_data.positions:
#                 # Skip if no cost price or current value
#                 if not position.cost_price or not position.value_chf:
#                     continue
# 
#                 # Calculate cost basis
#                 quantity = position.quantity or 1.0
#                 cost_basis = position.cost_price * quantity
#                 current_value = position.value_chf
# 
#                 unrealized_pnl = current_value - cost_basis
#                 pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0.0
# 
#                 total_unrealized_pnl += unrealized_pnl
#                 total_cost += cost_basis
# 
#                 performance_list.append({
#                     "name": position.name,
#                     "ticker": position.ticker or "N/A",
#                     "asset_class": position.asset_class or "Unknown",
#                     "cost_basis_chf": round(cost_basis, 2),
#                     "current_value_chf": round(current_value, 2),
#                     "unrealized_pnl_chf": round(unrealized_pnl, 2),
#                     "pnl_pct": round(pnl_pct, 2)
#                 })
# 
#             if not performance_list:
#                 return {
#                     "success": False,
#                     "error": "No positions with cost price data found.",
#                     "display_type": "text"
#                 }
# 
#             # Sort by P&L CHF descending
#             performance_list.sort(key=lambda x: x["unrealized_pnl_chf"], reverse=True)
# 
#             # Get top and bottom performers
#             top_performers = performance_list[:top_n]
#             bottom_performers = performance_list[-top_n:][::-1]  # Reverse worst to show worst first
# 
#             # Calculate total P&L %
#             total_pnl_pct = (total_unrealized_pnl / total_cost * 100) if total_cost > 0 else 0.0
# 
#             # Build KPIs
#             kpis = [
#                 {
#                     "label": "Total Unrealized P&L",
#                     "value": f"CHF {total_unrealized_pnl:,.2f}",
#                     "change": f"{total_pnl_pct:+.2f}%",
#                     "change_type": "positive" if total_unrealized_pnl >= 0 else "negative",
#                     "icon": "trending-up" if total_unrealized_pnl >= 0 else "trending-down"
#                 },
#                 {
#                     "label": "Positions with P&L Data",
#                     "value": str(len(performance_list)),
#                     "icon": "briefcase"
#                 },
#                 {
#                     "label": "Total Cost Basis",
#                     "value": f"CHF {total_cost:,.2f}",
#                     "icon": "dollar-sign"
#                 }
#             ]
# 
#             # Build top performers table
#             top_table = {
#                 "headers": ["Position", "Gain/Loss (CHF)", "Gain/Loss (%)"],
#                 "rows": [
#                     [
#                         f"{p['name']} ({p['ticker']})",
#                         f"CHF {p['unrealized_pnl_chf']:,.2f}",
#                         f"{p['pnl_pct']:+.2f}%"
#                     ]
#                     for p in top_performers
#                 ]
#             }
# 
#             # Build worst performers table
#             worst_table = {
#                 "headers": ["Position", "Gain/Loss (CHF)", "Gain/Loss (%)"],
#                 "rows": [
#                     [
#                         f"{p['name']} ({p['ticker']})",
#                         f"CHF {p['unrealized_pnl_chf']:,.2f}",
#                         f"{p['pnl_pct']:+.2f}%"
#                     ]
#                     for p in bottom_performers
#                 ]
#             }
# 
#             return {
#                 "success": True,
#                 "content": f"Portfolio performance: {len(performance_list)} positions with P&L data.",
#                 "display_type": "mixed",
#                 "kpis": kpis,
#                 "top_performers": top_performers,
#                 "worst_performers": bottom_performers,
#                 "top_table": top_table,
#                 "worst_table": worst_table,
#                 "total_unrealized_pnl_chf": total_unrealized_pnl,
#                 "total_pnl_pct": total_pnl_pct,
#                 "all_performance": performance_list
#             }
# 
#     except Exception as e:
        logger.error(f"[{session_id}] Error getting portfolio performance: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "display_type": "text"
        }


# ────────────────────────────────────────────────────────────────────────────
# DISABLED TEMPORARILY — BUGS DOCUMENTED IN PORTFOLIO_TOOLS_BUGS.MD
# ────────────────────────────────────────────────────────────────────────────
# Bug #1 (HIGH): Weighted beta/sharpe/maxdd return 0.00 (normalization issue)
# Bug #2 (HIGH): Stress scenarios return CHF 0 (depends on Bug #1)
# Bug #3 (LOW): Portfolio volatility slightly off (6.5% vs 7.1% expected)
# Will be re-enabled after fixes — see PORTFOLIO_TOOLS_BUGS.md for details
# ────────────────────────────────────────────────────────────────────────────

# @mcp.tool()
# async def analyze_portfolio_risk(
#     session_id: str,
#     days: int = 90,
#     benchmark_ticker: str = "SPY"
# ) -> dict:
#     """
#     Comprehensive portfolio-level risk analysis.
# 
#     Aggregates risk metrics from all positions and computes portfolio-level
#     volatility, VaR, beta, concentration metrics, and stress scenarios.
# 
#     Args:
#         session_id: Portfolio session ID
#         days: Days of historical data for calculations (default: 90)
#         benchmark_ticker: Benchmark for beta/alpha (default: SPY)
# 
#     Returns:
#         Dict with portfolio risk metrics, concentration, stress scenarios
# 
#     Example:
#         risk = await analyze_portfolio_risk("abc123", days=252)
#         # Returns: Portfolio vol 15%, VaR CHF 5K, concentration analysis, etc.
#     """
#     logger.info(f"[{session_id}] Analyzing portfolio-level risk (days={days})")
# 
#     try:
#         with get_session() as db_session:
#             portfolio = db_session.get(Portfolio, session_id)
#             if not portfolio:
#                 return {
#                     "success": False,
#                     "error": f"Portfolio {session_id} not found.",
#                     "display_type": "text"
#                 }
# 
#             # Parse portfolio data
#             from app.models.portfolio import PortfolioData
#             portfolio_data = PortfolioData.model_validate_json(portfolio.data_json)
# 
#             # Get portfolio total value
#             total_value = sum(p.value_chf or 0.0 for p in portfolio_data.positions)
# 
#             if total_value == 0:
#                 return {
#                     "success": False,
#                     "error": "Portfolio has zero total value.",
#                     "display_type": "text"
#                 }
# 
#             # Separate listed and unlisted positions
#             listed_positions = [p for p in portfolio_data.positions if p.ticker]
#             unlisted_positions = [p for p in portfolio_data.positions if not p.ticker]
# 
#             # Get risk metrics for listed positions
#             risk_metrics = {}
#             for position in listed_positions:
#                 try:
#                     # Call analyze_risk for each listed position
#                     risk_result = await analyze_risk(
#                         ticker=position.ticker,
#                         session_id=session_id,
#                         days=days,
#                         benchmark=benchmark_ticker
#                     )
#                     if "volatility" in risk_result:
#                         risk_metrics[position.ticker] = risk_result
#                 except Exception as e:
#                     logger.warning(f"Could not get risk for {position.ticker}: {e}")
# 
#             # Calculate weighted average risk metrics for listed positions
#             listed_value = sum(p.value_chf or 0.0 for p in listed_positions)
#             listed_weight = listed_value / total_value if total_value > 0 else 0
# 
#             weighted_vol = 0.0
#             weighted_beta = 0.0
#             weighted_sharpe = 0.0
#             weighted_max_dd = 0.0
# 
#             for position in listed_positions:
#                 if position.ticker in risk_metrics:
#                     weight = (position.value_chf or 0.0) / total_value
#                     metrics = risk_metrics[position.ticker]
# 
#                     weighted_vol += weight * metrics.get("volatility", 0.0)
#                     weighted_beta += weight * metrics.get("beta", 0.0)
#                     weighted_sharpe += weight * metrics.get("sharpe_ratio", 0.0)
#                     weighted_max_dd += weight * metrics.get("max_drawdown", 0.0)
# 
#             # Estimate volatility for unlisted positions (conservative estimates)
#             unlisted_vol_estimate = 0.15  # 15% assumed vol for funds/structured products
#             unlisted_value = sum(p.value_chf or 0.0 for p in unlisted_positions)
#             unlisted_weight = unlisted_value / total_value if total_value > 0 else 0
# 
#             # Portfolio volatility (simplified - assumes some diversification)
#             # In reality would need correlation matrix
#             portfolio_vol = (
#                 weighted_vol * listed_weight +
#                 unlisted_vol_estimate * unlisted_weight
#             ) * 0.7  # Diversification factor
# 
#             # Portfolio VaR (parametric, 95% confidence, 1-day)
#             var_95_pct = 1.65 * portfolio_vol / (252 ** 0.5)  # Daily VaR
#             var_95_chf = total_value * var_95_pct
# 
#             # Concentration metrics
#             position_values = sorted(
#                 [(p.name, p.value_chf or 0.0) for p in portfolio_data.positions],
#                 key=lambda x: x[1],
#                 reverse=True
#             )
# 
#             top3_value = sum(v for _, v in position_values[:3])
#             top5_value = sum(v for _, v in position_values[:5])
#             top3_pct = (top3_value / total_value * 100) if total_value > 0 else 0
#             top5_pct = (top5_value / total_value * 100) if total_value > 0 else 0
# 
#             # Herfindahl-Hirschman Index (concentration)
#             hhi = sum(((v / total_value) ** 2) for _, v in position_values)
# 
#             # Stress scenarios
#             stress_scenarios = [
#                 {
#                     "scenario": "Normal Day (1σ)",
#                     "impact_pct": -portfolio_vol / (252 ** 0.5),
#                     "impact_chf": -total_value * portfolio_vol / (252 ** 0.5)
#                 },
#                 {
#                     "scenario": "VaR 95% (1 day)",
#                     "impact_pct": -var_95_pct,
#                     "impact_chf": -var_95_chf
#                 },
#                 {
#                     "scenario": "Market Correction (-10%)",
#                     "impact_pct": -0.10 * weighted_beta * listed_weight,
#                     "impact_chf": -total_value * 0.10 * weighted_beta * listed_weight
#                 },
#                 {
#                     "scenario": "Market Crash (-30%)",
#                     "impact_pct": -0.30 * weighted_beta * listed_weight,
#                     "impact_chf": -total_value * 0.30 * weighted_beta * listed_weight
#                 },
#                 {
#                     "scenario": "Max Drawdown",
#                     "impact_pct": weighted_max_dd,
#                     "impact_chf": total_value * weighted_max_dd
#                 }
#             ]
# 
#             # Build KPIs
#             kpis = [
#                 {
#                     "label": "Portfolio Volatility",
#                     "value": f"{portfolio_vol * 100:.1f}%",
#                     "change": "annualized",
#                     "icon": "activity"
#                 },
#                 {
#                     "label": "VaR 95% (1-day)",
#                     "value": f"CHF {abs(var_95_chf):,.0f}",
#                     "change": f"{abs(var_95_pct) * 100:.2f}%",
#                     "change_type": "negative",
#                     "icon": "alert-triangle"
#                 },
#                 {
#                     "label": "Portfolio Beta",
#                     "value": f"{weighted_beta:.2f}",
#                     "change": f"vs {benchmark_ticker}",
#                     "icon": "trending-up"
#                 },
#                 {
#                     "label": "Top 3 Concentration",
#                     "value": f"{top3_pct:.1f}%",
#                     "change": "High" if top3_pct > 50 else "Moderate",
#                     "change_type": "warning" if top3_pct > 50 else "neutral",
#                     "icon": "pie-chart"
#                 }
#             ]
# 
#             # Build concentration table
#             concentration_table = {
#                 "headers": ["Position", "Value (CHF)", "Weight (%)"],
#                 "rows": [
#                     [
#                         name,
#                         f"CHF {value:,.2f}",
#                         f"{(value / total_value * 100):.1f}%"
#                     ]
#                     for name, value in position_values[:10]  # Top 10
#                 ]
#             }
# 
#             # Build stress scenarios table
#             stress_table = {
#                 "headers": ["Scenario", "Impact (CHF)", "Impact (%)"],
#                 "rows": [
#                     [
#                         s["scenario"],
#                         f"CHF {s['impact_chf']:,.0f}",
#                         f"{s['impact_pct'] * 100:+.2f}%"
#                     ]
#                     for s in stress_scenarios
#                 ]
#             }
# 
#             # Build risk factors summary
#             risk_factors = []
# 
#             # Concentration risk
#             if top3_pct > 50:
#                 risk_factors.append({
#                     "factor": "Concentration Risk",
#                     "level": "HIGH",
#                     "description": f"Top 3 positions represent {top3_pct:.1f}% of portfolio"
#                 })
#             elif top3_pct > 40:
#                 risk_factors.append({
#                     "factor": "Concentration Risk",
#                     "level": "MEDIUM",
#                     "description": f"Top 3 positions represent {top3_pct:.1f}% of portfolio"
#                 })
# 
#             # Liquidity risk (unlisted positions)
#             if unlisted_weight > 0.5:
#                 risk_factors.append({
#                     "factor": "Liquidity Risk",
#                     "level": "MEDIUM-HIGH",
#                     "description": f"{unlisted_weight * 100:.1f}% in unlisted positions"
#                 })
# 
#             # Market risk (volatility)
#             if portfolio_vol > 0.20:
#                 risk_factors.append({
#                     "factor": "Market Volatility",
#                     "level": "HIGH",
#                     "description": f"Portfolio volatility {portfolio_vol * 100:.1f}% is elevated"
#                 })
#             elif portfolio_vol > 0.15:
#                 risk_factors.append({
#                     "factor": "Market Volatility",
#                     "level": "MEDIUM",
#                     "description": f"Portfolio volatility {portfolio_vol * 100:.1f}%"
#                 })
# 
#             return {
#                 "success": True,
#                 "content": f"Portfolio risk analysis complete for {len(portfolio_data.positions)} positions.",
#                 "display_type": "mixed",
#                 "kpis": kpis,
#                 "portfolio_volatility": portfolio_vol,
#                 "var_95_chf": var_95_chf,
#                 "var_95_pct": var_95_pct,
#                 "weighted_beta": weighted_beta,
#                 "weighted_sharpe": weighted_sharpe,
#                 "weighted_max_dd": weighted_max_dd,
#                 "concentration": {
#                     "top3_pct": top3_pct,
#                     "top5_pct": top5_pct,
#                     "hhi": hhi
#                 },
#                 "concentration_table": concentration_table,
#                 "stress_scenarios": stress_scenarios,
#                 "stress_table": stress_table,
#                 "risk_factors": risk_factors,
#                 "listed_weight": listed_weight,
#                 "unlisted_weight": unlisted_weight,
#                 "num_positions": len(portfolio_data.positions),
#                 "num_listed": len(listed_positions),
#                 "num_unlisted": len(unlisted_positions)
#             }
# 
    except Exception as e:
        logger.error(f"[{session_id}] Error analyzing portfolio risk: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "display_type": "text"
        }
