"""
Bank-specific PDF parser configurations.

Each bank has different PDF formats. This module defines detection rules
and parser strategies for each supported bank.
"""
from typing import Literal

BankName = Literal["wealthpoint", "ubs", "julius_baer", "credit_suisse", "generic"]
ParserStrategy = Literal["pdfplumber", "llm_vision", "hybrid"]


class BankConfig:
    """Configuration for a specific bank's PDF format."""

    def __init__(
        self,
        name: BankName,
        detect_keywords: list[str],
        parser: ParserStrategy,
        table_settings: dict | None = None,
        position_table_headers: list[str] | None = None,
        extra_prompt: str = "",
        confidence_threshold: float = 0.7,
    ):
        """
        Initialize bank configuration.

        Args:
            name: Bank identifier
            detect_keywords: Keywords to detect this bank's PDFs
            parser: Preferred parsing strategy
            table_settings: pdfplumber table extraction settings
            position_table_headers: Expected table headers for positions
            extra_prompt: Additional context for LLM extraction
            confidence_threshold: Minimum confidence to use pdfplumber alone
        """
        self.name = name
        self.detect_keywords = detect_keywords
        self.parser = parser
        self.table_settings = table_settings or {}
        self.position_table_headers = position_table_headers or []
        self.extra_prompt = extra_prompt
        self.confidence_threshold = confidence_threshold


# ────────────────────────────────────────────────────────────────────────────
# Bank Configurations
# ────────────────────────────────────────────────────────────────────────────

BANK_CONFIGS: dict[BankName, BankConfig] = {
    "wealthpoint": BankConfig(
        name="wealthpoint",
        detect_keywords=[
            "WealthPoint",
            "Rothschild",
            "Edmond de Rothschild",
            "VALORISATION DE VOTRE PORTEFEUILLE",
        ],
        parser="pdfplumber",  # Format known, pdfplumber works well
        table_settings={
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "intersection_tolerance": 3,
        },
        position_table_headers=[
            "Description",
            "ISIN",
            "Quantité",
            "Cours",
            "Devise",
            "Valeur CHF",
            "Poids",
        ],
        confidence_threshold=0.85,  # High confidence for known format
    ),

    "ubs": BankConfig(
        name="ubs",
        detect_keywords=[
            "UBS",
            "UBS Switzerland AG",
            "UBS Asset Management",
            "Portfolio Statement",
        ],
        parser="llm_vision",  # Complex format, multi-page positions
        extra_prompt=(
            "UBS statements often have positions split across multiple pages. "
            "Concatenate all position tables before extracting. "
            "The total value is usually on the first page header. "
            "Position details may continue on pages 2-3."
        ),
        confidence_threshold=0.6,  # Lower threshold, prefer LLM
    ),

    "julius_baer": BankConfig(
        name="julius_baer",
        detect_keywords=[
            "Julius Baer",
            "Julius Bär",
            "Bank Julius Baer",
            "Vermögensübersicht",
        ],
        parser="llm_vision",  # German headers, complex layout
        extra_prompt=(
            "Julius Baer uses German headers: "
            "'Bezeichnung' (name), 'Valor' (security number), 'Kurs' (price), "
            "'Bewertung' (valuation). "
            "The portfolio total is labeled 'Gesamtvermögen'."
        ),
        confidence_threshold=0.6,
    ),

    "credit_suisse": BankConfig(
        name="credit_suisse",
        detect_keywords=[
            "Credit Suisse",
            "CS",
            "Portfolio Overview",
            "Investment Proposal",
        ],
        parser="hybrid",  # Try pdfplumber first, fall back to LLM
        table_settings={
            "vertical_strategy": "text",
            "horizontal_strategy": "lines",
        },
        extra_prompt=(
            "Credit Suisse statements mix text and tables. "
            "Position data may be in borderless tables. "
            "Watch for multi-currency positions."
        ),
        confidence_threshold=0.7,
    ),

    "generic": BankConfig(
        name="generic",
        detect_keywords=[],  # Default fallback
        parser="llm_vision",  # Unknown format, use LLM
        extra_prompt=(
            "This is a generic financial statement. "
            "Extract all positions, allocation data, and portfolio totals. "
            "Infer the bank/institution from logos or headers if possible."
        ),
        confidence_threshold=0.5,  # Low threshold for unknown formats
    ),
}


def detect_bank(text: str) -> BankConfig:
    """
    Detect which bank issued the PDF based on text content.

    Args:
        text: Full text extracted from PDF

    Returns:
        BankConfig for the detected bank (or generic if unknown)
    """
    text_upper = text.upper()

    # Check each bank's keywords
    for bank_name, config in BANK_CONFIGS.items():
        if bank_name == "generic":
            continue  # Skip generic, use as fallback

        for keyword in config.detect_keywords:
            if keyword.upper() in text_upper:
                return config

    # No match found, return generic
    return BANK_CONFIGS["generic"]


def get_bank_config(bank_name: BankName) -> BankConfig:
    """
    Get configuration for a specific bank.

    Args:
        bank_name: Bank identifier

    Returns:
        BankConfig for the requested bank

    Raises:
        KeyError: If bank name is not recognized
    """
    return BANK_CONFIGS[bank_name]
