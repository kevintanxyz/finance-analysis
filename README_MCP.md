# WealthPoint - Portfolio Intelligence Platform

AI-powered portfolio analysis for family offices via Model Context Protocol (MCP).

**Status**: Phase 1 - 85% Complete (Feb 11, 2026)

---

## Overview

WealthPoint is a portfolio analysis platform that ingests PDF valuation statements and provides intelligent analysis through:
- 8 specialized AI agents (Market Researcher, Quant Analyst, Strategy Advisor, Compliance Officer, etc.)
- Natural language Q&A (French and English accepted, responses in English)
- Risk metrics, momentum indicators, correlation analysis
- Portfolio optimization and backtesting
- Compliance checking and reporting

The platform exposes all capabilities via **MCP (Model Context Protocol)**, allowing any MCP client (Claude Desktop, Claude Code, custom React apps) to connect and use the analysis tools.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  CLIENTS                                                │
│  Claude Desktop │ Claude Code │ React Chat │ Custom    │
└───────────────────────┬─────────────────────────────────┘
                        │ MCP Protocol (stdio / HTTP)
                        ▼
┌─────────────────────────────────────────────────────────┐
│  MCP SERVER  (mcp_server/)                              │
│                                                         │
│  Tools:     upload_portfolio, ask_portfolio, ...        │
│  Resources: portfolio://{id}, positions://{id}, ...     │
│  Prompts:   portfolio-summary, risk-report, ...         │
│                                                         │
│  ┌────────────────────────────────────────────────────┐ │
│  │  INTERNAL ENGINE (app/)                            │ │
│  │  parsers/    → PDF → PortfolioData                 │ │
│  │  analysis/   → Risk, Momentum, Correlation, ...    │ │
│  │  services/   → yfinance, LLM, SQLite               │ │
│  │  llm/        → Claude + Ollama abstraction         │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**No FastAPI, no REST API** — MCP is the only exposure surface.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| MCP Server | `mcp` Python SDK v1.x |
| Transport | stdio (local) + Streamable HTTP (remote/React) |
| LLM | Anthropic Claude (primary) + Ollama (fallback) |
| Database | SQLite v1 (migrateable to PostgreSQL) |
| PDF Parsing | pdfplumber |
| Market Data | yfinance |
| Analysis | pandas, numpy, scipy |
| Validation | Pydantic v2 |

---

## Project Structure

```
finance-analysis/
├── finance-guru-ref/          # Finance-Guru clone (READ-ONLY reference)
│   ├── src/analysis/          #   → Risk, momentum, correlation calculators
│   ├── src/strategies/        #   → Portfolio optimizer, backtester
│   ├── fin-guru/agents/       #   → Agent definitions (system prompts)
│   └── ...
│
├── mcp_server/                # MCP Server (only exposure surface)
│   ├── server.py              # FastMCP main entry point
│   ├── tools.py               # MCP tools (upload_portfolio, ask_portfolio, ...)
│   ├── resources.py           # MCP resources (portfolio://{id}, ...)
│   └── prompts.py             # MCP prompt templates
│
├── app/                       # Internal Python modules
│   ├── config.py              # Pydantic settings (env vars)
│   ├── database.py            # SQLModel tables (clients, portfolios, cache)
│   ├── models/
│   │   └── portfolio.py       # Pydantic models (PortfolioData, Position, ...)
│   ├── parsers/
│   │   ├── __init__.py        # detect_pdf_type(), parse_pdf()
│   │   └── valuation_pdf.py   # WealthPoint PDF parser (⚠️ needs refactoring)
│   ├── analysis/              # [Phase 2] Calculators
│   │   ├── risk_calculator.py
│   │   ├── momentum.py
│   │   ├── correlation.py
│   │   └── ...
│   ├── llm/                   # LLM abstraction
│   │   ├── __init__.py        # LLMProvider factory
│   │   ├── claude.py          # Claude provider
│   │   ├── ollama.py          # Ollama provider
│   │   └── prompts.py         # System prompts (English)
│   └── services/
│       ├── qa_service_llm.py  # LLM-powered Q&A
│       └── market_service.py  # yfinance bridge
│
├── tests/
│   └── test_phase1.py         # [TODO] Unit tests
│
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
├── PROMPT_CONTINUATION.md     # Full project context & requirements
├── PROGRESS.md                # Implementation progress tracker
├── NEXT_STEPS.md              # Detailed next steps & refactoring plan
└── README_MCP.md              # This file
```

---

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required environment variables:
- `ANTHROPIC_API_KEY` — Claude API key (get from https://console.anthropic.com)
- `DATABASE_URL` — SQLite path (default: `sqlite:///./wealthpoint.db`)

Optional:
- `OLLAMA_MODEL` — Ollama model for fallback (default: `llama3.1`)
- `OLLAMA_URL` — Ollama server URL (default: `http://localhost:11434`)
- `EXA_API_KEY` — Exa web search API key (for Market Researcher)
- `BRIGHTDATA_API_TOKEN` — Bright Data scraping API token

### 3. Initialize Database

The database auto-initializes on first import. To manually create tables:

```python
from app.database import create_db_and_tables
create_db_and_tables()
```

---

## Usage

### Local Testing (stdio mode)

Run the MCP server in stdio mode:

```bash
python -m mcp_server.server
```

Or use the MCP inspector for debugging:

```bash
mcp dev mcp_server/server.py
```

### Claude Desktop Integration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "wealthpoint-analysis": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/finance-analysis",
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "DATABASE_URL": "sqlite:///./wealthpoint.db"
      }
    }
  }
}
```

Restart Claude Desktop. The WealthPoint tools will appear in the tool selection.

### React Frontend (Phase 5)

Run in Streamable HTTP mode for React frontend:

```bash
python -m mcp_server.server --transport streamable-http --port 3001
```

The React app connects to `http://localhost:3001`.

---

## MCP Tools

### Phase 1 (Available Now)

| Tool | Description | Args | Returns |
|------|-------------|------|---------|
| `upload_portfolio` | Parse PDF and save to DB | `pdf_base64`, `filename`, `client_id` | `session_id`, summary |
| `ask_portfolio` | Q&A about portfolio | `session_id`, `question` | `content`, `display_type`, charts/tables/kpis |

### Phase 2-4 (Coming Soon)

| Tool | Description |
|------|-------------|
| `get_market_data` | Live market data for all listed positions |
| `analyze_risk` | VaR, Sharpe, Sortino, Beta, Alpha, Max Drawdown |
| `analyze_momentum` | RSI, MACD, SMA, Golden Cross, signals |
| `analyze_correlation` | Correlation matrix + diversification insights |
| `price_options` | Black-Scholes options pricing + Greeks |
| `optimize_portfolio` | Portfolio optimization (Max Sharpe, Risk Parity, etc.) |
| `backtest_strategy` | Backtest strategy vs benchmark |
| `check_compliance` | Compliance violations and warnings |
| `analyze_dividends` | Dividend yield and income optimization |
| `generate_full_report` | Comprehensive portfolio report (all agents) |

---

## MCP Resources

Resources expose portfolio data for the LLM to read:

- `portfolio://{session_id}` — Full portfolio data (JSON)
- `portfolio://{session_id}/positions` — All positions
- `portfolio://{session_id}/listed` — Listed positions only (with tickers)
- `portfolio://{session_id}/allocation` — Asset allocation
- `portfolio://{session_id}/exposure` — Currency/regional/sector exposure
- `portfolio://{session_id}/pnl` — P&L overview and detail
- `clients://list` — List of all clients

---

## MCP Prompts

Pre-defined conversation templates:

- `portfolio-summary` — Comprehensive portfolio overview
- `risk-report` — Deep risk analysis
- `rebalance-plan` — Rebalancing recommendations
- `morning-briefing` — Daily portfolio update

---

## Workflow Example

1. **Upload PDF**:
   ```json
   {
     "tool": "upload_portfolio",
     "params": {
       "pdf_base64": "JVBERi0xLjQK...",
       "filename": "valuation_2025.pdf"
     }
   }
   ```

   Response:
   ```json
   {
     "session_id": "abc123-...",
     "summary": "Portfolio loaded! 13 positions, CHF 2'988.44",
     "valuation_date": "27th of November 2025",
     "total_value_chf": 2988.44,
     "positions_count": 13
   }
   ```

2. **Ask questions**:
   ```json
   {
     "tool": "ask_portfolio",
     "params": {
       "session_id": "abc123-...",
       "question": "What is the asset allocation?"
     }
   }
   ```

   Response:
   ```json
   {
     "content": "Here is your portfolio allocation...",
     "display_type": "pie_chart",
     "charts": [{
       "chart_type": "pie",
       "title": "Asset Allocation",
       "labels": ["Equities", "Others", "Bonds", "Structured Products", "Cash"],
       "datasets": [{"label": "Allocation", "data": [38.00, 36.63, 17.66, 6.36, 1.35]}]
     }]
   }
   ```

3. **Read resources**:
   ```
   portfolio://abc123-.../listed
   ```

   Returns:
   ```json
   [
     {
       "name": "Roche Holding AG",
       "ticker": "ROG.SW",
       "value_chf": 1150.00,
       "weight_pct": 38.5,
       "perf_ytd_pct": 20.35
     },
     ...
   ]
   ```

---

## Development Status

### ✅ Phase 1 (85% Complete)

- [x] MCP Server structure
- [x] SQLite database
- [x] LLM abstraction (Claude + Ollama)
- [x] MCP tools: `upload_portfolio`, `ask_portfolio`
- [x] MCP resources: all portfolio data
- [x] MCP prompts: templates
- [ ] PDF parser refactoring (hardcoded positions → dynamic tables)
- [ ] Unit tests

### 🚧 Phase 2 (Not Started)

Analysis tools from Finance-Guru:
- Risk Calculator
- Momentum Indicators
- Correlation Analysis
- Options Pricer
- Portfolio Optimizer + Backtester

### ⏳ Phase 3-5 (Planned)

- Phase 3: Complete MCP server features (cache, Streamable HTTP, external MCP servers)
- Phase 4: Specialized agents (Compliance, Strategy Advisor, Dividend, Tax)
- Phase 5: React frontend, multi-PDF support, auth, deployment

---

## Next Steps

See [NEXT_STEPS.md](NEXT_STEPS.md) for:
- PDF parser refactoring plan (immediate priority)
- Phase 1 completion checklist
- Phase 2 implementation order
- Testing strategy

See [PROGRESS.md](PROGRESS.md) for:
- Detailed progress tracker
- Files created in each phase
- Decisions made

See [PROMPT_CONTINUATION.md](PROMPT_CONTINUATION.md) for:
- Full project context
- Architecture decisions
- Requirements

---

## Contributing

When continuing work:
1. Read `NEXT_STEPS.md` for current priorities
2. Update `PROGRESS.md` as you complete tasks
3. Reference `finance-guru-ref/` for Finance-Guru implementations
4. Keep all prompts and responses in **English**
5. Use Swiss number formatting (apostrophe separator: 2'988.44)

---

## License

Private / Internal Use

---

**Last Updated**: February 11, 2026
