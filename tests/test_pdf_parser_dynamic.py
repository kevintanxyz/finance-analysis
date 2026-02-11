"""
Test dynamic PDF parser with table extraction.

This test validates that the refactored parser can extract positions
dynamically from tables without hardcoded data.
"""
import pytest
from app.parsers.pdf_table_extractor import (
    find_header_row,
    infer_asset_class,
    infer_position_type,
    parse_position_row,
    _parse_number,
    _parse_pct,
)
from app.models.portfolio import AssetClass, PositionType


# ────────────────────────────────────────────────────────────────────────────
# Test Helper Functions
# ────────────────────────────────────────────────────────────────────────────


def test_parse_number():
    """Test Swiss number parsing."""
    assert _parse_number("2'988.44") == 2988.44
    assert _parse_number("1,234.56") == 1234.56
    assert _parse_number("100") == 100.0
    assert _parse_number("") == 0.0
    assert _parse_number(None) == 0.0
    assert _parse_number("invalid") == 0.0


def test_parse_pct():
    """Test percentage parsing."""
    assert _parse_pct("3.37%") == 3.37
    assert _parse_pct("10.5") == 10.5
    assert _parse_pct("-2.5%") == -2.5
    assert _parse_pct("") == 0.0


# ────────────────────────────────────────────────────────────────────────────
# Test Table Header Detection
# ────────────────────────────────────────────────────────────────────────────


def test_find_header_row():
    """Test header row detection in tables."""
    # Table with headers in first row
    table1 = [
        ["Currency", "ISIN", "Name", "Value CHF", "Weight %"],
        ["CHF", "CH0012032048", "Roche Holding AG", "312.90", "10.47%"],
    ]
    assert find_header_row(table1) == 0

    # Table with headers in second row
    table2 = [
        ["POSITIONS", "", "", "", ""],
        ["Currency", "ISIN", "Name", "Value CHF", "Weight %"],
        ["CHF", "CH0012032048", "Roche Holding AG", "312.90", "10.47%"],
    ]
    assert find_header_row(table2) == 1

    # Table without recognizable headers
    table3 = [
        ["Random", "Data", "Here"],
        ["More", "Random", "Data"],
    ]
    assert find_header_row(table3) is None


# ────────────────────────────────────────────────────────────────────────────
# Test Asset Class Inference
# ────────────────────────────────────────────────────────────────────────────


def test_infer_asset_class_bonds():
    """Test bond detection."""
    # Bond with coupon and maturity
    assert infer_asset_class(
        "USU64106CB80",
        "4.85% Nestle Holdings Inc 2033/03/14"
    ) == AssetClass.BONDS

    # US Treasury
    assert infer_asset_class(
        "US912810UD80",
        "4.125% United States of America 2044/08/15"
    ) == AssetClass.BONDS

    # Bond fund
    assert infer_asset_class(
        "LU0135487147",
        "Pictet SICAV - Pictet-CHF Bonds Fund"
    ) == AssetClass.BONDS


def test_infer_asset_class_equities():
    """Test equity detection."""
    # Swiss equity
    assert infer_asset_class(
        "CH0012032048",
        "Roche Holding AG"
    ) == AssetClass.EQUITIES

    # US equity
    assert infer_asset_class(
        "US0378331005",
        "Apple Inc"
    ) == AssetClass.EQUITIES

    # European equity
    assert infer_asset_class(
        "FR0000120271",
        "TotalEnergies SE"
    ) == AssetClass.EQUITIES

    # ETF
    assert infer_asset_class(
        "US78462F1030",
        "SPDR S&P 500 ETF Trust"
    ) == AssetClass.EQUITIES


def test_infer_asset_class_structured_products():
    """Test structured product detection."""
    assert infer_asset_class(
        "LU2771658486",
        "USS Luxembourg Fund Series SICAV-RAIF - DNA 9 Structured Note"
    ) == AssetClass.STRUCTURED_PRODUCTS


def test_infer_asset_class_others():
    """Test other asset class detection."""
    # Commodity
    assert infer_asset_class(
        "CH0104851461",
        "Pictet CH Precious Metals Fund - Physical Gold"
    ) == AssetClass.OTHERS

    # Hedge fund
    assert infer_asset_class(
        "VGG7238P1062",
        "Prima Capital Fund Ltd"
    ) == AssetClass.OTHERS


def test_infer_asset_class_cash():
    """Test cash account detection."""
    assert infer_asset_class(
        "",
        "Cash Account CHF"
    ) == AssetClass.CASH


# ────────────────────────────────────────────────────────────────────────────
# Test Position Type Inference
# ────────────────────────────────────────────────────────────────────────────


def test_infer_position_type():
    """Test position type inference."""
    # Cash
    assert infer_position_type(
        AssetClass.CASH, "Cash Account CHF", "CHF"
    ) == PositionType.CASH_ACCOUNT

    # Bond FX
    assert infer_position_type(
        AssetClass.BONDS, "4.85% Nestle Holdings Inc 2033", "USD"
    ) == PositionType.BOND_FX

    # Bond CHF
    assert infer_position_type(
        AssetClass.BONDS, "3.5% Swiss Confederation 2028", "CHF"
    ) == PositionType.BOND

    # Bond fund
    assert infer_position_type(
        AssetClass.BONDS, "Pictet CHF Bonds Fund", "CHF"
    ) == PositionType.BOND_FUND

    # Equity
    assert infer_position_type(
        AssetClass.EQUITIES, "Roche Holding AG", "CHF"
    ) == PositionType.EQUITY

    # ETF
    assert infer_position_type(
        AssetClass.EQUITIES, "SPDR S&P 500 ETF Trust", "USD"
    ) == PositionType.ETF

    # Structured product
    assert infer_position_type(
        AssetClass.STRUCTURED_PRODUCTS, "DNA 9 Certificate", "CHF"
    ) == PositionType.STRUCTURED_PRODUCT

    # Fund
    assert infer_position_type(
        AssetClass.OTHERS, "Prima Capital Fund", "USD"
    ) == PositionType.FUND

    # Commodity
    assert infer_position_type(
        AssetClass.OTHERS, "Physical Gold Fund", "USD"
    ) == PositionType.COMMODITY


# ────────────────────────────────────────────────────────────────────────────
# Test Position Row Parsing
# ────────────────────────────────────────────────────────────────────────────


def test_parse_position_row():
    """Test parsing a full position row."""
    headers = ["currency", "isin", "name", "value chf", "weight %"]
    row = ["CHF", "CH0012032048", "Roche Holding AG", "312.90", "10.47%"]

    isin_ticker_map = {
        "CH0012032048": ("ROG.SW", True),
    }

    position = parse_position_row(headers, row, isin_ticker_map)

    assert position is not None
    assert position.currency == "CHF"
    assert position.isin == "CH0012032048"
    assert position.name == "Roche Holding AG"
    assert position.value_chf == 312.90
    assert position.weight_pct == 10.47
    assert position.ticker == "ROG.SW"
    assert position.is_listed is True
    assert position.asset_class == AssetClass.EQUITIES
    assert position.position_type == PositionType.EQUITY


def test_parse_position_row_with_bond():
    """Test parsing a bond position."""
    headers = ["currency", "isin", "name", "value chf", "weight %", "maturity", "coupon", "ytm"]
    row = ["USD", "USU64106CB80", "4.85% Nestle Holdings Inc 2033/03/14", "0.84", "0.03%", "14/03/2033", "4.85%", "4.32%"]

    isin_ticker_map = {
        "USU64106CB80": (None, False),
    }

    position = parse_position_row(headers, row, isin_ticker_map)

    assert position is not None
    assert position.currency == "USD"
    assert position.isin == "USU64106CB80"
    assert position.asset_class == AssetClass.BONDS
    assert position.position_type == PositionType.BOND_FX
    assert position.maturity_date == "14/03/2033"
    assert position.coupon_rate == 4.85
    assert position.ytm == 4.32


def test_parse_position_row_skip_invalid():
    """Test that invalid rows are skipped."""
    headers = ["currency", "isin", "name", "value chf", "weight %"]

    # Row with missing required fields
    row1 = ["", "", "", "", ""]
    assert parse_position_row(headers, row1, {}) is None

    # Row that is actually a header
    row2 = ["Currency", "ISIN", "Name", "Value CHF", "Weight %"]
    assert parse_position_row(headers, row2, {}) is None


# ────────────────────────────────────────────────────────────────────────────
# Integration Test (would need actual PDF)
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.skip(reason="Requires actual PDF file")
def test_extract_positions_from_pdf():
    """
    Integration test with actual PDF.

    To run this test:
    1. Place a sample valuation PDF in tests/fixtures/sample_valuation.pdf
    2. Remove the @pytest.mark.skip decorator
    3. Run: pytest tests/test_pdf_parser_dynamic.py::test_extract_positions_from_pdf
    """
    import pdfplumber
    from app.parsers.pdf_table_extractor import extract_positions_from_tables
    from app.parsers.valuation_pdf import ISIN_TICKER_MAP

    pdf_path = "tests/fixtures/sample_valuation.pdf"

    with pdfplumber.open(pdf_path) as pdf:
        positions = extract_positions_from_tables(pdf, ISIN_TICKER_MAP)

        # Basic validation
        assert len(positions) > 0, "No positions extracted"

        # Check that all positions have required fields
        for position in positions:
            assert position.currency, f"Missing currency: {position.name}"
            assert position.isin or position.asset_class == AssetClass.CASH, f"Missing ISIN: {position.name}"
            assert position.name, "Missing position name"
            assert position.value_chf > 0, f"Invalid value: {position.name}"
            assert position.asset_class, f"Missing asset class: {position.name}"

        print(f"\n✅ Successfully extracted {len(positions)} positions")
        for p in positions[:5]:  # Print first 5
            print(f"  - {p.name}: {p.value_chf} CHF ({p.weight_pct}%)")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
