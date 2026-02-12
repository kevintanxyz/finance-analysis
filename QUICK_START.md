# WealthPoint - Quick Start Guide

**For continuing implementation in next chat session**

---

## 📋 What Has Been Done (Phase 1 - 85%)

✅ **Infrastructure Complete**:
- MCP server structure created (`mcp_server/`)
- Database models ready (`app/database.py`)
- LLM abstraction working (`app/llm/`)
- Configuration system set up (`app/config.py`)

✅ **MCP Tools Working**:
- `upload_portfolio` — PDF upload (base64) → parse → save to SQLite → return session_id
- `ask_portfolio` — Q&A with LLM (returns structured data for frontend)

✅ **MCP Resources Exposed**:
- `portfolio://{session_id}` — Full portfolio
- `portfolio://{session_id}/positions` — All positions
- `portfolio://{session_id}/listed` — Listed positions only
- etc.

✅ **All prompts in English** (as requested)

---

## 🚨 What Needs to Be Done Next

### Priority 1: Refactor PDF Parser

**Problem**: The PDF parser at `app/parsers/valuation_pdf.py` line 394+ has hardcoded positions.

**Solution**: Make it dynamic using `pdfplumber.extract_tables()`.

**Detailed plan**: See [NEXT_STEPS.md](NEXT_STEPS.md) section "IMMEDIATE PRIORITY: Refactor PDF Parser"

**Steps**:
1. Analyze sample PDF structure
2. Create `_extract_positions_from_tables()` method
3. Add header detection and row parsing
4. Test with real PDF
5. Add validation

### Priority 2: Unit Tests

Create `tests/test_phase1.py` with:
- PDF parser tests (with mock data)
- LLM provider tests (mock responses)
- MCP tools tests (mock database)

### Priority 3: Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Add your ANTHROPIC_API_KEY

# Test MCP server
mcp dev mcp_server/server.py
```

---

## 🗂️ Key Files to Know

| File | Purpose |
|------|---------|
| `PROMPT_CONTINUATION.md` | **Full project context** — read this first! |
| `PROGRESS.md` | What's done, what's pending, decisions made |
| `NEXT_STEPS.md` | **Detailed refactoring plan** for PDF parser + Phase 2 roadmap |
| `README_MCP.md` | Project overview, architecture, usage |
| `mcp_server/tools.py` | MCP tools implementation |
| `app/parsers/valuation_pdf.py` | **PDF parser (needs refactoring)** |
| `app/llm/prompts.py` | System prompts (all in English) |

---

## 💡 How to Continue

### If continuing PDF parser refactoring:

1. **Read** `NEXT_STEPS.md` section "IMMEDIATE PRIORITY: Refactor PDF Parser"
2. **Run** the PDF analysis script to understand table structure
3. **Implement** `_extract_positions_from_tables()` method
4. **Test** with sample PDF
5. **Update** `PROGRESS.md` when done

### If moving to Phase 2 (analysis tools):

1. **Complete** PDF parser refactoring first (Priority 1)
2. **Read** `finance-guru-ref/src/analysis/risk_metrics_cli.py` for reference
3. **Create** `app/analysis/risk_calculator.py` (adapt Finance-Guru code)
4. **Add** MCP tool `analyze_risk` in `mcp_server/tools.py`
5. **Test** with mock market data
6. **Update** `PROGRESS.md` Phase 2 progress

---

## 📁 Project Structure Quick Reference

```
finance-analysis/
├── mcp_server/               # MCP Server (only exposure)
│   ├── server.py             # Main entry point
│   ├── tools.py              # ⭐ MCP tools (upload, ask, analyze)
│   ├── resources.py          # MCP resources (portfolio data)
│   └── prompts.py            # MCP prompt templates
│
├── app/
│   ├── config.py             # Settings (env vars)
│   ├── database.py           # SQLite models
│   ├── parsers/
│   │   └── valuation_pdf.py  # ⚠️ NEEDS REFACTORING
│   ├── llm/                  # LLM abstraction
│   │   ├── claude.py
│   │   ├── ollama.py
│   │   └── prompts.py        # ⭐ System prompts (English)
│   ├── services/
│   │   └── qa_service_llm.py # Q&A with display_type
│   └── analysis/             # [Phase 2] Calculators (to be created)
│
├── finance-guru-ref/         # Reference code (READ-ONLY)
│   ├── src/analysis/         # ⭐ Risk, momentum, correlation
│   ├── src/strategies/       # ⭐ Optimizer, backtester
│   └── fin-guru/agents/      # ⭐ Agent definitions
│
├── PROMPT_CONTINUATION.md    # ⭐ FULL PROJECT CONTEXT
├── PROGRESS.md               # ⭐ Progress tracker
├── NEXT_STEPS.md             # ⭐ Detailed next steps
└── README_MCP.md             # Project overview
```

---

## 🔧 Commands Cheat Sheet

```bash
# Install dependencies
pip install -r requirements.txt

# Run MCP server (stdio mode)
python -m mcp_server.server

# Run with MCP inspector (dev mode)
mcp dev mcp_server/server.py

# Run in Streamable HTTP mode (for React frontend)
python -m mcp_server.server --transport streamable-http --port 3001

# Run tests (when created)
pytest tests/

# Format code
black app/ mcp_server/

# Type check
mypy app/ mcp_server/
```

---

## 🎯 Current Sprint Goals

1. ✅ Phase 1 infrastructure — **DONE**
2. 🚧 Refactor PDF parser — **IN PROGRESS** (see NEXT_STEPS.md)
3. ⏳ Unit tests — **TODO**
4. ⏳ Local testing with Claude Desktop — **TODO**
5. ⏳ Phase 2: Risk Calculator — **TODO** (read Finance-Guru first)

---

## 📚 Important Notes

### Language
- **All prompts and responses in English** (user request)
- Accept questions in French or English, respond in English
- Use Swiss number formatting: `2'988.44` (apostrophe separator)

### Architecture
- **No FastAPI** — MCP server is the only exposure surface
- **MCP tools return structured data**, not text (LLM client does the rendering)
- **Tools = wrappers** — business logic in `app/analysis/`, not in `mcp_server/`

### Finance-Guru Reference
- **Read before coding** — always check `finance-guru-ref/` for existing implementations
- **Adapt, don't rewrite** — CLI → Python function, stdout → dict return
- **Keep separation** — Calculator classes in `app/analysis/`, MCP tools in `mcp_server/tools.py`

---

## 🚀 Start Here

1. **New to project?** → Read `PROMPT_CONTINUATION.md`
2. **Continuing work?** → Read `NEXT_STEPS.md`
3. **Need context?** → Read `PROGRESS.md`
4. **Want to run?** → Read `README_MCP.md`
5. **Quick start?** → You're reading it!

---

**Ready to code?** Start with the PDF parser refactoring (see NEXT_STEPS.md)!

**Last Updated**: February 11, 2026 14:00
