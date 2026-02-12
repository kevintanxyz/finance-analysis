"""
PDF Parser Router — Intelligent format detection and parsing strategy.

Routes PDF extraction based on bank format detection:
- Known formats (WealthPoint) → pdfplumber (fast, free)
- Unknown formats (UBS, Julius Baer) → Claude Vision (smart, paid)
- Hybrid mode → Both + cross-validation

**MVP Configuration:** For now, all formats use Claude Vision only.
This can be changed later by setting USE_HYBRID_MODE = True.
"""
import pdfplumber
from typing import Optional

from app.llm import LLMProvider
from app.models.portfolio import PortfolioData
from app.parsers.bank_configs import detect_bank, BankConfig
from app.parsers.llm_extractor import LLMPDFExtractor
from app.parsers.pdf_table_extractor import extract_positions_from_tables
from app.parsers.cross_validator import CrossValidator, ValidationResult


# ────────────────────────────────────────────────────────────────────────────
# Router Configuration
# ────────────────────────────────────────────────────────────────────────────

# Vision-Only Mode (Production): Claude Vision extracts all sections
# - Pros: Comprehensive extraction, handles any format
# - Cons: API costs (~$0.01 per 18-page PDF)
#
# Hybrid Mode: Vision (primary) + pdfplumber (fallback verification)
# - Pros: pdfplumber fills gaps if Vision misses something
# - Cons: Slightly slower (runs both extractors)
#
# Current status: Vision extracts all sections successfully, so hybrid is optional
USE_CLAUDE_VISION_ONLY = True  # Set False to enable hybrid mode


# ────────────────────────────────────────────────────────────────────────────
# PDF Parser Router
# ────────────────────────────────────────────────────────────────────────────


class PDFParserRouter:
    """
    Intelligent PDF parser router.

    Detects bank format and chooses optimal parsing strategy:
    1. Detect bank from PDF text
    2. Choose strategy: pdfplumber, Claude Vision, or hybrid
    3. Extract data using chosen strategy
    4. Validate and return

    **MVP Mode:** Currently uses Claude Vision for all formats.
    """

    def __init__(
        self,
        llm: LLMProvider,
        isin_ticker_map: Optional[dict] = None,
        verbose: bool = False,
        use_cache: bool = True,
    ):
        """
        Initialize router.

        Args:
            llm: LLM provider (must support vision)
            isin_ticker_map: ISIN → (ticker, is_listed) mapping
            verbose: Print routing decisions and progress
            use_cache: Cache Claude Vision API responses (default: True)
        """
        self.llm = llm
        self.isin_ticker_map = isin_ticker_map or {}
        self.verbose = verbose
        self.use_cache = use_cache
        self.validator = CrossValidator()

    async def parse(
        self,
        pdf_bytes: bytes,
        filename: str = "valuation.pdf",
    ) -> tuple[PortfolioData, dict]:
        """
        Parse PDF using optimal strategy based on format.

        Args:
            pdf_bytes: PDF file as bytes
            filename: Original filename (for logging)

        Returns:
            Tuple of (portfolio_data, parsing_summary)
            - portfolio_data: Validated PortfolioData
            - parsing_summary: Dict with strategy used, confidence, warnings
        """
        if self.verbose:
            print(f"\n📄 Parsing PDF: {filename}")

        # Step 1: Detect bank format
        bank_config = self._detect_bank_format(pdf_bytes)

        if self.verbose:
            print(f"🏦 Detected bank: {bank_config.name}")
            print(f"📋 Preferred strategy: {bank_config.parser}")

        # Step 2: Choose parsing strategy
        # MVP: Always use Claude Vision
        if USE_CLAUDE_VISION_ONLY:
            if self.verbose:
                print("🔧 MVP Mode: Using Claude Vision for all formats")
            strategy = "llm_vision"
        else:
            strategy = self._choose_strategy(bank_config)

        if self.verbose:
            print(f"✨ Using strategy: {strategy}")

        # Step 3: Extract data
        portfolio_data, validation = await self._extract_with_strategy(
            pdf_bytes, bank_config, strategy
        )

        # Step 4: Build summary
        summary = {
            "filename": filename,
            "bank_detected": bank_config.name,
            "strategy_used": strategy,
            "confidence_score": validation.confidence_score,
            "is_valid": validation.is_valid,
            "warnings": validation.warnings,
            "errors": validation.errors,
            "metrics": validation.metrics,
        }

        if self.verbose:
            print(f"\n✅ Parsing complete")
            print(f"   Strategy: {strategy}")
            print(f"   Confidence: {validation.confidence_score:.2f}")
            print(f"   Positions: {len(portfolio_data.positions)}")
            if validation.warnings:
                print(f"   ⚠️  {len(validation.warnings)} warnings")
            if validation.errors:
                print(f"   ❌ {len(validation.errors)} errors")

        return portfolio_data, summary

    def _detect_bank_format(self, pdf_bytes: bytes) -> BankConfig:
        """
        Detect which bank issued the PDF.

        Args:
            pdf_bytes: PDF file as bytes

        Returns:
            BankConfig for detected bank
        """
        # Extract text from first page for detection
        with pdfplumber.open_pdf(pdf_bytes) as pdf:
            if not pdf.pages:
                raise ValueError("PDF has no pages")

            first_page_text = pdf.pages[0].extract_text() or ""

            # Check first 3 pages for keywords
            text_sample = first_page_text
            if len(pdf.pages) > 1:
                text_sample += "\n" + (pdf.pages[1].extract_text() or "")
            if len(pdf.pages) > 2:
                text_sample += "\n" + (pdf.pages[2].extract_text() or "")

        bank_config = detect_bank(text_sample)

        return bank_config

    def _choose_strategy(self, bank_config: BankConfig) -> str:
        """
        Choose parsing strategy based on bank config.

        Args:
            bank_config: Detected bank configuration

        Returns:
            Strategy name: "pdfplumber", "llm_vision", or "hybrid"
        """
        # MVP: Override all to Claude Vision
        if USE_CLAUDE_VISION_ONLY:
            return "llm_vision"

        # Production logic (when hybrid mode enabled):
        return bank_config.parser

    async def _extract_with_strategy(
        self,
        pdf_bytes: bytes,
        bank_config: BankConfig,
        strategy: str,
    ) -> tuple[PortfolioData, ValidationResult]:
        """
        Extract data using chosen strategy.

        Args:
            pdf_bytes: PDF file as bytes
            bank_config: Bank configuration
            strategy: Parsing strategy to use

        Returns:
            Tuple of (portfolio_data, validation_result)
        """
        if strategy == "llm_vision":
            return await self._extract_with_llm(pdf_bytes, bank_config)

        elif strategy == "pdfplumber":
            return await self._extract_with_pdfplumber(pdf_bytes, bank_config)

        elif strategy == "hybrid":
            return await self._extract_hybrid(pdf_bytes, bank_config)

        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    async def _extract_with_llm(
        self,
        pdf_bytes: bytes,
        bank_config: BankConfig,
    ) -> tuple[PortfolioData, ValidationResult]:
        """Extract using Claude Vision only."""
        extractor = LLMPDFExtractor(
            self.llm,
            verbose=self.verbose,
            use_cache=self.use_cache,
        )

        portfolio = await extractor.extract(
            pdf_bytes,
            bank_config=bank_config,
            isin_ticker_map=self.isin_ticker_map,
        )

        validation = self.validator.validate(portfolio)

        return portfolio, validation

    async def _extract_with_pdfplumber(
        self,
        pdf_bytes: bytes,
        bank_config: BankConfig,
    ) -> tuple[PortfolioData, ValidationResult]:
        """Extract using pdfplumber only."""
        with pdfplumber.open_pdf(pdf_bytes) as pdf:
            positions = extract_positions_from_tables(
                pdf,
                self.isin_ticker_map,
                table_settings=bank_config.table_settings,
            )

        if not positions:
            raise ValueError("pdfplumber failed to extract any positions")

        # Build minimal PortfolioData
        total_value = sum(p.value_chf for p in positions)

        portfolio = PortfolioData(
            valuation_date="",  # Not extracted by pdfplumber
            total_value_chf=total_value,
            positions=positions,
        )

        validation = self.validator.validate(portfolio)

        return portfolio, validation

    async def _extract_hybrid(
        self,
        pdf_bytes: bytes,
        bank_config: BankConfig,
    ) -> tuple[PortfolioData, ValidationResult]:
        """
        Extract using both Claude Vision (primary) + pdfplumber (fallback).

        Strategy:
        1. Extract with Claude Vision (comprehensive)
        2. Extract with pdfplumber (specific sections as verification)
        3. Merge results (Vision primary, pdfplumber fills gaps)
        4. Validate merged result
        """
        if self.verbose:
            print("🔄 Running hybrid extraction (Claude Vision + pdfplumber fallback)...")

        # Step 1: Extract with Claude Vision (primary)
        vision_result, _ = await self._extract_with_llm(pdf_bytes, bank_config)

        if self.verbose:
            vision_sections = self._count_non_empty_sections(vision_result)
            print(f"   📊 Vision extracted {vision_sections} sections")

        # Step 2: Extract with pdfplumber (fallback for missing sections)
        pdfplumber_result = None
        try:
            # For pdfplumber, we need to use ValuationPDFParser for full extraction
            import tempfile
            import os
            from app.parsers.valuation_pdf import ValuationPDFParser

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(pdf_bytes)
                tmp_path = tmp.name

            try:
                parser = ValuationPDFParser(tmp_path)
                pdfplumber_result = parser.parse()

                if self.verbose:
                    pdfplumber_sections = self._count_non_empty_sections(pdfplumber_result)
                    print(f"   📄 pdfplumber extracted {pdfplumber_sections} sections")
            finally:
                os.unlink(tmp_path)

        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  pdfplumber failed: {e}")

        # Step 3: Merge results (Vision primary, pdfplumber fills gaps)
        if pdfplumber_result:
            merged_result = self._merge_extractions(vision_result, pdfplumber_result)

            if self.verbose:
                merged_sections = self._count_non_empty_sections(merged_result)
                print(f"   ✅ Merged result has {merged_sections} sections")
        else:
            merged_result = vision_result

        # Step 4: Validate merged result
        validation = self.validator.validate(merged_result)

        if self.verbose:
            print(f"   Validation confidence: {validation.confidence_score:.2f}")

        return merged_result, validation

    def _merge_extractions(
        self,
        vision: PortfolioData,
        pdfplumber: PortfolioData,
    ) -> PortfolioData:
        """
        Merge Vision (primary) with pdfplumber (fallback).

        Rules:
        - If Vision extracted a section with data → Use Vision
        - If Vision section is empty BUT pdfplumber has data → Use pdfplumber
        - Positions: Always prefer Vision (better ISIN recognition)
        - Metadata: Prefer Vision (better date parsing)
        """
        merged = vision.model_copy(deep=True)

        # Asset Allocation - fill gaps from pdfplumber
        if not merged.asset_allocation and pdfplumber.asset_allocation:
            merged.asset_allocation = pdfplumber.asset_allocation
            if self.verbose:
                print("      → Filled asset_allocation from pdfplumber fallback")

        # Currency Exposure
        if not merged.currency_exposure and pdfplumber.currency_exposure:
            merged.currency_exposure = pdfplumber.currency_exposure
            if self.verbose:
                print("      → Filled currency_exposure from pdfplumber fallback")

        # Regional Exposure
        if not merged.regional_exposure and pdfplumber.regional_exposure:
            merged.regional_exposure = pdfplumber.regional_exposure
            if self.verbose:
                print("      → Filled regional_exposure from pdfplumber fallback")

        # Sector Exposure
        if not merged.sector_exposure and pdfplumber.sector_exposure:
            merged.sector_exposure = pdfplumber.sector_exposure
            if self.verbose:
                print("      → Filled sector_exposure from pdfplumber fallback")

        # Tops/Flops
        if not merged.tops and pdfplumber.tops:
            merged.tops = pdfplumber.tops
            if self.verbose:
                print("      → Filled tops from pdfplumber fallback")

        if not merged.flops and pdfplumber.flops:
            merged.flops = pdfplumber.flops
            if self.verbose:
                print("      → Filled flops from pdfplumber fallback")

        # Performance
        if not merged.performance and pdfplumber.performance:
            merged.performance = pdfplumber.performance
            if self.verbose:
                print("      → Filled performance from pdfplumber fallback")

        # P&L Overview
        if merged.pnl_overview.total_pnl_value == 0 and pdfplumber.pnl_overview.total_pnl_value != 0:
            merged.pnl_overview = pdfplumber.pnl_overview
            if self.verbose:
                print("      → Filled pnl_overview from pdfplumber fallback")

        # P&L Detail
        if merged.pnl_detail.total_pnl == 0 and pdfplumber.pnl_detail.total_pnl != 0:
            merged.pnl_detail = pdfplumber.pnl_detail
            if self.verbose:
                print("      → Filled pnl_detail from pdfplumber fallback")

        # Transactions
        if not merged.transactions and pdfplumber.transactions:
            merged.transactions = pdfplumber.transactions
            if self.verbose:
                print("      → Filled transactions from pdfplumber fallback")

        return merged

    def _count_non_empty_sections(self, portfolio: PortfolioData) -> int:
        """Count how many sections have data."""
        count = 0

        if portfolio.positions:
            count += 1
        if portfolio.asset_allocation:
            count += 1
        if portfolio.currency_exposure:
            count += 1
        if portfolio.regional_exposure:
            count += 1
        if portfolio.sector_exposure:
            count += 1
        if portfolio.tops:
            count += 1
        if portfolio.flops:
            count += 1
        if portfolio.performance:
            count += 1
        if portfolio.transactions:
            count += 1
        if portfolio.pnl_overview.total_pnl_value != 0:
            count += 1

        return count


# ────────────────────────────────────────────────────────────────────────────
# Helper to open PDF from bytes
# ────────────────────────────────────────────────────────────────────────────


def open_pdf(pdf_bytes: bytes):
    """Open PDF from bytes (pdfplumber helper)."""
    from io import BytesIO
    return pdfplumber.open(BytesIO(pdf_bytes))


# Monkey-patch pdfplumber to support bytes directly
pdfplumber.open_pdf = open_pdf
