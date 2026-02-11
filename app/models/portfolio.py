"""Pydantic models for structured portfolio data."""
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────

class AssetClass(str, Enum):
    CASH = "Cash"
    BONDS = "Bonds"
    EQUITIES = "Equities"
    STRUCTURED_PRODUCTS = "Structured Products"
    OTHERS = "Others"


class PositionType(str, Enum):
    CASH_ACCOUNT = "cash_account"
    BOND_FX = "bond_fx"
    BOND_FUND = "bond_fund"
    EQUITY = "equity"
    ETF = "etf"
    STRUCTURED_PRODUCT = "structured_product"
    FUND = "fund"
    COMMODITY = "commodity"
    OTHER = "other"


# ── Sub‑models ─────────────────────────────────────────────────────────

class MandateDetails(BaseModel):
    mandate: str = ""
    custody_bank: str = ""
    portfolio_number: str = ""


class PortfolioDetails(BaseModel):
    currency: str = "CHF"
    profile: str = ""


class AllocationItem(BaseModel):
    asset_class: str
    value_chf: float
    weight_pct: float


class ExposureItem(BaseModel):
    name: str
    value_chf: float
    weight_pct: float


class PnLOverview(BaseModel):
    assets_start: float = 0.0
    assets_end: float = 0.0
    change_in_value: float = 0.0
    deposits_cash: float = 0.0
    withdrawals_cash: float = 0.0
    deposits_securities: float = 0.0
    withdrawals_securities: float = 0.0
    total_deposits_withdrawals: float = 0.0
    total_pnl_pct: float = 0.0
    total_pnl_value: float = 0.0


class PnLDetail(BaseModel):
    realized_market_profit: float = 0.0
    realized_market_loss: float = 0.0
    realized_fx_profit: float = 0.0
    realized_fx_loss: float = 0.0
    unrealized_market_pnl: float = 0.0
    unrealized_fx_pnl: float = 0.0
    interests_dividends: float = 0.0
    realized_interests: float = 0.0
    unrealized_interests: float = 0.0
    realized_dividends: float = 0.0
    portfolio_management_fees: float = 0.0
    total_bank_fees: float = 0.0
    withholding_taxes: float = 0.0
    other_taxes: float = 0.0
    total_pnl: float = 0.0


class TopFlop(BaseModel):
    name: str
    currency: str
    pct: float


class PerformancePeriod(BaseModel):
    from_date: str
    to_date: str
    start_value: float
    end_value: float
    deposits: float
    withdrawals: float
    profit_loss: float
    cum_pnl: float
    performance_pct: float
    cum_perf_pct: float


class Position(BaseModel):
    """A single portfolio position."""
    asset_class: AssetClass
    sub_category: str = ""
    position_type: PositionType
    currency: str
    isin: Optional[str] = None
    valor: Optional[str] = None
    quantity: float = 0.0
    name: str
    cost_price: Optional[float] = None
    quote: Optional[float] = None
    quote_date: Optional[str] = None
    perf_ytd_pct: Optional[float] = None
    contr_ytd_pct: Optional[float] = None
    fx_contr_ytd_pct: Optional[float] = None
    value_quote_ccy: Optional[float] = None
    accrued_interest: Optional[float] = None
    fx_rate: Optional[float] = None
    value_chf: float = 0.0
    weight_pct: float = 0.0
    # For listed instruments → ticker for Finance-Guru
    ticker: Optional[str] = None
    is_listed: bool = False
    # Bond-specific
    maturity_date: Optional[str] = None
    coupon_rate: Optional[float] = None
    ytm: Optional[float] = None
    modified_duration: Optional[float] = None


class Transaction(BaseModel):
    date: str
    instrument: str
    operation_type: str
    description: Optional[str] = None
    amount: float = 0.0
    price: float = 0.0
    settlement_ccy: str = ""
    op_value: float = 0.0


class ScenarioAnalysis(BaseModel):
    scenario: str
    impact_pct: float


class RiskAnalysis(BaseModel):
    risk_grade: str = ""
    risk_budget: str = ""
    scenarios: list[ScenarioAnalysis] = []


# ── Main Portfolio Model ───────────────────────────────────────────────

class PortfolioData(BaseModel):
    """Complete structured portfolio extracted from a valuation PDF."""
    extraction_date: str = ""
    valuation_date: str = ""
    mandate: MandateDetails = MandateDetails()
    portfolio_details: PortfolioDetails = PortfolioDetails()
    asset_allocation: list[AllocationItem] = []
    total_value_chf: float = 0.0
    currency_exposure: list[ExposureItem] = []
    regional_exposure: list[ExposureItem] = []
    sector_exposure: list[ExposureItem] = []
    pnl_overview: PnLOverview = PnLOverview()
    pnl_detail: PnLDetail = PnLDetail()
    tops: list[TopFlop] = []
    flops: list[TopFlop] = []
    performance: list[PerformancePeriod] = []
    positions: list[Position] = []
    transactions: list[Transaction] = []
    risk_analysis: RiskAnalysis = RiskAnalysis()

    @property
    def listed_positions(self) -> list[Position]:
        """Return only positions that have a ticker (listed instruments)."""
        return [p for p in self.positions if p.is_listed and p.ticker]

    @property
    def listed_tickers(self) -> list[str]:
        """Return ticker symbols for listed instruments."""
        return [p.ticker for p in self.positions if p.is_listed and p.ticker]


# ── API Request / Response ─────────────────────────────────────────────

class UploadResponse(BaseModel):
    session_id: str
    message: str
    valuation_date: str
    total_value_chf: float
    positions_count: int
    listed_count: int
    listed_tickers: list[str]


class QuestionRequest(BaseModel):
    question: str


class QuestionResponse(BaseModel):
    question: str
    answer: str
    data: Optional[dict] = None


class MarketAnalysis(BaseModel):
    ticker: str
    name: str
    currency: str
    weight_pct: float
    value_chf: float
    perf_ytd_pct: Optional[float] = None
    current_price: Optional[float] = None
    price_change_1d_pct: Optional[float] = None
    price_change_5d_pct: Optional[float] = None
    price_change_1m_pct: Optional[float] = None
    volume: Optional[float] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    error: Optional[str] = None
