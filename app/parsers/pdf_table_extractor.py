"""
Dynamic PDF table extraction for portfolio positions.

This module provides helper functions to extract positions dynamically from
PDF tables using pdfplumber, replacing the hardcoded approach in valuation_pdf.py.
"""
from typing import Optional, Any
import re
import pdfplumber

from app.models.portfolio import (
    AssetClass,
    Position,
    PositionType,
)


def _parse_number(s: str | None) -> float:
    """Parse a number string with Swiss formatting (apostrophe as thousands sep)."""
    if not s or not str(s).strip():
        return 0.0
    s = str(s).strip().replace("'", "").replace("'", "").replace("\u2019", "")
    s = s.replace(",", ".") if "," in s and "." not in s else s
    s = s.rstrip("%")
    try:
        return float(s)
    except (ValueError, AttributeError):
        return 0.0


def _parse_pct(s: str | None) -> float:
    """Parse a percentage string."""
    if not s:
        return 0.0
    return _parse_number(str(s).replace("%", ""))


def find_header_row(table: list[list]) -> Optional[int]:
    """
    Find the row index containing column headers in a table.

    Args:
        table: Table data from pdfplumber

    Returns:
        Index of header row, or None if not found
    """
    for i, row in enumerate(table):
        if not row:
            continue

        # Convert row to lowercase string for matching
        row_text = " ".join(str(cell or "").lower() for cell in row)

        # Look for key headers that identify a positions table
        has_isin = "isin" in row_text or "valor" in row_text
        has_value = any(keyword in row_text for keyword in ["value", "worth", "valeur"])
        has_weight = any(keyword in row_text for keyword in ["weight", "%", "pct"])

        if has_isin and (has_value or has_weight):
            return i

    return None


def infer_asset_class(isin: str, name: str) -> AssetClass:
    """
    Infer asset class from ISIN and position name.

    Args:
        isin: ISIN code
        name: Position name

    Returns:
        AssetClass enum value
    """
    name_lower = name.lower()

    # Cash accounts
    if "cash account" in name_lower or "cash" in name_lower and "account" in name_lower:
        return AssetClass.CASH

    # Bonds - identified by coupon rate and maturity year in name
    # Pattern: "4.85% ... 2033" or "3.5% ... 2025"
    has_coupon = bool(re.search(r"\d+\.?\d*%", name))
    has_maturity = bool(re.search(r"20\d{2}", name))
    if has_coupon and has_maturity:
        return AssetClass.BONDS

    # Bond funds
    if "bond" in name_lower and ("fund" in name_lower or "sicav" in name_lower or "pictet" in name_lower):
        return AssetClass.BONDS

    # ETFs
    if any(keyword in name_lower for keyword in ["etf", "spdr", "ishares", "vanguard", "tracker"]):
        return AssetClass.EQUITIES

    # Equities (stocks) - company names with legal entity suffix
    equity_suffixes = ["ag", "inc", "corp", "ltd", "plc", "sa", "se", "holding", "holdings"]
    if any(f" {suffix}" in name_lower or name_lower.endswith(suffix) for suffix in equity_suffixes):
        # Exclude bonds (they can also have company names)
        if not has_coupon and "bond" not in name_lower:
            return AssetClass.EQUITIES

    # Structured products
    if any(keyword in name_lower for keyword in ["structured", "certificate", "warrant", "note"]):
        return AssetClass.STRUCTURED_PRODUCTS

    # Funds (mutual funds, hedge funds, PE funds)
    if any(keyword in name_lower for keyword in ["fund", "sicav", "ucits", "fcp", "private equity", "pe fund"]):
        return AssetClass.OTHERS

    # Commodities
    if any(keyword in name_lower for keyword in ["gold", "silver", "commodity", "metal"]):
        return AssetClass.OTHERS

    # Default to OTHERS for unclassified
    return AssetClass.OTHERS


def infer_position_type(asset_class: AssetClass, name: str, currency: str = "") -> PositionType:
    """
    Infer position type from asset class, name, and currency.

    Args:
        asset_class: Asset class enum
        name: Position name
        currency: Currency code (CHF, USD, EUR, etc.)

    Returns:
        PositionType enum value
    """
    name_lower = name.lower()

    if asset_class == AssetClass.CASH:
        return PositionType.CASH_ACCOUNT

    if asset_class == AssetClass.BONDS:
        # Check if it's a bond fund
        if "fund" in name_lower or "sicav" in name_lower:
            return PositionType.BOND_FUND

        # Check if it's a foreign currency bond (FX bond)
        if currency and currency != "CHF":
            return PositionType.BOND_FX

        return PositionType.BOND

    if asset_class == AssetClass.EQUITIES:
        # ETF
        if any(keyword in name_lower for keyword in ["etf", "spdr", "ishares", "vanguard", "tracker"]):
            return PositionType.ETF

        # Regular equity/stock
        return PositionType.EQUITY

    if asset_class == AssetClass.STRUCTURED_PRODUCTS:
        return PositionType.STRUCTURED_PRODUCT

    # OTHERS category
    if "fund" in name_lower or "sicav" in name_lower:
        return PositionType.FUND

    if any(keyword in name_lower for keyword in ["gold", "silver", "commodity", "metal"]):
        return PositionType.COMMODITY

    if any(keyword in name_lower for keyword in ["private equity", "pe fund", "venture"]):
        return PositionType.PRIVATE_EQUITY

    return PositionType.OTHER


def parse_position_row(headers: list, row: list, isin_ticker_map: dict) -> Optional[Position]:
    """
    Parse a single position row from a table.

    Args:
        headers: List of column headers (lowercased)
        row: List of cell values for this position
        isin_ticker_map: Dict mapping ISIN -> (ticker, is_listed)

    Returns:
        Position object, or None if row is invalid
    """
    try:
        # Create a dict mapping header -> value
        data = {}
        for i, header in enumerate(headers):
            if i < len(row):
                value = row[i]
                # Clean up header (lowercase, remove special chars)
                clean_header = str(header or "").lower().strip()
                data[clean_header] = value

        # Extract required fields
        # Try multiple possible header names for each field
        currency = (
            data.get("currency")
            or data.get("ccy")
            or data.get("curr")
            or ""
        )

        isin = (
            data.get("isin")
            or data.get("isin/valor")
            or ""
        )

        name = (
            data.get("name")
            or data.get("instrument")
            or data.get("security")
            or data.get("position")
            or ""
        )

        value_chf = _parse_number(
            data.get("value chf")
            or data.get("value (chf)")
            or data.get("market value chf")
            or data.get("val chf")
            or data.get("value")
        )

        weight_pct = _parse_pct(
            data.get("weight %")
            or data.get("weight")
            or data.get("wt %")
            or data.get("%")
            or data.get("pct")
        )

        # Skip row if missing critical fields
        if not all([currency, isin, name, value_chf]):
            return None

        # Convert to strings and clean
        currency = str(currency).strip()
        isin = str(isin).strip()
        name = str(name).strip()

        # Skip header rows that got through
        if "isin" in isin.lower() or "currency" in currency.lower():
            return None

        # Infer asset class and position type
        asset_class = infer_asset_class(isin, name)
        position_type = infer_position_type(asset_class, name, currency)

        # Check if listed (from ISIN_TICKER_MAP)
        ticker, is_listed = isin_ticker_map.get(isin, (None, False))

        # Extract optional fields
        quantity = _parse_number(
            data.get("quantity")
            or data.get("qty")
            or data.get("shares")
            or data.get("units")
        )

        cost_price = _parse_number(
            data.get("cost price")
            or data.get("cost")
            or data.get("avg price")
            or data.get("purchase price")
        )

        quote = _parse_number(
            data.get("quote")
            or data.get("price")
            or data.get("market price")
            or data.get("current price")
        )

        perf_ytd_pct = _parse_pct(
            data.get("perf ytd")
            or data.get("ytd perf")
            or data.get("ytd %")
            or data.get("performance ytd")
        )

        # Bond-specific fields
        maturity_date = str(data.get("maturity") or "").strip() or None
        coupon_rate = _parse_pct(data.get("coupon") or data.get("coupon rate"))
        ytm = _parse_pct(data.get("ytm") or data.get("yield") or data.get("yield to maturity"))
        modified_duration = _parse_number(data.get("duration") or data.get("modified duration"))

        # FX rate
        fx_rate = _parse_number(data.get("fx") or data.get("fx rate") or data.get("exchange rate"))
        if not fx_rate and currency == "CHF":
            fx_rate = 1.0

        # Determine sub-category based on position type and name
        sub_category = _infer_sub_category(asset_class, position_type, name, currency)

        return Position(
            asset_class=asset_class,
            sub_category=sub_category,
            position_type=position_type,
            currency=currency,
            isin=isin or None,
            name=name,
            quantity=quantity or None,
            cost_price=cost_price or None,
            quote=quote or None,
            value_chf=value_chf,
            weight_pct=weight_pct,
            ticker=ticker,
            is_listed=is_listed,
            perf_ytd_pct=perf_ytd_pct or None,
            fx_rate=fx_rate or None,
            # Bond-specific
            maturity_date=maturity_date,
            coupon_rate=coupon_rate or None,
            ytm=ytm or None,
            modified_duration=modified_duration or None,
        )

    except Exception as e:
        # Log error but don't crash
        print(f"Warning: Error parsing position row: {e}")
        print(f"  Row data: {row[:5]}...")  # Print first 5 cells for debugging
        return None


def _infer_sub_category(asset_class: AssetClass, position_type: PositionType, name: str, currency: str) -> str:
    """Infer sub-category for better classification."""
    name_lower = name.lower()

    if asset_class == AssetClass.CASH:
        return "Cash (accounts)"

    if asset_class == AssetClass.BONDS:
        if position_type == PositionType.BOND_FX:
            return "Bonds FX"
        if position_type == PositionType.BOND_FUND:
            return "Other Fixed Income"
        return "Bonds"

    if asset_class == AssetClass.EQUITIES:
        # Determine geographic region from name or currency
        if "switzerland" in name_lower or "swiss" in name_lower or currency == "CHF":
            return "Equity Switzerland"
        elif currency == "EUR" or any(country in name_lower for country in ["france", "germany", "europe", "eu"]):
            return "Equity Europe ex Switzerland"
        elif currency == "USD" or any(country in name_lower for country in ["america", "us ", "united states"]):
            return "Equity North America"
        elif any(region in name_lower for region in ["asia", "japan", "china", "emerging"]):
            return "Equity Asia/EM"
        return "Equity Other"

    if asset_class == AssetClass.STRUCTURED_PRODUCTS:
        return "Structured Products"

    if asset_class == AssetClass.OTHERS:
        if "gold" in name_lower or "commodity" in name_lower:
            return "Commodities"
        if "private equity" in name_lower:
            return "Private Equity"
        return "Other"

    return ""


def extract_positions_from_tables(pdf: pdfplumber.PDF, isin_ticker_map: dict) -> list[Position]:
    """
    Extract positions dynamically from PDF tables.

    Args:
        pdf: pdfplumber PDF object
        isin_ticker_map: Dict mapping ISIN -> (ticker, is_listed)

    Returns:
        List of Position objects
    """
    positions = []

    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text() or ""

        # Only process pages that look like POSITIONS pages
        if "POSITIONS" not in text.upper():
            continue

        # Extract tables from this page
        tables = page.extract_tables()

        if not tables:
            continue

        for table_num, table in enumerate(tables):
            if not table or len(table) < 2:
                continue

            # Find header row
            header_idx = find_header_row(table)
            if header_idx is None:
                continue

            headers = [str(h or "").lower().strip() for h in table[header_idx]]

            # Parse data rows
            for row_idx, row in enumerate(table[header_idx + 1:], start=header_idx + 1):
                if not row or not any(row):  # Skip empty rows
                    continue

                position = parse_position_row(headers, row, isin_ticker_map)
                if position:
                    positions.append(position)

    return positions
