"""
Database models and setup for SQLite using SQLModel.

Tables:
- clients: Family office clients with risk profiles
- portfolios: Portfolio snapshots from uploaded PDFs (session_id = key)
- analysis_cache: Cached analysis results (optional for Phase 1)
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, create_engine, Session
from app.config import settings


# ────────────────────────────────────────────────────────────────────────────
# Models
# ────────────────────────────────────────────────────────────────────────────


class Client(SQLModel, table=True):
    """Family office client."""

    __tablename__ = "clients"

    id: Optional[str] = Field(default=None, primary_key=True)  # UUID
    name: str = Field(index=True)
    email: Optional[str] = None
    risk_profile: Optional[str] = None  # conservative | moderate | aggressive
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Portfolio(SQLModel, table=True):
    """Portfolio snapshot from uploaded PDF.

    The `id` field is the session_id — it's the key used in all MCP tool calls
    to reference this portfolio. The `data_json` field contains the full
    PortfolioData object serialized as JSON.
    """

    __tablename__ = "portfolios"

    id: Optional[str] = Field(default=None, primary_key=True)  # session_id (UUID)
    client_id: str = Field(foreign_key="clients.id", index=True)
    valuation_date: Optional[str] = None
    total_value_chf: Optional[float] = None
    raw_text: Optional[str] = None  # Raw PDF text
    data_json: str = Field(default="{}")  # PortfolioData serialized
    pdf_filename: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AnalysisCache(SQLModel, table=True):
    """Cached analysis results.

    Market data analyses (risk, momentum, correlation) are cached for 5 minutes.
    Portfolio-level analyses are cached until the portfolio is updated.
    """

    __tablename__ = "analysis_cache"

    id: Optional[str] = Field(default=None, primary_key=True)  # UUID
    portfolio_id: str = Field(foreign_key="portfolios.id", index=True)
    analysis_type: str = Field(index=True)  # risk | momentum | correlation | compliance
    ticker: Optional[str] = Field(default=None, index=True)
    parameters: str = Field(default="{}")  # JSON parameters
    result_json: str = Field(default="{}")  # JSON result
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None  # None = never expires


# ────────────────────────────────────────────────────────────────────────────
# Database setup
# ────────────────────────────────────────────────────────────────────────────


# Create engine
engine = create_engine(
    settings.database_url,
    echo=False,  # Set to True for SQL debugging
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)


def create_db_and_tables():
    """Create all tables if they don't exist."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Get a database session."""
    return Session(engine)


# Initialize database on import
create_db_and_tables()
