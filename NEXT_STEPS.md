# WealthPoint - Next Steps for Implementation

**Last Updated**: February 11, 2026 14:00

This document outlines the immediate next steps to complete Phase 1 and continue with Phase 2-5.

---

## 🚨 IMMEDIATE PRIORITY: Refactor PDF Parser

### Current Problem

The PDF parser at [app/parsers/valuation_pdf.py:394](app/parsers/valuation_pdf.py#L394) has hardcoded positions:

```python
known_positions = [
    {
        "isin": "USU64106CB80", "valor": "125610987",
        "name": "4.85% Nestle Holdings Inc 2033/03/14",
        "asset_class": AssetClass.BONDS, "sub": "Bonds FX",
        "type": PositionType.BOND_FX, "ccy": "USD",
        ...
    },
    # ... more hardcoded positions
]
```

This approach:
- ❌ Only works with one specific PDF
- ❌ Requires manual updates for new portfolios
- ❌ Doesn't scale to multi-client usage

### Solution: Dynamic Table Extraction

Use `pdfplumber.extract_tables()` to dynamically parse position tables from PDFs.

### Refactoring Plan

#### Step 1: Analyze PDF Structure

Before coding, examine a sample PDF to understand:
1. How many tables are on the POSITIONS pages?
2. What are the column headers?
3. Are positions split across multiple pages?
4. Are there different table formats for different asset classes?

**Action**: Run this script to analyze a sample PDF:

```python
import pdfplumber

with pdfplumber.open("sample_valuation.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"\n=== PAGE {i+1} ===")
        print(page.extract_text()[:500])  # First 500 chars

        tables = page.extract_tables()
        print(f"\nTables found: {len(tables)}")
        for j, table in enumerate(tables):
            print(f"\nTable {j+1}:")
            for row in table[:5]:  # First 5 rows
                print(row)
```

#### Step 2: Create Table Parser

Create a new method `_extract_positions_from_tables()`:

```python
def _extract_positions_from_tables(self, pdf: pdfplumber.PDF) -> list[Position]:
    """
    Extract positions dynamically from PDF tables.

    Expected table structure:
    | Currency | ISIN | Valor | Qty | Name | ... | Value CHF | Weight % |
    """
    positions = []

    for page in pdf.pages:
        text = page.extract_text() or ""

        # Only process POSITIONS pages
        if "POSITIONS" not in text or "ISIN" not in text:
            continue

        tables = page.extract_tables()

        for table in tables:
            if not table or len(table) < 2:
                continue

            # Find header row
            header_idx = self._find_header_row(table)
            if header_idx is None:
                continue

            headers = table[header_idx]

            # Parse data rows
            for row in table[header_idx + 1:]:
                if not row or not any(row):  # Skip empty rows
                    continue

                position = self._parse_position_row(headers, row)
                if position:
                    positions.append(position)

    return positions


def _find_header_row(self, table: list) -> Optional[int]:
    """Find the row index containing column headers."""
    for i, row in enumerate(table):
        if not row:
            continue

        # Look for key headers
        row_text = " ".join(str(cell or "") for cell in row).lower()
        if "isin" in row_text and ("value" in row_text or "weight" in row_text):
            return i

    return None


def _parse_position_row(self, headers: list, row: list) -> Optional[Position]:
    """Parse a single position row."""
    try:
        # Create a dict mapping header -> value
        data = {}
        for i, header in enumerate(headers):
            if i < len(row):
                data[header.lower() if header else f"col_{i}"] = row[i]

        # Extract required fields
        currency = data.get("currency") or data.get("ccy")
        isin = data.get("isin")
        name = data.get("name") or data.get("instrument")
        value_chf = _parse_number(data.get("value chf") or data.get("value"))
        weight_pct = _parse_pct(data.get("weight %") or data.get("weight"))

        if not all([currency, isin, name, value_chf]):
            return None  # Missing required fields

        # Determine asset class from position type or ISIN
        asset_class = self._infer_asset_class(isin, name)

        # Check if listed (from ISIN_TICKER_MAP)
        ticker, is_listed = ISIN_TICKER_MAP.get(isin, (None, False))

        return Position(
            asset_class=asset_class,
            position_type=self._infer_position_type(asset_class, name),
            currency=currency,
            isin=isin,
            name=name,
            quantity=_parse_number(data.get("quantity") or data.get("qty")),
            cost_price=_parse_number(data.get("cost price")),
            quote=_parse_number(data.get("quote") or data.get("price")),
            value_chf=value_chf,
            weight_pct=weight_pct,
            ticker=ticker,
            is_listed=is_listed,
            # Bond-specific fields
            maturity_date=data.get("maturity"),
            coupon_rate=_parse_pct(data.get("coupon")),
            ytm=_parse_pct(data.get("ytm") or data.get("yield")),
            modified_duration=_parse_number(data.get("duration")),
        )

    except Exception as e:
        print(f"Error parsing row: {e}")
        return None


def _infer_asset_class(self, isin: str, name: str) -> AssetClass:
    """Infer asset class from ISIN and name."""
    name_lower = name.lower()

    # Cash accounts
    if "cash account" in name_lower:
        return AssetClass.CASH

    # Bonds
    if "%" in name and any(year in name for year in ["2025", "2026", "2027", "2028", "2029", "2030", "2031", "2032", "2033"]):
        return AssetClass.BONDS

    # Equities (stocks)
    if any(keyword in name_lower for keyword in ["ag", "inc", "corp", "ltd", "plc", "sa", "holding"]):
        # Check if it's not a bond or fund
        if "%" not in name and "fund" not in name_lower:
            return AssetClass.EQUITIES

    # ETFs
    if any(keyword in name_lower for keyword in ["etf", "spdr", "ishares", "vanguard"]):
        return AssetClass.EQUITIES

    # Structured products
    if any(keyword in name_lower for keyword in ["structured", "certificate", "warrant"]):
        return AssetClass.STRUCTURED_PRODUCTS

    # Funds
    if "fund" in name_lower or "pictet" in name_lower:
        return AssetClass.OTHERS

    # Default
    return AssetClass.OTHERS


def _infer_position_type(self, asset_class: AssetClass, name: str) -> PositionType:
    """Infer position type from asset class and name."""
    name_lower = name.lower()

    if asset_class == AssetClass.CASH:
        return PositionType.CASH_ACCOUNT

    if asset_class == AssetClass.BONDS:
        return PositionType.BOND_FX if any(ccy in name.upper() for ccy in ["USD", "EUR"]) else PositionType.BOND

    if asset_class == AssetClass.EQUITIES:
        if "etf" in name_lower or "spdr" in name_lower or "ishares" in name_lower:
            return PositionType.ETF
        return PositionType.EQUITY

    if asset_class == AssetClass.STRUCTURED_PRODUCTS:
        return PositionType.STRUCTURED_PRODUCT

    if "fund" in name_lower:
        return PositionType.FUND

    if "gold" in name_lower or "commodity" in name_lower:
        return PositionType.COMMODITY

    return PositionType.OTHER
```

#### Step 3: Update `_extract_positions()`

Replace the current implementation:

```python
def _extract_positions(self, pdf: pdfplumber.PDF) -> list[Position]:
    """Extract all positions from POSITIONS pages."""
    positions = []

    # Try dynamic table extraction first
    positions.extend(self._extract_positions_from_tables(pdf))

    # Fallback to cash positions if no tables found
    if not positions:
        positions.extend(self._extract_cash_positions())

    return positions
```

#### Step 4: Test with Sample PDF

1. Get a sample PDF (or use the one mentioned in PROMPT_CONTINUATION.md)
2. Run the parser
3. Verify all positions are extracted correctly
4. Check for missing fields or parsing errors

#### Step 5: Add Error Handling

```python
def parse(self) -> PortfolioData:
    """Parse the PDF and return structured data."""
    try:
        with pdfplumber.open(self.pdf_path) as pdf:
            # ... existing code ...

            data.positions = self._extract_positions(pdf)

            # Validate: ensure we have at least some positions
            if not data.positions:
                raise ValueError("No positions found in PDF. Parser may need adjustment.")

            # Validate: ensure total value matches sum of positions
            positions_sum = sum(p.value_chf for p in data.positions)
            if abs(positions_sum - data.total_value_chf) > 0.01:  # Allow small rounding errors
                print(f"Warning: Positions sum ({positions_sum}) != total value ({data.total_value_chf})")

        return data

    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")
```

---

## 📝 Phase 1 Completion Tasks

After refactoring the parser:

### 1. Unit Tests

Create `tests/test_phase1.py`:

```python
import pytest
from app.parsers import parse_pdf
from app.llm import create_llm
from app.database import get_session, Client, Portfolio

def test_pdf_parser_with_fixture():
    """Test PDF parser with a fixture PDF."""
    # TODO: Create a minimal test PDF or use mocked pdfplumber data
    pass

def test_llm_provider_factory():
    """Test LLM factory creates correct provider."""
    from app.config import settings

    # Mock settings
    settings.anthropic_api_key = None
    llm = create_llm()
    assert llm.__class__.__name__ == "OllamaProvider"

    settings.anthropic_api_key = "test-key"
    llm = create_llm()
    assert llm.__class__.__name__ == "ClaudeProvider"

@pytest.mark.asyncio
async def test_upload_portfolio_tool():
    """Test upload_portfolio MCP tool."""
    # TODO: Mock PDF data and test tool
    pass

@pytest.mark.asyncio
async def test_ask_portfolio_tool():
    """Test ask_portfolio MCP tool."""
    # TODO: Mock portfolio data and LLM response
    pass
```

### 2. Local MCP Server Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run server in dev mode with inspector
mcp dev mcp_server/server.py

# Or run in stdio mode
python -m mcp_server.server
```

### 3. Claude Desktop Integration

Create `claude_desktop_config.json`:

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

Test workflow:
1. Upload a PDF via `upload_portfolio` tool
2. Ask questions via `ask_portfolio` tool
3. Read resources via `portfolio://{session_id}`
4. Use prompts like `portfolio-summary`

---

## 🚀 Phase 2 - Analysis Tools

After Phase 1 is complete and tested:

### Order of Implementation

1. **Risk Calculator** (highest priority)
   - Read `finance-guru-ref/src/analysis/risk_metrics_cli.py`
   - Adapt to `app/analysis/risk_calculator.py`
   - Create MCP tool `analyze_risk`

2. **Momentum Indicators**
   - Read `finance-guru-ref/src/utils/momentum_cli.py`
   - Adapt to `app/analysis/momentum.py`
   - Create MCP tool `analyze_momentum`

3. **Correlation Analysis**
   - Read `finance-guru-ref/src/analysis/correlation_cli.py`
   - Adapt to `app/analysis/correlation.py`
   - Create MCP tool `analyze_correlation`

4. **Options Pricer**
   - Read `finance-guru-ref/src/analysis/options_pricer_cli.py`
   - Adapt to `app/analysis/options_pricer.py`
   - Create MCP tool `price_options`

5. **Portfolio Optimizer + Backtester**
   - Read `finance-guru-ref/src/strategies/optimizer.py` and `backtester.py`
   - Adapt to `app/analysis/portfolio_optimizer.py` and `backtester.py`
   - Create MCP tools `optimize_portfolio` and `backtest_strategy`

### Key Principles for Phase 2

- **Read before coding**: Always read the Finance-Guru source file first
- **Adapt, don't rewrite**: Use existing logic, just change I/O (CLI → Python functions)
- **Keep separation**: Calculator classes in `app/analysis/`, MCP tools in `mcp_server/tools.py`
- **Return structured data**: Tools return dicts, not text
- **Test with mock data**: Don't require live market data for tests

---

## 📋 Phase 3 - Complete MCP Features

1. **Streamable HTTP Transport**
   - Test server with `--transport streamable-http --port 3001`
   - Create simple test client

2. **Cache Implementation**
   - Use `analysis_cache` table for market data (5min TTL)
   - Cache portfolio analyses until portfolio updated

3. **External MCP Servers**
   - Document how to configure Exa, Bright Data, Sequential Thinking
   - Test integration with Claude Desktop

---

## 🎯 Phase 4 - Specialized Agents

1. **Compliance Officer**
   - Read `finance-guru-ref/fin-guru/agents/compliance-officer.md`
   - Create configurable limits (per client)
   - Tool `check_compliance` with violations report

2. **Strategy Advisor**
   - Use Phase 2 optimizer + backtester
   - Tools `optimize_portfolio`, `backtest_strategy`

3. **Dividend Specialist**
   - Dividend yield analysis
   - Income projection
   - Tool `analyze_dividends`

4. **Full Report Generator**
   - Orchestrate all tools
   - Generate comprehensive PDF (Phase 5)
   - Tool `generate_full_report`

---

## 🌐 Phase 5 - Production

1. **React Frontend**
   - Chat interface
   - File upload (PDF → base64)
   - Dynamic rendering based on display_type

2. **Multi-PDF Support**
   - UBS parser
   - Julius Baer parser
   - Credit Suisse parser

3. **Authentication**
   - JWT tokens
   - Multi-client support
   - Portfolio access control

4. **Deployment**
   - Docker images
   - Production database (PostgreSQL)
   - CI/CD pipeline

---

## 🔍 How to Use This Document

1. **Before each coding session**: Read the relevant section above
2. **Update PROGRESS.md**: Mark tasks as complete
3. **Update this file**: Add new findings, blockers, or decisions
4. **Reference PROMPT_CONTINUATION.md**: For architecture and requirements

---

## 📞 Getting Help

If stuck:
1. Check `finance-guru-ref/` for reference implementations
2. Review `PROMPT_CONTINUATION.md` for architecture decisions
3. Check MCP SDK docs: https://modelcontextprotocol.io/docs
4. Check Anthropic API docs: https://docs.anthropic.com/

---

**Last Updated**: February 11, 2026 14:00
