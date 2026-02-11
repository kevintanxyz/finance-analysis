"""
PDF Parser Router — Intelligent format detection and parsing strategy.

Routes PDF extraction based on bank format detection:
- Known formats (NUMAN) → pdfplumber (fast, free)
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

# MVP: Use Claude Vision for all formats
# TODO: Enable hybrid mode after validating Claude Vision accuracy
USE_CLAUDE_VISION_ONLY = True  # Set False to enable hybrid pdfplumber + LLM


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
        Extract using both pdfplumber + Claude Vision, then cross-validate.

        Strategy:
        1. Try pdfplumber (fast, free)
        2. Run Claude Vision in parallel
        3. Cross-validate results
        4. Return best result or merged result
        """
        if self.verbose:
            print("🔄 Running hybrid extraction (pdfplumber + Claude Vision)...")

        # Extract with pdfplumber
        try:
            pdfplumber_result, _ = await self._extract_with_pdfplumber(
                pdf_bytes, bank_config
            )
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  pdfplumber failed: {e}")
            pdfplumber_result = None

        # Extract with Claude Vision
        llm_result, _ = await self._extract_with_llm(pdf_bytes, bank_config)

        # Cross-validate
        validation = self.validator.compare(pdfplumber_result, llm_result)

        if self.verbose:
            print(f"   Cross-validation confidence: {validation.confidence_score:.2f}")

        # Choose best result
        if not pdfplumber_result:
            return llm_result, validation

        # If high agreement, prefer pdfplumber (faster, cheaper)
        if validation.confidence_score > 0.9:
            if self.verbose:
                print("   ✅ High confidence → using pdfplumber result")
            return pdfplumber_result, validation

        # Otherwise use Claude Vision (more accurate)
        if self.verbose:
            print("   ⚠️  Low confidence → using Claude Vision result")
        return llm_result, validation


# ────────────────────────────────────────────────────────────────────────────
# Helper to open PDF from bytes
# ────────────────────────────────────────────────────────────────────────────


def open_pdf(pdf_bytes: bytes):
    """Open PDF from bytes (pdfplumber helper)."""
    from io import BytesIO
    return pdfplumber.open(BytesIO(pdf_bytes))


# Monkey-patch pdfplumber to support bytes directly
pdfplumber.open_pdf = open_pdf
