# Portfolio Analysis API

FastAPI service that ingests financial valuation PDFs, extracts structured data, and exposes Q&A + market analysis endpoints compatible with [Finance-Guru](https://github.com/AojdevStudio/Finance-Guru).

## Architecture

```
┌──────────────┐      ┌──────────────────────────────────────────┐
│  Valuation   │      │          Portfolio Analysis API          │
│    PDF       │─────▶│                                          │
└──────────────┘      │  ┌─────────┐  ┌──────────┐  ┌────────┐ │
                      │  │  PDF    │  │  Q&A     │  │ Market │ │
                      │  │ Parser  │─▶│ Service  │  │ Service│ │
                      │  └─────────┘  └──────────┘  └────────┘ │
                      │       │                          │      │
                      │       ▼                          ▼      │
                      │  ┌──────────────┐  ┌──────────────────┐ │
                      │  │ Structured   │  │   yfinance       │ │
                      │  │ PortfolioData│  │ (listed tickers) │ │
                      │  └──────────────┘  └──────────────────┘ │
                      └──────────────────────────────────────────┘
                                         │
                                         ▼
                      ┌──────────────────────────────────────────┐
                      │         Finance-Guru Agents              │
                      │  (risk, momentum, correlation analysis)  │
                      └──────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Run
uvicorn app.main:app --reload

# 3. Open docs
open http://localhost:8000/docs
```

Or with Docker:

```bash
docker compose up --build
```

## API Endpoints

### Upload & Parse

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/upload` | Upload a valuation PDF, get structured data |
| `GET` | `/api/v1/portfolio/{session_id}` | Full structured portfolio JSON |
| `GET` | `/api/v1/portfolio/{session_id}/positions` | Positions (filterable) |

### Q&A

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/ask/{session_id}` | Ask questions in natural language (FR/EN) |

**Example questions:**
- "Quelle est la valeur totale du portefeuille?"
- "Top performers"
- "Exposition par devise"
- "Détails sur Roche"
- "Analyse de risque"
- "Obligations et duration"

### Finance-Guru Bridge (Listed Positions)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/listed/{session_id}` | Listed positions with tickers |
| `GET` | `/api/v1/market/{session_id}` | Live market data (price, PE, beta…) |
| `GET` | `/api/v1/risk/{session_id}/{ticker}` | Sharpe, Sortino, VaR, Beta, Alpha |
| `GET` | `/api/v1/momentum/{session_id}/{ticker}` | RSI, MACD, SMA crossovers |
| `GET` | `/api/v1/correlation/{session_id}` | Correlation matrix + diversification |

## Usage Example

```bash
# Upload PDF
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@valuation.pdf"

# Response:
# {
#   "session_id": "a1b2c3d4e5f6",
#   "total_value_chf": 2988.44,
#   "listed_tickers": ["ROG.SW", "TTE.PA", "AAPL", "SPY"]
# }

# Ask a question
curl -X POST http://localhost:8000/api/v1/ask/a1b2c3d4e5f6 \
  -H "Content-Type: application/json" \
  -d '{"question": "allocation du portefeuille"}'

# Risk metrics for Apple
curl http://localhost:8000/api/v1/risk/a1b2c3d4e5f6/AAPL?days=90
```

## Extracted Data Structure

The PDF parser extracts:

- **Metadata**: mandate, custody bank, portfolio number, currency, profile
- **Asset Allocation**: Cash, Bonds, Equities, Structured Products, Others
- **Exposure**: by currency (CHF/USD/EUR), region, sector
- **P&L**: overview + detailed breakdown (realized/unrealized, FX, fees)
- **Tops/Flops**: best and worst performers YTD
- **Performance**: monthly and yearly with deposits/withdrawals
- **Positions**: each instrument with ISIN, cost, quote, P&L, weight
- **Transactions**: all buys/sells/subscriptions
- **Risk Analysis**: scenario stress tests (historical crises)

## Finance-Guru Integration

Listed positions are automatically identified and tagged with their ticker:

| Position | Ticker | Exchange |
|----------|--------|----------|
| Roche Holding Ltd | `ROG.SW` | SIX |
| TotalEnergies SE | `TTE.PA` | Euronext |
| Apple Inc | `AAPL` | NASDAQ |
| SPDR S&P 500 ETF | `SPY` | NYSE |

These can be fed into Finance-Guru agents for deep analysis:

```bash
# In Finance-Guru / Claude Code:
*quant "Analyze risk profile for ROG.SW, AAPL, SPY from my portfolio API"
*strategy "Check correlation and optimize allocation for ROG.SW TTE.PA AAPL SPY"
```

## Extending

### Add new PDF formats

Create a parser in `app/parsers/` and register it in `app/parsers/__init__.py`:

```python
def detect_pdf_type(pdf_path: str) -> str:
    # Add your detection logic
    if "YOUR BANK HEADER" in first_pages:
        return "your_bank"
```

### Add ISIN → Ticker mappings

Edit `ISIN_TICKER_MAP` in `app/parsers/valuation_pdf.py`:

```python
ISIN_TICKER_MAP = {
    "CH0012032048": ("ROG.SW", True),   # Roche
    "YOUR_ISIN":    ("TICKER", True),   # Your instrument
}
```

### Add LLM-powered Q&A

The Q&A service is designed to be extended with an LLM backend.
Add an Anthropic/OpenAI client in `app/services/qa_service.py` for
free-form questions that go beyond pattern matching.

## Project Structure

```
portfolio-api/
├── app/
│   ├── main.py                 # FastAPI app
│   ├── models/
│   │   └── portfolio.py        # Pydantic models
│   ├── parsers/
│   │   ├── __init__.py         # Generic parser + format detection
│   │   └── valuation_pdf.py    # WealthPoint format parser
│   ├── routers/
│   │   └── portfolio.py        # API endpoints
│   └── services/
│       ├── market_service.py   # yfinance + risk/momentum analysis
│       ├── qa_service.py       # Q&A engine
│       └── session_store.py    # In-memory session management
├── scripts/
│   ├── demo.sh                 # curl demo
│   └── test_client.py          # Python test client
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```
