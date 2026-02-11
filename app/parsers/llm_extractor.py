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

Extract ALL portfolio positions and financial data from this document.

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
  ]
}

**Critical Rules:**
1. Extract ALL positions, even without ISINs
2. **reference_currency**: Extract from document header (e.g., "Portfolio CHF", "Portfolio USD")
3. **value**: Position value in reference_currency (NOT always CHF!)
4. If field not found → null (never guess/invent)
4. For bonds: extract maturity_date and coupon_rate if available
5. For equities: infer ticker if possible (e.g., ISIN CH0012032048 → ROG.SW)
6. Verify: sum of position values ≈ total_value (±1% tolerance)
7. Asset class inference:
   - Bonds: Look for coupon rates (e.g., "4.85%"), maturity years (e.g., "2033")
   - Equities: Company names ending in AG, Inc, SE, SA, GmbH, Ltd
   - ETFs: Names containing "ETF", "UCITS", "Index"
   - Funds: Names containing "Fund", "Fonds", "FCP"
   - Structured: Names with "Note", "Certificate"
8. Swiss number format: use apostrophe (2'988.44) or period (2988.44) as thousand separator
9. Percentages: already in 0-100 range (e.g., 10.5 means 10.5%)

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

        user_prompt = "Extract all portfolio data from these document pages."

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

        # Build PortfolioData (simplified, only core fields)
        # Full implementation would parse allocation, exposure, etc.
        portfolio_data = PortfolioData(
            valuation_date=data.get("valuation_date", ""),
            total_value_chf=data.get("total_value", 0.0),
            positions=positions,
            # TODO: Parse allocation, exposure from data
            # For now, return minimal structure
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
