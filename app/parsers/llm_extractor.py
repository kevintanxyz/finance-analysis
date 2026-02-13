"""
LLM-based PDF extraction using Claude Vision API.

This module uses Claude's vision capabilities to extract structured
portfolio data directly from PDF images. Works with any format.
"""
import base64
import hashlib
import json
from io import BytesIO
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
from app.llm import LLMProvider
from app.models.portfolio import Position, PortfolioData, AssetClass, PositionType
from app.parsers.bank_configs import BankConfig


# ────────────────────────────────────────────────────────────────────────────
# Extraction System Prompt
# ────────────────────────────────────────────────────────────────────────────

EXTRACTION_SYSTEM_PROMPT = """You are a financial data extraction expert specialized in portfolio statements.

**CRITICAL**: You will receive ALL pages of this multi-page document. You MUST scan through EVERY page to extract ALL data sections:
- Portfolio positions (usually first pages)
- Asset allocation, currency/regional/sector exposure
- Performance history, tops/flops
- P&L overview and detail
- **TRANSACTIONS** (usually last pages) - CRITICAL: DO NOT skip transaction history!

Extract ALL portfolio positions and financial data from this complete document.

Return ONLY valid JSON matching this exact schema:

{
  "valuation_date": "YYYY-MM-DD",
  "reference_currency": "CHF|USD|EUR|GBP|...",  // Extract from document
  "total_value": 0.00,
  "total_pnl": 0.00,
  "total_pnl_pct": 0.00,

  "allocation": {
    "cash": {"pct": 0.00, "value": 0.00},
    "bonds": {"pct": 0.00, "value": 0.00},
    "equities": {"pct": 0.00, "value": 0.00},
    "structured_products": {"pct": 0.00, "value": 0.00},
    "other": {"pct": 0.00, "value": 0.00}
  },

  "positions": [
    {
      "name": "str",
      "isin": "str or null",
      "asset_class": "cash|bond|equity|structured|fund|other",
      "currency": "CHF|USD|EUR|GBP|...",  // Position currency
      "quantity": 0.00,
      "purchase_price": 0.00,
      "current_price": 0.00,
      "value": 0.00,  // Value in reference_currency (NOT hardcoded CHF)
      "pnl": 0.00,
      "pnl_pct": 0.00,
      "weight_pct": 0.00,
      "maturity_date": "YYYY-MM-DD or null",
      "coupon_rate": 0.00,
      "ticker": "str or null"
    }
  ],

  "currency_exposure": [
    {"currency": "CHF|USD|EUR|...", "pct": 0.00, "value": 0.00}
  ],

  "regional_exposure": [
    {"region": "str", "pct": 0.00, "value": 0.00}
  ],

  "sector_exposure": [
    {"sector": "str", "pct": 0.00, "value": 0.00}
  ],

  "tops": [
    {"name": "str", "currency": "CHF|USD|EUR|...", "pct": 0.00}
  ],

  "flops": [
    {"name": "str", "currency": "CHF|USD|EUR|...", "pct": 0.00}
  ],

  "performance": [
    {
      "from_date": "DD/MM/YYYY",
      "to_date": "DD/MM/YYYY",
      "start_value": 0.00,
      "end_value": 0.00,
      "deposits": 0.00,
      "withdrawals": 0.00,
      "profit_loss": 0.00,
      "cum_pnl": 0.00,
      "performance_pct": 0.00,
      "cum_perf_pct": 0.00
    }
  ],

  "pnl_overview": {
    "assets_end": 0.00,
    "deposits_cash": 0.00,
    "withdrawals_cash": 0.00,
    "total_deposits_withdrawals": 0.00,
    "total_pnl_pct": 0.00,
    "total_pnl_value": 0.00
  },

  "pnl_detail": {
    "unrealized_market_pnl": 0.00,
    "unrealized_fx_pnl": 0.00,
    "unrealized_interests": 0.00,
    "realized_dividends": 0.00,
    "portfolio_management_fees": 0.00,
    "total_bank_fees": 0.00,
    "withholding_taxes": 0.00,
    "total_pnl": 0.00
  },

  "transactions": [
    {
      "date": "DD/MM/YYYY",
      "instrument": "str",
      "operation_type": "Buy|Sell|Subscription|Redemption",
      "amount": 0.00,
      "price": 0.00,
      "settlement_ccy": "CHF|USD|EUR|...",
      "op_value": 0.00
    }
  ]
}

**Critical Rules:**
1. Extract ALL positions, even without ISINs
2. **reference_currency**: Extract from document header (e.g., "Portfolio CHF", "Portfolio USD")
3. **value**: Position value in reference_currency (NOT always CHF!)
4. **IMPORTANT**: If a section is not found in the document, return empty arrays [] or zero values, but ALWAYS include the field
5. For bonds: extract maturity_date and coupon_rate if available
6. For equities: infer ticker if possible (e.g., ISIN CH0012032048 → ROG.SW)
7. Verify: sum of position values ≈ total_value (±1% tolerance)
8. Asset class inference:
   - Bonds: Look for coupon rates (e.g., "4.85%"), maturity years (e.g., "2033")
   - Equities: Company names ending in AG, Inc, SE, SA, GmbH, Ltd
   - ETFs: Names containing "ETF", "UCITS", "Index"
   - Funds: Names containing "Fund", "Fonds", "FCP"
   - Structured: Names with "Note", "Certificate"
9. Swiss number format: use apostrophe (2'988.44) or period (2988.44) as thousand separator
10. Percentages: already in 0-100 range (e.g., 10.5 means 10.5%)
11. **TOPS/FLOPS**: Look for sections titled "Tops, Perf. YTD" or "Best performers" and "Flops, Perf. YTD" or "Worst performers"
12. **PERFORMANCE**: Look for tables with columns like "From", "To", "Start Value", "End Value", "Performance", etc.
13. **EXPOSURES**: Look for sections titled "Currencies", "Regions", "Sectors" with breakdown tables
14. **P&L**: Look for "PROFIT & LOSS" sections with overview and detailed breakdown
15. **TRANSACTIONS (CRITICAL - Often on last pages)**:
    - Look for sections titled "TRANSACTIONS", "Transaction History", "Mouvements", "Operations"
    - Typically found on the LAST pages of the statement (pages 15-18 in an 18-page document)
    - Extract ALL transactions with: date, instrument name, operation type (Buy/Sell/Subscription/Redemption), amount, price, currency, total value
    - IMPORTANT: Scan through ALL pages - don't stop after positions page!
    - If no transactions found, return empty array [] but you MUST check all pages first

**IMPORTANT**: Return ONLY the JSON object. No markdown code blocks, no explanation text.
"""


# ────────────────────────────────────────────────────────────────────────────
# LLM PDF Extractor
# ────────────────────────────────────────────────────────────────────────────


class LLMPDFExtractor:
    """
    Extract structured portfolio data from PDFs using Claude Vision.

    This extractor sends PDF pages as images to Claude, which returns
    structured JSON matching our Pydantic schema. Works with any format.
    """

    def __init__(
        self,
        llm: LLMProvider,
        verbose: bool = False,
        cache_dir: Optional[str] = None,
        use_cache: bool = True,
    ):
        """
        Initialize extractor.

        Args:
            llm: LLM provider (must support vision)
            verbose: Print extraction progress
            cache_dir: Directory to cache API responses (default: ./cache/claude_vision)
            use_cache: Use cached responses if available (default: True)
        """
        self.llm = llm
        self.verbose = verbose
        self.use_cache = use_cache

        # Setup cache directory
        if cache_dir is None:
            cache_dir = "./cache/claude_vision"
        self.cache_dir = Path(cache_dir)
        if use_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def extract(
        self,
        pdf_bytes: bytes,
        bank_config: Optional[BankConfig] = None,
        isin_ticker_map: Optional[dict] = None,
    ) -> PortfolioData:
        """
        Extract portfolio data from PDF using Claude Vision.

        Args:
            pdf_bytes: PDF file as bytes
            bank_config: Optional bank-specific configuration
            isin_ticker_map: Optional ISIN → ticker mapping

        Returns:
            PortfolioData validated by Pydantic

        Raises:
            ValueError: If extraction fails or JSON is invalid
        """
        if self.verbose:
            print("🖼️  Converting PDF pages to images...")

        # Step 1: Convert PDF pages to images
        images_b64 = self._pdf_to_images_base64(pdf_bytes)

        if self.verbose:
            print(f"   → {len(images_b64)} pages converted")

        # Step 2: Build extraction prompt with bank context
        system_prompt = EXTRACTION_SYSTEM_PROMPT
        if bank_config and bank_config.extra_prompt:
            system_prompt += f"\n\n**Bank-Specific Context:**\n{bank_config.extra_prompt}"

        user_prompt = f"""Extract all portfolio data from these {len(images_b64)} document pages.

**IMPORTANT**:
- This is a complete {len(images_b64)}-page statement
- Scan through EVERY page from page 1 to page {len(images_b64)}
- Transactions are typically on the LAST pages (pages {max(1, len(images_b64) - 3)} to {len(images_b64)})
- DO NOT stop extracting after positions - continue to ALL pages to find transactions, performance, P&L sections

Return the complete JSON with ALL sections filled from all {len(images_b64)} pages."""

        # Step 3: Check cache or call Claude Vision
        cache_key = self._get_cache_key(pdf_bytes)
        cached_response = self._load_from_cache(cache_key)

        if cached_response is not None:
            if self.verbose:
                print("💾 Using cached response (no API call)")
            response_text = cached_response
        else:
            if self.verbose:
                print("🤖 Sending to Claude Vision for extraction...")

            response_text = await self.llm.complete_with_images(
                system=system_prompt,
                user=user_prompt,
                images_b64=images_b64,
                response_format="json",
            )

            if self.verbose:
                print("   → Received structured data from LLM")

            # Save to cache
            self._save_to_cache(cache_key, response_text)

        # Step 4: Parse and validate JSON
        try:
            portfolio_dict = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON: {e}\n\nResponse: {response_text[:500]}")

        # Step 5: Convert to Pydantic models
        portfolio_data = self._dict_to_portfolio_data(portfolio_dict, isin_ticker_map)

        if self.verbose:
            print(f"✅ Extracted {len(portfolio_data.positions)} positions")

        return portfolio_data

    def _get_cache_key(self, pdf_bytes: bytes) -> str:
        """Generate cache key from PDF content hash."""
        return hashlib.sha256(pdf_bytes).hexdigest()

    def _save_to_cache(self, cache_key: str, response_text: str) -> None:
        """Save API response to cache file."""
        if not self.use_cache:
            return

        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            cache_file.write_text(response_text, encoding="utf-8")
            if self.verbose:
                print(f"   💾 Saved to cache: {cache_file.name}")
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  Failed to save cache: {e}")

    def _load_from_cache(self, cache_key: str) -> Optional[str]:
        """Load API response from cache if available."""
        if not self.use_cache:
            return None

        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                return cache_file.read_text(encoding="utf-8")
            except Exception as e:
                if self.verbose:
                    print(f"   ⚠️  Failed to load cache: {e}")
        return None

    def _pdf_to_images_base64(self, pdf_bytes: bytes, dpi: int = 150) -> list[str]:
        """
        Convert PDF pages to base64-encoded PNG images.

        Args:
            pdf_bytes: PDF file as bytes
            dpi: Resolution for image rendering

        Returns:
            List of base64-encoded PNG images (one per page)
        """
        images_b64 = []

        # Open PDF with PyMuPDF
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

        for page_num in range(len(pdf_document)):
            # Render page to image
            page = pdf_document[page_num]
            mat = fitz.Matrix(dpi / 72, dpi / 72)  # 72 DPI is default
            pix = page.get_pixmap(matrix=mat)

            # Convert to PNG bytes
            img_bytes = pix.tobytes("png")

            # Encode to base64
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            images_b64.append(img_b64)

        pdf_document.close()

        return images_b64

    def _dict_to_portfolio_data(
        self,
        data: dict,
        isin_ticker_map: Optional[dict] = None,
    ) -> PortfolioData:
        """
        Convert LLM-extracted dict to PortfolioData.

        Args:
            data: Dict from LLM (validated against schema)
            isin_ticker_map: Optional ISIN → ticker mapping

        Returns:
            Validated PortfolioData object
        """
        from app.models.portfolio import (
            AllocationItem, ExposureItem, TopFlop, PerformancePeriod,
            PnLOverview, PnLDetail, Transaction
        )

        isin_ticker_map = isin_ticker_map or {}

        # Parse positions
        positions = []
        for pos_dict in data.get("positions", []):
            # Map asset class string to enum
            asset_class_str = pos_dict.get("asset_class", "other").lower()
            asset_class = self._parse_asset_class(asset_class_str)

            # Map position type
            position_type = self._infer_position_type(pos_dict, asset_class)

            # Enrich ticker from ISIN if available
            isin = pos_dict.get("isin")
            ticker = pos_dict.get("ticker")
            is_listed = False

            if isin and isin in isin_ticker_map:
                ticker, is_listed = isin_ticker_map[isin]
            elif ticker:
                is_listed = True  # LLM inferred a ticker

            position = Position(
                asset_class=asset_class,
                position_type=position_type,
                currency=pos_dict.get("currency", "CHF"),
                isin=isin,
                name=pos_dict.get("name", "Unknown Position"),
                quantity=pos_dict.get("quantity"),
                cost_price=pos_dict.get("purchase_price"),
                quote=pos_dict.get("current_price"),
                # Accept both "value" (new) and "value_chf" (legacy) for backward compat
                value_chf=pos_dict.get("value") or pos_dict.get("value_chf", 0.0),
                weight_pct=pos_dict.get("weight_pct", 0.0),
                ticker=ticker,
                is_listed=is_listed,
                # Bond-specific
                maturity_date=pos_dict.get("maturity_date"),
                coupon_rate=pos_dict.get("coupon_rate"),
                # P&L
                pnl=pos_dict.get("pnl"),
                pnl_pct=pos_dict.get("pnl_pct"),
            )
            positions.append(position)

        # Parse asset allocation (convert from nested dict to list)
        asset_allocation = []
        allocation_dict = data.get("allocation", {})
        if allocation_dict:
            for asset_class_key, values in allocation_dict.items():
                if values and isinstance(values, dict):
                    asset_allocation.append(AllocationItem(
                        asset_class=asset_class_key.replace("_", " ").title(),  # "structured_products" → "Structured Products"
                        value_chf=values.get("value", 0.0),
                        weight_pct=values.get("pct", 0.0),
                    ))

        # Parse currency exposure
        currency_exposure = [
            ExposureItem(
                name=exp.get("currency", ""),
                value_chf=exp.get("value", 0.0),
                weight_pct=exp.get("pct", 0.0),
            )
            for exp in data.get("currency_exposure", [])
        ]

        # Parse regional exposure
        regional_exposure = [
            ExposureItem(
                name=exp.get("region", ""),
                value_chf=exp.get("value", 0.0),
                weight_pct=exp.get("pct", 0.0),
            )
            for exp in data.get("regional_exposure", [])
        ]

        # Parse sector exposure
        sector_exposure = [
            ExposureItem(
                name=exp.get("sector", ""),
                value_chf=exp.get("value", 0.0),
                weight_pct=exp.get("pct", 0.0),
            )
            for exp in data.get("sector_exposure", [])
        ]

        # Parse tops/flops
        tops = [
            TopFlop(
                name=t.get("name", ""),
                currency=t.get("currency", "CHF"),
                pct=t.get("pct", 0.0),
            )
            for t in data.get("tops", [])
        ]

        flops = [
            TopFlop(
                name=f.get("name", ""),
                currency=f.get("currency", "CHF"),
                pct=f.get("pct", 0.0),
            )
            for f in data.get("flops", [])
        ]

        # Parse performance periods
        performance = [
            PerformancePeriod(
                from_date=p.get("from_date", ""),
                to_date=p.get("to_date", ""),
                start_value=p.get("start_value", 0.0),
                end_value=p.get("end_value", 0.0),
                deposits=p.get("deposits", 0.0),
                withdrawals=p.get("withdrawals", 0.0),
                profit_loss=p.get("profit_loss", 0.0),
                cum_pnl=p.get("cum_pnl", 0.0),
                performance_pct=p.get("performance_pct", 0.0),
                cum_perf_pct=p.get("cum_perf_pct", 0.0),
            )
            for p in data.get("performance", [])
        ]

        # Parse P&L overview
        pnl_overview_dict = data.get("pnl_overview", {})
        pnl_overview = PnLOverview(
            assets_end=pnl_overview_dict.get("assets_end", 0.0),
            deposits_cash=pnl_overview_dict.get("deposits_cash", 0.0),
            withdrawals_cash=pnl_overview_dict.get("withdrawals_cash", 0.0),
            total_deposits_withdrawals=pnl_overview_dict.get("total_deposits_withdrawals", 0.0),
            total_pnl_pct=pnl_overview_dict.get("total_pnl_pct", 0.0),
            total_pnl_value=pnl_overview_dict.get("total_pnl_value", 0.0),
        )

        # Parse P&L detail
        pnl_detail_dict = data.get("pnl_detail", {})
        pnl_detail = PnLDetail(
            unrealized_market_pnl=pnl_detail_dict.get("unrealized_market_pnl", 0.0),
            unrealized_fx_pnl=pnl_detail_dict.get("unrealized_fx_pnl", 0.0),
            unrealized_interests=pnl_detail_dict.get("unrealized_interests", 0.0),
            realized_dividends=pnl_detail_dict.get("realized_dividends", 0.0),
            portfolio_management_fees=pnl_detail_dict.get("portfolio_management_fees", 0.0),
            total_bank_fees=pnl_detail_dict.get("total_bank_fees", 0.0),
            withholding_taxes=pnl_detail_dict.get("withholding_taxes", 0.0),
            total_pnl=pnl_detail_dict.get("total_pnl", 0.0),
        )

        # Parse transactions
        transactions = [
            Transaction(
                date=t.get("date", ""),
                instrument=t.get("instrument", ""),
                operation_type=t.get("operation_type", ""),
                amount=t.get("amount", 0.0),
                price=t.get("price", 0.0),
                settlement_ccy=t.get("settlement_ccy", "CHF"),
                op_value=t.get("op_value", 0.0),
            )
            for t in data.get("transactions", [])
        ]

        # Build complete PortfolioData
        portfolio_data = PortfolioData(
            valuation_date=data.get("valuation_date", ""),
            extraction_date=data.get("valuation_date", ""),  # Same as valuation date
            total_value_chf=data.get("total_value", 0.0),
            positions=positions,
            asset_allocation=asset_allocation,
            currency_exposure=currency_exposure,
            regional_exposure=regional_exposure,
            sector_exposure=sector_exposure,
            tops=tops,
            flops=flops,
            performance=performance,
            pnl_overview=pnl_overview,
            pnl_detail=pnl_detail,
            transactions=transactions,
        )

        return portfolio_data

    def _parse_asset_class(self, asset_class_str: str) -> AssetClass:
        """Map string to AssetClass enum."""
        mapping = {
            "cash": AssetClass.CASH,
            "bond": AssetClass.BONDS,
            "bonds": AssetClass.BONDS,
            "equity": AssetClass.EQUITIES,
            "equities": AssetClass.EQUITIES,
            "structured": AssetClass.STRUCTURED_PRODUCTS,
            "structured_products": AssetClass.STRUCTURED_PRODUCTS,
            "fund": AssetClass.OTHERS,  # Funds go to OTHERS
            "other": AssetClass.OTHERS,
        }
        return mapping.get(asset_class_str.lower(), AssetClass.OTHERS)

    def _infer_position_type(self, pos_dict: dict, asset_class: AssetClass) -> PositionType:
        """Infer position type from asset class and name."""
        name = pos_dict.get("name", "").upper()

        if asset_class == AssetClass.CASH:
            return PositionType.CASH_ACCOUNT

        if asset_class == AssetClass.BONDS:
            # Differentiate between bond funds and direct bonds
            if "FUND" in name or "FONDS" in name or "SICAV" in name:
                return PositionType.BOND_FUND
            return PositionType.BOND_FX  # Direct bonds/FX bonds

        if asset_class == AssetClass.EQUITIES:
            if "ETF" in name or "UCITS" in name or "INDEX" in name:
                return PositionType.ETF
            return PositionType.EQUITY

        if asset_class == AssetClass.STRUCTURED_PRODUCTS:
            # All structured products map to STRUCTURED_PRODUCT
            return PositionType.STRUCTURED_PRODUCT

        # Others: funds, commodities, etc.
        if "FUND" in name or "FONDS" in name or "FCP" in name:
            return PositionType.FUND
        if "GOLD" in name or "SILVER" in name or "COMMODITY" in name:
            return PositionType.COMMODITY

        return PositionType.OTHER
