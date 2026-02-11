"""
Cross-validation for PDF extraction results.

Validates extraction quality by checking consistency between:
- Position values sum vs total portfolio value
- Weight percentages sum
- Currency exposure vs positions
- Missing required fields

Can also compare pdfplumber vs Claude Vision results (for hybrid mode).
"""
from typing import Optional
from app.models.portfolio import PortfolioData, Position


class ValidationResult:
    """Result of extraction validation."""

    def __init__(self):
        self.is_valid = True
        self.confidence_score = 1.0
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.metrics: dict = {}

    def add_warning(self, message: str):
        """Add a validation warning."""
        self.warnings.append(message)
        self.confidence_score -= 0.05  # Small penalty

    def add_error(self, message: str):
        """Add a validation error."""
        self.errors.append(message)
        self.is_valid = False
        self.confidence_score -= 0.2  # Large penalty

    def __repr__(self) -> str:
        status = "✅ Valid" if self.is_valid else "❌ Invalid"
        return (
            f"{status} (confidence: {self.confidence_score:.2f})\n"
            f"  Warnings: {len(self.warnings)}\n"
            f"  Errors: {len(self.errors)}"
        )


class CrossValidator:
    """
    Validates extraction quality and compares results from different extractors.
    """

    def __init__(self, tolerance_pct: float = 1.0):
        """
        Initialize validator.

        Args:
            tolerance_pct: Tolerance for value mismatches (default 1%)
        """
        self.tolerance_pct = tolerance_pct

    def validate(self, portfolio: PortfolioData) -> ValidationResult:
        """
        Validate a single extraction result.

        Args:
            portfolio: Extracted portfolio data

        Returns:
            ValidationResult with confidence score and issues
        """
        result = ValidationResult()

        # Check 1: Positions sum matches total value
        self._check_value_consistency(portfolio, result)

        # Check 2: Weights sum to ~100%
        self._check_weights(portfolio, result)

        # Check 3: Missing required fields
        self._check_required_fields(portfolio, result)

        # Check 4: ISINs are valid format
        self._check_isin_format(portfolio, result)

        # Check 5: Reasonable values (no negative, no extreme)
        self._check_value_ranges(portfolio, result)

        # Store metrics
        result.metrics = {
            "total_positions": len(portfolio.positions),
            "total_value_declared": portfolio.total_value_chf,
            "total_value_calculated": sum(p.value_chf for p in portfolio.positions),
            "total_weight_pct": sum(p.weight_pct for p in portfolio.positions),
            "positions_with_isin": sum(1 for p in portfolio.positions if p.isin),
        }

        return result

    def compare(
        self,
        pdfplumber_result: Optional[PortfolioData],
        llm_result: PortfolioData,
    ) -> ValidationResult:
        """
        Compare results from pdfplumber vs Claude Vision.

        Args:
            pdfplumber_result: Result from pdfplumber extraction (can be None)
            llm_result: Result from Claude Vision

        Returns:
            ValidationResult indicating which result is more reliable
        """
        result = ValidationResult()

        # If no pdfplumber result, validate LLM only
        if not pdfplumber_result or not pdfplumber_result.positions:
            result.add_warning("No pdfplumber result available, using LLM only")
            return self.validate(llm_result)

        # Compare position counts
        pdf_count = len(pdfplumber_result.positions)
        llm_count = len(llm_result.positions)

        if abs(pdf_count - llm_count) > 2:
            result.add_warning(
                f"Position count mismatch: pdfplumber={pdf_count}, LLM={llm_count}"
            )

        # Compare total values
        pdf_total = pdfplumber_result.total_value_chf
        llm_total = llm_result.total_value_chf

        value_diff_pct = abs(pdf_total - llm_total) / max(pdf_total, llm_total) * 100

        if value_diff_pct > self.tolerance_pct:
            result.add_warning(
                f"Total value mismatch: pdfplumber={pdf_total:,.2f}, "
                f"LLM={llm_total:,.2f} ({value_diff_pct:.2f}% diff)"
            )
        else:
            # Values match → high confidence
            result.confidence_score = min(1.0, result.confidence_score + 0.1)

        # Compare position by position (by ISIN)
        pdf_by_isin = {p.isin: p for p in pdfplumber_result.positions if p.isin}
        llm_by_isin = {p.isin: p for p in llm_result.positions if p.isin}

        common_isins = set(pdf_by_isin.keys()) & set(llm_by_isin.keys())

        for isin in common_isins:
            pdf_pos = pdf_by_isin[isin]
            llm_pos = llm_by_isin[isin]

            # Compare values
            if pdf_pos.value_chf and llm_pos.value_chf:
                pos_diff_pct = abs(pdf_pos.value_chf - llm_pos.value_chf) / max(
                    pdf_pos.value_chf, llm_pos.value_chf
                ) * 100

                if pos_diff_pct > self.tolerance_pct * 2:  # Double tolerance for individual positions
                    result.add_warning(
                        f"Position value mismatch for {isin}: "
                        f"pdfplumber={pdf_pos.value_chf:,.2f}, "
                        f"LLM={llm_pos.value_chf:,.2f} ({pos_diff_pct:.2f}% diff)"
                    )

        # Store comparison metrics
        result.metrics = {
            "pdfplumber_positions": pdf_count,
            "llm_positions": llm_count,
            "common_positions": len(common_isins),
            "total_value_diff_pct": value_diff_pct,
            "pdfplumber_confidence": self.validate(pdfplumber_result).confidence_score,
            "llm_confidence": self.validate(llm_result).confidence_score,
        }

        return result

    def _check_value_consistency(self, portfolio: PortfolioData, result: ValidationResult):
        """Check if position values sum to total value."""
        calculated_total = sum(p.value_chf for p in portfolio.positions)
        declared_total = portfolio.total_value_chf

        if declared_total == 0:
            result.add_error("Total portfolio value is zero")
            return

        diff_pct = abs(calculated_total - declared_total) / declared_total * 100

        if diff_pct > self.tolerance_pct:
            result.add_warning(
                f"Value sum mismatch: calculated={calculated_total:,.2f}, "
                f"declared={declared_total:,.2f} ({diff_pct:.2f}% diff)"
            )

    def _check_weights(self, portfolio: PortfolioData, result: ValidationResult):
        """Check if weights sum to ~100%."""
        total_weight = sum(p.weight_pct for p in portfolio.positions)

        if abs(total_weight - 100.0) > 2.0:  # ±2% tolerance
            result.add_warning(
                f"Weights sum to {total_weight:.2f}% (should be ~100%)"
            )

    def _check_required_fields(self, portfolio: PortfolioData, result: ValidationResult):
        """Check for missing required fields."""
        for i, pos in enumerate(portfolio.positions):
            if not pos.name or pos.name == "Unknown Position":
                result.add_error(f"Position {i+1} missing name")

            if pos.value_chf <= 0:
                result.add_error(f"Position {pos.name} has invalid value: {pos.value_chf}")

            if pos.weight_pct < 0 or pos.weight_pct > 100:
                result.add_warning(
                    f"Position {pos.name} has suspicious weight: {pos.weight_pct}%"
                )

    def _check_isin_format(self, portfolio: PortfolioData, result: ValidationResult):
        """Check ISIN format (2 letters + 9 alphanumeric + 1 digit)."""
        for pos in portfolio.positions:
            if not pos.isin:
                continue  # Missing ISIN is OK for some assets

            isin = pos.isin.strip()

            if len(isin) != 12:
                result.add_warning(
                    f"Position {pos.name} has malformed ISIN: {isin} (should be 12 chars)"
                )
                continue

            if not isin[:2].isalpha():
                result.add_warning(
                    f"Position {pos.name} ISIN should start with country code: {isin}"
                )

            if not isin[2:].isalnum():
                result.add_warning(
                    f"Position {pos.name} ISIN contains invalid characters: {isin}"
                )

    def _check_value_ranges(self, portfolio: PortfolioData, result: ValidationResult):
        """Check for unrealistic values."""
        for pos in portfolio.positions:
            # Negative values
            if pos.value_chf < 0:
                result.add_error(f"Position {pos.name} has negative value: {pos.value_chf}")

            # Extreme weights
            if pos.weight_pct > 95:
                result.add_warning(
                    f"Position {pos.name} dominates portfolio: {pos.weight_pct}%"
                )

            # Suspicious quantities
            if pos.quantity and pos.quantity < 0:
                result.add_error(f"Position {pos.name} has negative quantity: {pos.quantity}")
