"""
LLM-based validation and correction for PDF extraction.

This module uses an LLM to validate and enhance the positions extracted
by pdfplumber, improving accuracy and handling edge cases.
"""
import json
from typing import Optional
from app.llm import LLMProvider
from app.models.portfolio import Position, AssetClass, PositionType


# ────────────────────────────────────────────────────────────────────────────
# LLM Validation System Prompt
# ────────────────────────────────────────────────────────────────────────────

VALIDATION_SYSTEM_PROMPT = """You are a financial data validation expert specialized in portfolio statements.

Your role is to validate and correct position data extracted from PDF portfolio statements.

**Validation Tasks:**

1. **Verify data consistency**
   - Check that value_chf = quantity × quote × fx_rate (approximately)
   - Ensure weight_pct adds up to ~100% across all positions
   - Validate that currency codes are valid (CHF, USD, EUR, etc.)

2. **Correct OCR errors**
   - Fix common OCR mistakes in position names (e.g., "R0che" → "Roche")
   - Correct malformed ISINs (should be 12 characters: 2 letters + 9 alphanumeric + 1 digit)
   - Fix number formatting errors

3. **Enhance classification**
   - Verify asset_class is correct based on position name and characteristics
   - Correct position_type if obviously wrong
   - Suggest better sub_category classification

4. **Infer missing data**
   - If ticker is missing but ISIN is known, try to infer ticker
   - If maturity_date is missing for bonds, try to extract from name
   - If coupon_rate is in name but not parsed, extract it

5. **Flag suspicious data**
   - Extremely high/low values that might be errors
   - Inconsistent currency exposure
   - Missing required fields

**Output Format:**

Return a JSON object with:
{
  "valid": true/false,
  "corrections": [
    {
      "field": "name",
      "old_value": "R0che H0lding AG",
      "new_value": "Roche Holding AG",
      "reason": "Corrected OCR error (0 → o)"
    },
    ...
  ],
  "warnings": [
    "Position weight (45%) seems too high for single equity",
    ...
  ],
  "enhanced_fields": {
    "ticker": "ROG.SW",  // If inferred
    "maturity_date": "14/03/2033",  // If extracted from name
    ...
  }
}

**Important:** Only suggest corrections you are confident about. When in doubt, flag as warning.
"""


# ────────────────────────────────────────────────────────────────────────────
# Position Validator
# ────────────────────────────────────────────────────────────────────────────


class PositionValidator:
    """Validates and enhances position data using LLM."""

    def __init__(self, llm: LLMProvider):
        """
        Initialize validator.

        Args:
            llm: LLM provider (Claude or Ollama)
        """
        self.llm = llm

    async def validate_position(self, position: Position) -> dict:
        """
        Validate a single position using LLM.

        Args:
            position: Position to validate

        Returns:
            dict with validation results:
            {
                "valid": bool,
                "corrections": list[dict],
                "warnings": list[str],
                "enhanced_fields": dict
            }
        """
        # Build validation prompt
        position_data = {
            "name": position.name,
            "isin": position.isin,
            "currency": position.currency,
            "asset_class": position.asset_class.value if position.asset_class else None,
            "position_type": position.position_type.value if position.position_type else None,
            "quantity": position.quantity,
            "cost_price": position.cost_price,
            "quote": position.quote,
            "value_chf": position.value_chf,
            "weight_pct": position.weight_pct,
            "ticker": position.ticker,
            "fx_rate": position.fx_rate,
            # Bond-specific
            "maturity_date": position.maturity_date,
            "coupon_rate": position.coupon_rate,
            "ytm": position.ytm,
        }

        user_prompt = f"""Validate this position data extracted from a PDF:

```json
{json.dumps(position_data, indent=2)}
```

Check for:
1. OCR errors in name/ISIN
2. Correct asset class and position type
3. Consistency (value = quantity × quote × fx_rate)
4. Missing fields that could be inferred
5. Any suspicious values

Return validation results in JSON format as specified in your instructions.
"""

        try:
            response_text = await self.llm.complete(
                system=VALIDATION_SYSTEM_PROMPT,
                user=user_prompt,
                response_format="json"
            )

            # Parse JSON response
            result = json.loads(response_text)

            return result

        except json.JSONDecodeError:
            # LLM didn't return valid JSON - return minimal result
            return {
                "valid": True,  # Assume valid if we can't validate
                "corrections": [],
                "warnings": ["LLM validation failed - could not parse response"],
                "enhanced_fields": {}
            }

        except Exception as e:
            return {
                "valid": True,
                "corrections": [],
                "warnings": [f"LLM validation error: {str(e)}"],
                "enhanced_fields": {}
            }

    async def validate_portfolio(
        self,
        positions: list[Position],
        total_value_chf: float
    ) -> dict:
        """
        Validate entire portfolio for consistency.

        Args:
            positions: List of all positions
            total_value_chf: Expected total portfolio value

        Returns:
            dict with portfolio-level validation:
            {
                "valid": bool,
                "total_weight_pct": float,
                "total_value_calculated": float,
                "warnings": list[str]
            }
        """
        # Calculate totals
        total_value_calculated = sum(p.value_chf for p in positions)
        total_weight_pct = sum(p.weight_pct for p in positions)

        warnings = []

        # Check total value matches
        value_diff = abs(total_value_calculated - total_value_chf)
        value_diff_pct = (value_diff / total_value_chf) * 100 if total_value_chf else 0

        if value_diff_pct > 1.0:  # More than 1% difference
            warnings.append(
                f"Total value mismatch: calculated {total_value_calculated:,.2f} "
                f"vs reported {total_value_chf:,.2f} ({value_diff_pct:.2f}% diff)"
            )

        # Check weights sum to ~100%
        if abs(total_weight_pct - 100.0) > 2.0:  # More than 2% off
            warnings.append(
                f"Position weights sum to {total_weight_pct:.2f}% (should be ~100%)"
            )

        # Check for missing ISINs
        missing_isin_count = sum(
            1 for p in positions
            if not p.isin and p.asset_class != AssetClass.CASH
        )
        if missing_isin_count > 0:
            warnings.append(
                f"{missing_isin_count} positions missing ISIN codes"
            )

        # Check for suspicious weights
        for p in positions:
            if p.weight_pct > 30.0 and p.position_type != PositionType.FUND:
                warnings.append(
                    f"High concentration: {p.name} ({p.weight_pct:.1f}%)"
                )

        return {
            "valid": len(warnings) == 0,
            "total_weight_pct": total_weight_pct,
            "total_value_calculated": total_value_calculated,
            "warnings": warnings
        }

    def apply_corrections(
        self,
        position: Position,
        validation_result: dict
    ) -> Position:
        """
        Apply LLM corrections to a position.

        Args:
            position: Original position
            validation_result: Validation result from validate_position()

        Returns:
            Corrected position
        """
        corrections = validation_result.get("corrections", [])
        enhanced_fields = validation_result.get("enhanced_fields", {})

        # Apply corrections
        for correction in corrections:
            field = correction["field"]
            new_value = correction["new_value"]

            if hasattr(position, field):
                setattr(position, field, new_value)

        # Apply enhanced fields
        for field, value in enhanced_fields.items():
            if hasattr(position, field) and not getattr(position, field):
                # Only apply if field is currently empty
                setattr(position, field, value)

        return position


# ────────────────────────────────────────────────────────────────────────────
# Batch Validation (with progress tracking)
# ────────────────────────────────────────────────────────────────────────────


async def validate_positions_batch(
    positions: list[Position],
    llm: LLMProvider,
    total_value_chf: float,
    apply_corrections: bool = True,
    verbose: bool = False
) -> tuple[list[Position], dict]:
    """
    Validate all positions in a portfolio using LLM.

    Args:
        positions: List of positions to validate
        llm: LLM provider
        total_value_chf: Expected total portfolio value
        apply_corrections: Whether to apply LLM corrections
        verbose: Print validation progress

    Returns:
        Tuple of (validated_positions, summary)
        - validated_positions: Corrected positions (if apply_corrections=True)
        - summary: Validation summary with all warnings and corrections
    """
    validator = PositionValidator(llm)

    validated_positions = []
    all_corrections = []
    all_warnings = []

    # Validate each position
    for i, position in enumerate(positions):
        if verbose:
            print(f"Validating {i+1}/{len(positions)}: {position.name[:50]}...")

        validation_result = await validator.validate_position(position)

        # Collect corrections and warnings
        corrections = validation_result.get("corrections", [])
        warnings = validation_result.get("warnings", [])

        if corrections:
            all_corrections.extend([
                {**c, "position": position.name}
                for c in corrections
            ])

        if warnings:
            all_warnings.extend([
                f"{position.name}: {w}"
                for w in warnings
            ])

        # Apply corrections if requested
        if apply_corrections:
            corrected_position = validator.apply_corrections(position, validation_result)
            validated_positions.append(corrected_position)
        else:
            validated_positions.append(position)

    # Portfolio-level validation
    portfolio_validation = await validator.validate_portfolio(
        validated_positions,
        total_value_chf
    )

    all_warnings.extend(portfolio_validation["warnings"])

    # Build summary
    summary = {
        "total_positions": len(positions),
        "corrections_applied": len(all_corrections),
        "warnings": all_warnings,
        "corrections": all_corrections,
        "portfolio_valid": portfolio_validation["valid"],
        "total_value_calculated": portfolio_validation["total_value_calculated"],
        "total_weight_pct": portfolio_validation["total_weight_pct"],
    }

    if verbose:
        print(f"\n✅ Validation complete:")
        print(f"   - {len(all_corrections)} corrections applied")
        print(f"   - {len(all_warnings)} warnings")

    return validated_positions, summary
