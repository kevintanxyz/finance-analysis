# Testing Guide for NUMAN

**Last Updated**: February 11, 2026

This guide explains how to test the NUMAN platform after Phase 1 completion.

---

## 🧪 Unit Tests

### PDF Parser Tests

The dynamic PDF parser has comprehensive unit tests:

```bash
# Run all parser tests
pytest tests/test_pdf_parser_dynamic.py -v

# Run specific test
pytest tests/test_pdf_parser_dynamic.py::test_infer_asset_class_bonds -v

# Run with coverage
pytest tests/test_pdf_parser_dynamic.py --cov=app.parsers --cov-report=html
```

**Tests included:**
- ✅ Number/percentage parsing (Swiss formatting)
- ✅ Table header detection
- ✅ Asset class inference (bonds, equities, ETFs, funds, etc.)
- ✅ Position type inference (equity, bond FX, structured product, etc.)
- ✅ Position row parsing (full end-to-end)
- ⏳ Integration test (requires real PDF)

---

## 📄 Testing with Real PDFs

### Step 1: Prepare Test PDF

Place a sample valuation PDF in the fixtures folder:

```bash
mkdir -p tests/fixtures
# Copy your PDF to: tests/fixtures/sample_valuation.pdf
```

### Step 2: Run Integration Test

Uncomment the integration test and run:

```python
# In tests/test_pdf_parser_dynamic.py
# Remove the @pytest.mark.skip decorator from test_extract_positions_from_pdf()
```

```bash
pytest tests/test_pdf_parser_dynamic.py::test_extract_positions_from_pdf -v
```

### Step 3: Manual PDF Analysis

To analyze a PDF structure manually:

```python
import pdfplumber

with pdfplumber.open("path/to/valuation.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"\n=== PAGE {i+1} ===")

        # Show text
        text = page.extract_text()
        print(text[:500])  # First 500 chars

        # Show tables
        tables = page.extract_tables()
        print(f"\nTables found: {len(tables)}")

        for j, table in enumerate(tables):
            print(f"\nTable {j+1} (first 5 rows):")
            for row in table[:5]:
                print(row)
```

### Step 4: Test End-to-End Parsing

```python
from app.parsers import parse_pdf

# Parse PDF
with open("tests/fixtures/sample_valuation.pdf", "rb") as f:
    pdf_bytes = f.read()

portfolio_data = parse_pdf(pdf_bytes)

# Validate results
print(f"Total value: CHF {portfolio_data.total_value_chf:,.2f}")
print(f"Positions extracted: {len(portfolio_data.positions)}")

# Check each position
for pos in portfolio_data.positions:
    print(f"  - {pos.name} ({pos.asset_class.value}): CHF {pos.value_chf:,.2f}")
```

---

## 🔧 Testing MCP Server

### Local Server Test

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run server in dev mode (with inspector)
mcp dev mcp_server/server.py
```

The MCP inspector will open in your browser, allowing you to:
- View available tools
- View available resources
- Test tool calls manually
- See request/response payloads

### Test Tools Manually

Using Python:

```python
import asyncio
import base64
from mcp_server.tools import upload_portfolio, ask_portfolio

async def test():
    # Encode PDF
    with open("tests/fixtures/sample_valuation.pdf", "rb") as f:
        pdf_bytes = f.read()
        pdf_base64 = base64.b64encode(pdf_bytes).decode()

    # Test upload
    result = await upload_portfolio(pdf_base64, "sample.pdf", "default")
    print("Upload result:", result)

    session_id = result["session_id"]

    # Test Q&A
    answer = await ask_portfolio(session_id, "What is the total portfolio value?")
    print("Answer:", answer)

asyncio.run(test())
```

---

## 🖥️ Testing with Claude Desktop

### Step 1: Configure Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "numan-portfolio": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/absolute/path/to/finance-analysis",
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-your-key-here",
        "DATABASE_URL": "sqlite:///./numan.db"
      }
    }
  }
}
```

### Step 2: Restart Claude Desktop

Close and reopen Claude Desktop. The NUMAN tools should appear in the tools menu.

### Step 3: Test Workflow

1. **Upload a PDF**:
   ```
   Can you parse this valuation PDF for me?
   [Attach PDF file]
   ```

   Claude will call `upload_portfolio` and return the session_id.

2. **Ask questions**:
   ```
   What is the total portfolio value?
   Show me the asset allocation.
   What are the top 3 performers?
   List all equity positions.
   ```

   Claude will call `ask_portfolio` and display the results.

3. **Read resources**:
   ```
   Can you read the portfolio resource?
   ```

   Claude will use `portfolio://{session_id}` to load the data.

4. **Use prompts**:
   ```
   Give me a portfolio summary.
   ```

   Claude will use the `portfolio-summary` prompt template.

---

## 🧩 Testing Individual Components

### Test LLM Providers

```python
from app.llm import create_llm
import asyncio

async def test_llm():
    llm = create_llm()

    response = await llm.complete(
        system="You are a financial analyst.",
        user="What is a bond?"
    )

    print(response)

asyncio.run(test_llm())
```

### Test Database

```python
from app.database import get_session, Client, Portfolio
import uuid

with get_session() as session:
    # Create test client
    client = Client(
        id="test-client",
        name="Test Client",
        risk_profile="moderate"
    )
    session.add(client)
    session.commit()

    # Create test portfolio
    portfolio = Portfolio(
        id=str(uuid.uuid4()),
        client_id="test-client",
        valuation_date="2026-02-11",
        total_value_chf=1000000.0,
        data_json='{"positions": []}',
        pdf_filename="test.pdf"
    )
    session.add(portfolio)
    session.commit()

    print(f"Created portfolio: {portfolio.id}")
```

### Test Q&A Service

```python
from app.services.qa_service_llm import QAService
from app.llm import create_llm
import asyncio

async def test_qa():
    llm = create_llm()
    qa_service = QAService(llm)

    # Mock portfolio data
    portfolio_data = {
        "valuation_date": "2026-02-11",
        "total_value_chf": 1000000.0,
        "positions": [...]
    }

    response = await qa_service.ask(
        portfolio_data,
        "What is the total value?"
    )

    print(response)

asyncio.run(test_qa())
```

---

## 📊 Test Coverage

### Current Coverage (Phase 1)

```
app/parsers/pdf_table_extractor.py    ✅ 85% (unit tests)
app/parsers/valuation_pdf.py          ⚠️ 40% (needs integration test)
app/llm/                               ⏳ 0%  (needs mock tests)
app/services/qa_service_llm.py         ⏳ 0%  (needs mock tests)
mcp_server/tools.py                    ⏳ 0%  (needs mock tests)
app/database.py                        ⏳ 0%  (needs tests)
```

### To Improve Coverage

Create these tests in future sessions:

```bash
tests/
├── test_pdf_parser_dynamic.py     ✅ DONE
├── test_llm_providers.py          ⏳ TODO — Mock Claude/Ollama
├── test_qa_service.py             ⏳ TODO — Mock LLM responses
├── test_mcp_tools.py              ⏳ TODO — Mock database
├── test_database.py               ⏳ TODO — Test CRUD operations
└── fixtures/
    └── sample_valuation.pdf       ⏳ TODO — Real PDF for testing
```

---

## 🐛 Common Issues & Solutions

### Issue: pdfplumber can't find tables

**Symptom**: `extract_tables()` returns empty list

**Solutions**:
1. Check if PDF has actual tables (not just text formatted as table)
2. Try adjusting table detection settings:
   ```python
   tables = page.extract_tables(table_settings={
       "vertical_strategy": "lines",
       "horizontal_strategy": "lines",
   })
   ```
3. Fall back to text extraction with regex

### Issue: Asset class misclassified

**Symptom**: Position classified as wrong asset class

**Solutions**:
1. Check the inference logic in `infer_asset_class()`
2. Add more specific patterns for edge cases
3. Update ISIN_TICKER_MAP if it's a known security

### Issue: Number parsing fails

**Symptom**: Values are 0.0 or incorrect

**Solutions**:
1. Check Swiss formatting (apostrophe vs comma)
2. Handle different thousand separators
3. Add debug logging to `_parse_number()`

### Issue: Missing positions

**Symptom**: Some positions not extracted

**Solutions**:
1. Check if table headers are detected correctly
2. Verify header names match expected patterns
3. Add more header name variations to `parse_position_row()`

---

## 📝 Test Checklist

Before moving to Phase 2, verify:

- [ ] Unit tests pass: `pytest tests/test_pdf_parser_dynamic.py`
- [ ] MCP server starts: `python -m mcp_server.server`
- [ ] Database initializes: Check `numan.db` created
- [ ] LLM provider works: Test with mock or real API key
- [ ] Integration test passes with real PDF
- [ ] Claude Desktop integration works
- [ ] All documentation up to date

---

## 🚀 Next: Phase 2 Testing

When implementing Phase 2 analysis tools:

1. **Create test fixtures** for market data (mock yfinance responses)
2. **Test each calculator** independently (risk, momentum, correlation)
3. **Test MCP tool wrappers** with mocked calculators
4. **Test with real market data** (optional, can be slow)
5. **Validate against Finance-Guru** reference implementations

See `NEXT_STEPS.md` for Phase 2 implementation plan.

---

**Last Updated**: February 11, 2026 15:45
