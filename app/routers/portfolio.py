"""
API Routes for the Portfolio Analysis Service.

Endpoints:
  POST /api/v1/upload          — Upload a valuation PDF
  GET  /api/v1/portfolio/{id}  — Get structured portfolio data
  POST /api/v1/ask/{id}        — Ask a question about the portfolio
  GET  /api/v1/listed/{id}     — Get listed positions with tickers
  GET  /api/v1/market/{id}     — Live market data for listed positions
  GET  /api/v1/risk/{id}/{tkr} — Risk metrics for a ticker
  GET  /api/v1/momentum/{id}/{tkr} — Momentum indicators for a ticker
  GET  /api/v1/correlation/{id}    — Correlation matrix for listed positions
"""
from __future__ import annotations

import os
import shutil
import tempfile
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.models.portfolio import (
    MarketAnalysis,
    QuestionRequest,
    QuestionResponse,
    UploadResponse,
)
from app.parsers import extract_raw_text, parse_pdf
from app.services.market_service import MarketDataService
from app.services.qa_service import PortfolioQA
from app.services.session_store import store

router = APIRouter(prefix="/api/v1", tags=["portfolio"])
market_svc = MarketDataService()


# ── Upload ─────────────────────────────────────────────────────────────

@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a valuation PDF and extract structured data."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted.")

    # Save to temp file
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        shutil.copyfileobj(file.file, tmp)
        tmp.close()

        # Parse
        portfolio = parse_pdf(tmp.name)
        raw_text = extract_raw_text(tmp.name)

        if not portfolio.positions and not portfolio.asset_allocation:
            raise HTTPException(
                422,
                "Could not extract portfolio data. "
                "The PDF format may not be supported yet.",
            )

        # Store session
        session_id = store.create(tmp.name, portfolio, raw_text)

        return UploadResponse(
            session_id=session_id,
            message="Portfolio parsed successfully.",
            valuation_date=portfolio.valuation_date,
            total_value_chf=portfolio.total_value_chf,
            positions_count=len(portfolio.positions),
            listed_count=len(portfolio.listed_positions),
            listed_tickers=portfolio.listed_tickers,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error processing PDF: {str(e)}")
    finally:
        file.file.close()


# ── Portfolio Data ─────────────────────────────────────────────────────

@router.get("/portfolio/{session_id}")
async def get_portfolio(session_id: str):
    """Get the full structured portfolio data."""
    session = store.get(session_id)
    if not session or not session.portfolio:
        raise HTTPException(404, "Session not found.")
    return session.portfolio.model_dump()


@router.get("/portfolio/{session_id}/positions")
async def get_positions(
    session_id: str,
    asset_class: Optional[str] = Query(None, description="Filter by asset class"),
    listed_only: bool = Query(False, description="Only listed positions"),
):
    """Get portfolio positions with optional filters."""
    session = store.get(session_id)
    if not session or not session.portfolio:
        raise HTTPException(404, "Session not found.")

    positions = session.portfolio.positions

    if asset_class:
        positions = [p for p in positions if p.asset_class.value.lower() == asset_class.lower()]

    if listed_only:
        positions = [p for p in positions if p.is_listed]

    return [p.model_dump() for p in positions]


# ── Q&A ────────────────────────────────────────────────────────────────

@router.post("/ask/{session_id}", response_model=QuestionResponse)
async def ask_question(session_id: str, req: QuestionRequest):
    """Ask a question about the portfolio."""
    session = store.get(session_id)
    if not session or not session.portfolio:
        raise HTTPException(404, "Session not found.")

    qa = PortfolioQA(session.portfolio, session.raw_text)
    result = qa.answer(req.question)

    return QuestionResponse(
        question=req.question,
        answer=result["answer"],
        data=result.get("data"),
    )


# ── Listed Positions ───────────────────────────────────────────────────

@router.get("/listed/{session_id}")
async def get_listed_positions(session_id: str):
    """Get listed positions with tickers (Finance-Guru compatible)."""
    session = store.get(session_id)
    if not session or not session.portfolio:
        raise HTTPException(404, "Session not found.")

    listed = session.portfolio.listed_positions
    return {
        "count": len(listed),
        "tickers": session.portfolio.listed_tickers,
        "positions": [
            {
                "ticker": p.ticker,
                "name": p.name,
                "isin": p.isin,
                "currency": p.currency,
                "value_chf": p.value_chf,
                "weight_pct": p.weight_pct,
                "cost_price": p.cost_price,
                "current_quote": p.quote,
                "perf_ytd_pct": p.perf_ytd_pct,
            }
            for p in listed
        ],
    }


# ── Market Analysis (Finance-Guru bridge) ──────────────────────────────

@router.get("/market/{session_id}")
async def get_market_data(session_id: str):
    """Get live market data for all listed positions."""
    session = store.get(session_id)
    if not session or not session.portfolio:
        raise HTTPException(404, "Session not found.")

    listed = session.portfolio.listed_positions
    if not listed:
        return {"message": "No listed positions found.", "analyses": []}

    analyses = []
    for pos in listed:
        analysis = market_svc.get_analysis(pos)
        analyses.append(analysis.model_dump())

    return {"count": len(analyses), "analyses": analyses}


@router.get("/risk/{session_id}/{ticker}")
async def get_risk_metrics(
    session_id: str,
    ticker: str,
    benchmark: str = Query("SPY", description="Benchmark ticker"),
    days: int = Query(90, ge=30, le=365, description="Lookback period"),
):
    """
    Compute risk metrics for a listed position.

    Finance-Guru compatible: Sharpe, Sortino, VaR, Beta, Alpha, Max Drawdown.
    """
    session = store.get(session_id)
    if not session or not session.portfolio:
        raise HTTPException(404, "Session not found.")

    # Validate ticker belongs to portfolio
    valid_tickers = session.portfolio.listed_tickers
    if ticker.upper() not in [t.upper() for t in valid_tickers]:
        raise HTTPException(
            400,
            f"Ticker {ticker} not in portfolio. Available: {valid_tickers}",
        )

    return market_svc.get_risk_metrics(ticker, benchmark, days)


@router.get("/momentum/{session_id}/{ticker}")
async def get_momentum(
    session_id: str,
    ticker: str,
    days: int = Query(90, ge=30, le=365),
):
    """
    Compute momentum indicators for a listed position.

    Finance-Guru compatible: RSI, MACD, SMA crossovers.
    """
    session = store.get(session_id)
    if not session or not session.portfolio:
        raise HTTPException(404, "Session not found.")

    valid_tickers = session.portfolio.listed_tickers
    if ticker.upper() not in [t.upper() for t in valid_tickers]:
        raise HTTPException(
            400,
            f"Ticker {ticker} not in portfolio. Available: {valid_tickers}",
        )

    return market_svc.get_momentum(ticker, days)


@router.get("/correlation/{session_id}")
async def get_correlation(
    session_id: str,
    days: int = Query(90, ge=30, le=365),
):
    """
    Compute correlation matrix between all listed positions.

    Finance-Guru compatible diversification analysis.
    """
    session = store.get(session_id)
    if not session or not session.portfolio:
        raise HTTPException(404, "Session not found.")

    tickers = session.portfolio.listed_tickers
    if len(tickers) < 2:
        return {"message": "Need at least 2 listed positions for correlation."}

    return market_svc.get_correlation_matrix(tickers, days)


# ── Session Management ─────────────────────────────────────────────────

@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and its data."""
    if store.delete(session_id):
        return {"message": "Session deleted."}
    raise HTTPException(404, "Session not found.")


@router.get("/sessions")
async def list_sessions():
    """List active sessions."""
    return {"sessions": store.list_sessions()}
