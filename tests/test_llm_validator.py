"""
Tests for LLM-based position validation.

These tests use mock LLM responses to validate the validator logic.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.parsers.llm_validator import PositionValidator, validate_positions_batch
from app.models.portfolio import Position, AssetClass, PositionType


# ────────────────────────────────────────────────────────────────────────────
# Mock LLM Provider
# ────────────────────────────────────────────────────────────────────────────


class MockLLM:
    """Mock LLM provider for testing."""

    def __init__(self, response: str):
        self.response = response

    async def complete(self, system: str, user: str, response_format=None) -> str:
        return self.response


# ────────────────────────────────────────────────────────────────────────────
# Test Position Validator
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_validate_position_with_corrections():
    """Test position validation with OCR corrections."""

    # Mock LLM response with corrections
    llm_response = """
    {
        "valid": false,
        "corrections": [
            {
                "field": "name",
                "old_value": "R0che H0lding AG",
                "new_value": "Roche Holding AG",
                "reason": "Corrected OCR error (0 → o)"
            }
        ],
        "warnings": [],
        "enhanced_fields": {
            "ticker": "ROG.SW"
        }
    }
    """

    llm = MockLLM(llm_response)
    validator = PositionValidator(llm)

    # Create position with OCR error
    position = Position(
        asset_class=AssetClass.EQUITIES,
        position_type=PositionType.EQUITY,
        currency="CHF",
        isin="CH0012032048",
        name="R0che H0lding AG",  # OCR error
        value_chf=312.90,
        weight_pct=10.47,
        ticker=None,  # Missing
        is_listed=True
    )

    # Validate
    result = await validator.validate_position(position)

    # Check result
    assert result["valid"] is False
    assert len(result["corrections"]) == 1
    assert result["corrections"][0]["field"] == "name"
    assert result["corrections"][0]["new_value"] == "Roche Holding AG"
    assert result["enhanced_fields"]["ticker"] == "ROG.SW"


@pytest.mark.asyncio
async def test_validate_position_valid():
    """Test validation of correct position."""

    llm_response = """
    {
        "valid": true,
        "corrections": [],
        "warnings": [],
        "enhanced_fields": {}
    }
    """

    llm = MockLLM(llm_response)
    validator = PositionValidator(llm)

    position = Position(
        asset_class=AssetClass.EQUITIES,
        position_type=PositionType.EQUITY,
        currency="CHF",
        isin="CH0012032048",
        name="Roche Holding AG",
        value_chf=312.90,
        weight_pct=10.47,
        ticker="ROG.SW",
        is_listed=True
    )

    result = await validator.validate_position(position)

    assert result["valid"] is True
    assert len(result["corrections"]) == 0
    assert len(result["warnings"]) == 0


@pytest.mark.asyncio
async def test_validate_position_with_warnings():
    """Test validation with warnings."""

    llm_response = """
    {
        "valid": true,
        "corrections": [],
        "warnings": [
            "Position weight (45%) seems too high for single equity"
        ],
        "enhanced_fields": {}
    }
    """

    llm = MockLLM(llm_response)
    validator = PositionValidator(llm)

    position = Position(
        asset_class=AssetClass.EQUITIES,
        position_type=PositionType.EQUITY,
        currency="CHF",
        isin="CH0012032048",
        name="Roche Holding AG",
        value_chf=1350.00,
        weight_pct=45.0,  # Very high concentration
        ticker="ROG.SW",
        is_listed=True
    )

    result = await validator.validate_position(position)

    assert result["valid"] is True
    assert len(result["warnings"]) == 1
    assert "45%" in result["warnings"][0]


# ────────────────────────────────────────────────────────────────────────────
# Test Apply Corrections
# ────────────────────────────────────────────────────────────────────────────


def test_apply_corrections():
    """Test applying corrections to a position."""

    validator = PositionValidator(MockLLM(""))

    position = Position(
        asset_class=AssetClass.EQUITIES,
        position_type=PositionType.EQUITY,
        currency="CHF",
        isin="CH0012032048",
        name="R0che H0lding AG",  # OCR error
        value_chf=312.90,
        weight_pct=10.47,
        ticker=None,
        is_listed=True
    )

    validation_result = {
        "valid": False,
        "corrections": [
            {
                "field": "name",
                "old_value": "R0che H0lding AG",
                "new_value": "Roche Holding AG",
                "reason": "OCR correction"
            }
        ],
        "warnings": [],
        "enhanced_fields": {
            "ticker": "ROG.SW"
        }
    }

    corrected = validator.apply_corrections(position, validation_result)

    assert corrected.name == "Roche Holding AG"
    assert corrected.ticker == "ROG.SW"


# ────────────────────────────────────────────────────────────────────────────
# Test Portfolio-Level Validation
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_validate_portfolio_consistent():
    """Test portfolio validation with consistent data."""

    llm = MockLLM("{}")
    validator = PositionValidator(llm)

    positions = [
        Position(
            asset_class=AssetClass.EQUITIES,
            position_type=PositionType.EQUITY,
            currency="CHF",
            isin="CH0012032048",
            name="Roche Holding AG",
            value_chf=500.0,
            weight_pct=50.0,
            ticker="ROG.SW",
            is_listed=True
        ),
        Position(
            asset_class=AssetClass.BONDS,
            position_type=PositionType.BOND,
            currency="CHF",
            isin="CH0123456789",
            name="Swiss Bond",
            value_chf=500.0,
            weight_pct=50.0,
            ticker=None,
            is_listed=False
        ),
    ]

    result = await validator.validate_portfolio(positions, 1000.0)

    assert result["valid"] is True
    assert result["total_value_calculated"] == 1000.0
    assert result["total_weight_pct"] == 100.0
    assert len(result["warnings"]) == 0


@pytest.mark.asyncio
async def test_validate_portfolio_inconsistent():
    """Test portfolio validation with inconsistent data."""

    llm = MockLLM("{}")
    validator = PositionValidator(llm)

    positions = [
        Position(
            asset_class=AssetClass.EQUITIES,
            position_type=PositionType.EQUITY,
            currency="CHF",
            isin="CH0012032048",
            name="Roche Holding AG",
            value_chf=500.0,
            weight_pct=45.0,  # Doesn't sum to 100%
            ticker="ROG.SW",
            is_listed=True
        ),
        Position(
            asset_class=AssetClass.BONDS,
            position_type=PositionType.BOND,
            currency="CHF",
            isin="CH0123456789",
            name="Swiss Bond",
            value_chf=400.0,  # Total = 900, not 1000
            weight_pct=40.0,
            ticker=None,
            is_listed=False
        ),
    ]

    result = await validator.validate_portfolio(positions, 1000.0)

    assert result["valid"] is False  # Should have warnings
    assert result["total_value_calculated"] == 900.0
    assert result["total_weight_pct"] == 85.0
    assert len(result["warnings"]) >= 2  # Value mismatch + weight sum


# ────────────────────────────────────────────────────────────────────────────
# Test Batch Validation
# ────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_validate_positions_batch():
    """Test batch validation of multiple positions."""

    # Mock LLM that returns valid for all
    llm_response = """
    {
        "valid": true,
        "corrections": [],
        "warnings": [],
        "enhanced_fields": {}
    }
    """

    llm = MockLLM(llm_response)

    positions = [
        Position(
            asset_class=AssetClass.EQUITIES,
            position_type=PositionType.EQUITY,
            currency="CHF",
            isin="CH0012032048",
            name="Roche Holding AG",
            value_chf=500.0,
            weight_pct=50.0,
            ticker="ROG.SW",
            is_listed=True
        ),
        Position(
            asset_class=AssetClass.BONDS,
            position_type=PositionType.BOND,
            currency="CHF",
            isin="CH0123456789",
            name="Swiss Bond",
            value_chf=500.0,
            weight_pct=50.0,
            ticker=None,
            is_listed=False
        ),
    ]

    validated, summary = await validate_positions_batch(
        positions,
        llm,
        1000.0,
        apply_corrections=True,
        verbose=False
    )

    assert len(validated) == 2
    assert summary["total_positions"] == 2
    assert summary["portfolio_valid"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
