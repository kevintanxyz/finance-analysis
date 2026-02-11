"""
Enhanced PDF parser with Claude Vision + LLM validation.

This module combines:
1. Claude Vision for intelligent extraction (works with any format)
2. LLM validation for correction and enhancement (accurate, smart)
3. pdfplumber fallback for known formats (fast, free) — disabled in MVP

**Version 1.2 — Claude Vision Router**
- Detects bank format automatically (NUMAN, UBS, Julius Baer, etc.)
- Uses Claude Vision API to extract structured data from PDF images
- Validates extraction quality with cross-validation
- Optional LLM validation layer for OCR corrections
"""
import pdfplumber
from typing import Optional
from io import BytesIO
from app.models.portfolio import Position
from app.parsers.pdf_router import PDFParserRouter
from app.parsers.llm_validator import validate_positions_batch
from app.llm import LLMProvider


async def extract_positions_with_validation(
    pdf_bytes: bytes,
    isin_ticker_map: dict,
    total_value_chf: float,
    llm: LLMProvider,
    enable_llm_validation: bool = True,
    apply_corrections: bool = True,
    verbose: bool = False,
    filename: str = "valuation.pdf",
) -> tuple[list[Position], dict]:
    """
    Extract positions from PDF using Claude Vision + optional LLM validation.

    **Version 1.2 — Claude Vision Router:**
    1. Detects bank format (NUMAN, UBS, Julius Baer, generic)
    2. Extracts data using Claude Vision (sends PDF pages as images)
    3. Validates extraction quality
    4. (Optional) Applies LLM validation for OCR corrections

    Args:
        pdf_bytes: PDF file as bytes
        isin_ticker_map: Dict mapping ISIN -> (ticker, is_listed)
        total_value_chf: Expected total portfolio value
        llm: LLM provider (required for Claude Vision)
        enable_llm_validation: Whether to use additional LLM validation layer
        apply_corrections: Whether to apply LLM corrections
        verbose: Print progress
        filename: Original filename (for logging)

    Returns:
        Tuple of (positions, summary)
        - positions: List of validated Position objects
        - summary: Dict with extraction strategy, confidence, warnings

    Example:
        >>> from app.llm import create_llm
        >>> llm = create_llm()
        >>> with open("portfolio.pdf", "rb") as f:
        ...     pdf_bytes = f.read()
        >>> positions, summary = await extract_positions_with_validation(
        ...     pdf_bytes, ISIN_TICKER_MAP, 1000000.0, llm, verbose=True
        ... )
        >>> print(f"Bank: {summary['bank_detected']}")
        >>> print(f"Strategy: {summary['strategy_used']}")
        >>> print(f"Confidence: {summary['confidence_score']:.2f}")
    """
    if verbose:
        print("🖼️  Step 1: Extracting with Claude Vision router...")

    # Step 1: Extract using PDFParserRouter (Claude Vision)
    router = PDFParserRouter(
        llm=llm,
        isin_ticker_map=isin_ticker_map,
        verbose=verbose,
    )

    portfolio_data, parsing_summary = await router.parse(pdf_bytes, filename)

    positions = portfolio_data.positions

    if not positions:
        return [], {
            "total_positions": 0,
            "bank_detected": parsing_summary.get("bank_detected", "unknown"),
            "strategy_used": parsing_summary.get("strategy_used", "none"),
            "confidence_score": 0.0,
            "corrections_applied": 0,
            "warnings": ["No positions extracted from PDF"],
            "corrections": [],
            "portfolio_valid": False,
        }

    if verbose:
        print(f"   ✅ Extracted {len(positions)} positions")
        print(f"   🏦 Bank: {parsing_summary['bank_detected']}")
        print(f"   📋 Strategy: {parsing_summary['strategy_used']}")
        print(f"   🎯 Confidence: {parsing_summary['confidence_score']:.2f}")

    # Step 2: Optional LLM validation (OCR corrections, field inference)
    if enable_llm_validation:
        if verbose:
            print("🤖 Step 2: Applying LLM validation layer...")

        validated_positions, validation_summary = await validate_positions_batch(
            positions,
            llm,
            total_value_chf,
            apply_corrections=apply_corrections,
            verbose=verbose
        )

        # Merge summaries
        combined_summary = {
            **parsing_summary,  # Bank, strategy, confidence
            **validation_summary,  # Corrections, warnings
            "llm_validation_enabled": True,
        }

        return validated_positions, combined_summary

    else:
        # No additional LLM validation - return Claude Vision extraction
        if verbose:
            print("⚠️  Skipping additional LLM validation (disabled)")

        return positions, {
            **parsing_summary,
            "corrections_applied": 0,
            "corrections": [],
            "llm_validation_enabled": False,
        }


# ────────────────────────────────────────────────────────────────────────────
# Convenience function for common use case
# ────────────────────────────────────────────────────────────────────────────


async def parse_portfolio_pdf(
    pdf_path: str,
    isin_ticker_map: dict,
    total_value_chf: float,
    llm: LLMProvider,
    enable_llm_validation: bool = True,
    verbose: bool = False
) -> tuple[list[Position], dict]:
    """
    Parse a portfolio PDF file with Claude Vision + validation.

    Convenience function that handles PDF loading.

    **Version 1.2 — Claude Vision Router:**
    - Automatically detects bank format
    - Uses Claude Vision for intelligent extraction
    - Works with any PDF format (NUMAN, UBS, Julius Baer, etc.)

    Args:
        pdf_path: Path to PDF file
        isin_ticker_map: Dict mapping ISIN -> (ticker, is_listed)
        total_value_chf: Expected total portfolio value
        llm: LLM provider (required for Claude Vision)
        enable_llm_validation: Whether to use additional LLM validation layer
        verbose: Print progress

    Returns:
        Tuple of (positions, summary)

    Example:
        >>> from app.llm import create_llm
        >>> from app.parsers.valuation_pdf import ISIN_TICKER_MAP
        >>>
        >>> llm = create_llm()
        >>> positions, summary = await parse_portfolio_pdf(
        ...     "valuation.pdf",
        ...     ISIN_TICKER_MAP,
        ...     2988.44,
        ...     llm,
        ...     verbose=True
        ... )
        >>>
        >>> # Check results
        >>> print(f"Bank: {summary['bank_detected']}")
        >>> print(f"Strategy: {summary['strategy_used']}")
        >>> print(f"Total: {len(positions)} positions")
    """
    # Load PDF as bytes
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    filename = pdf_path.split("/")[-1]  # Extract filename

    return await extract_positions_with_validation(
        pdf_bytes,
        isin_ticker_map,
        total_value_chf,
        llm,
        enable_llm_validation,
        apply_corrections=True,
        verbose=verbose,
        filename=filename,
    )
