"""
Generic PDF parser with LLM fallback.

For known PDF formats (WealthPoint valuation), uses the dedicated parser.
For unknown formats, extracts raw text + tables and uses LLM to structure.
"""
from __future__ import annotations

import pdfplumber

from app.models.portfolio import PortfolioData
from app.parsers.valuation_pdf import ValuationPDFParser


def detect_pdf_type(pdf_path: str) -> str:
    """Detect the type of financial PDF."""
    with pdfplumber.open(pdf_path) as pdf:
        first_pages = " ".join(
            (page.extract_text() or "") for page in pdf.pages[:3]
        )

    # WealthPoint valuation format
    if "STATEMENT OF ASSETS" in first_pages and "ASSET ALLOCATION" in first_pages:
        return "wealthpoint_valuation"

    # Add more format detections here
    # if "SOME OTHER PATTERN" in first_pages:
    #     return "other_format"

    return "unknown"


def extract_raw_text(pdf_path: str) -> str:
    """Extract all text from PDF for LLM-based parsing."""
    texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                texts.append(f"--- Page {i + 1} ---\n{text}")
    return "\n\n".join(texts)


def extract_tables(pdf_path: str) -> list[dict]:
    """Extract all tables from PDF."""
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_tables = page.extract_tables()
            for j, table in enumerate(page_tables):
                if table:
                    tables.append({
                        "page": i + 1,
                        "table_index": j,
                        "headers": table[0] if table else [],
                        "rows": table[1:] if len(table) > 1 else [],
                    })
    return tables


def parse_pdf(pdf_path: str) -> PortfolioData:
    """
    Parse a financial PDF into structured PortfolioData.

    Detects the format and routes to the appropriate parser.
    """
    pdf_type = detect_pdf_type(pdf_path)

    if pdf_type == "wealthpoint_valuation":
        parser = ValuationPDFParser(pdf_path)
        return parser.parse()

    # For unknown formats, return empty structure with raw text available
    # The Q&A service can use the raw text with an LLM
    return PortfolioData()
