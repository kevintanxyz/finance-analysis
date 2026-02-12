"""
Portfolio Compliance Checker for WealthPoint

Validates portfolio against compliance rules:
- Position concentration limits
- Asset class diversification requirements
- Currency exposure limits
- Cash allocation bounds
- Minimum diversification (position count)

Adapted from Finance Guru™ Compliance Officer agent.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from app.models.analysis import (
    ComplianceCheckOutput,
    ComplianceConfig,
    ComplianceViolation,
)

if TYPE_CHECKING:
    from app.models.portfolio import PortfolioData


class ComplianceChecker:
    """
    Portfolio compliance validator.

    Checks portfolio against configurable limits and generates
    a detailed compliance report with violations and recommendations.
    """

    def check_compliance(
        self,
        portfolio: "PortfolioData",
        config: ComplianceConfig | None = None
    ) -> ComplianceCheckOutput:
        """
        Run comprehensive compliance check on portfolio.

        Args:
            portfolio: PortfolioData object with positions and allocations
            config: ComplianceConfig with limits (uses defaults if None)

        Returns:
            ComplianceCheckOutput with violations and recommendations

        Example:
            >>> checker = ComplianceChecker()
            >>> result = checker.check_compliance(portfolio)
            >>> if not result.is_compliant:
            ...     print(f"Found {result.critical_count} critical violations")
            ...     for violation in result.violations:
            ...         print(f"  - {violation.message}")
        """
        config = config or ComplianceConfig()
        violations: list[ComplianceViolation] = []

        # Check 1: Position concentration
        position_violations = self._check_position_concentration(
            portfolio, config.max_single_position_pct
        )
        violations.extend(position_violations)

        # Check 2: Asset class concentration
        asset_class_violations = self._check_asset_class_concentration(
            portfolio, config.max_asset_class_pct
        )
        violations.extend(asset_class_violations)

        # Check 3: Currency concentration
        currency_violations = self._check_currency_concentration(
            portfolio, config.max_currency_pct
        )
        violations.extend(currency_violations)

        # Check 4: Minimum diversification (position count)
        diversification_violations = self._check_minimum_diversification(
            portfolio, config.min_positions_count
        )
        violations.extend(diversification_violations)

        # Check 5: Cash allocation bounds
        cash_violations = self._check_cash_allocation(
            portfolio, config.min_cash_pct, config.max_cash_pct
        )
        violations.extend(cash_violations)

        # Generate summary and recommendations
        summary = self._generate_summary(violations, portfolio)
        recommendations = self._generate_recommendations(violations)

        return ComplianceCheckOutput(
            timestamp=datetime.now().isoformat(),
            portfolio_value_chf=portfolio.total_value_chf,
            total_positions=len(portfolio.positions),
            is_compliant=True,  # Will be set to False by validator if violations exist
            violations=violations,
            summary=summary,
            recommendations=recommendations,
        )

    def _check_position_concentration(
        self,
        portfolio: "PortfolioData",
        max_pct: float
    ) -> list[ComplianceViolation]:
        """Check if any single position exceeds concentration limit."""
        violations = []

        # Exclude cash from concentration check (it's checked separately)
        non_cash_positions = [
            pos for pos in portfolio.positions
            if pos.asset_class != "Cash"
        ]

        for position in non_cash_positions:
            if position.weight_pct > max_pct:
                severity = "critical" if position.weight_pct > max_pct * 1.5 else "high"

                violations.append(ComplianceViolation(
                    severity=severity,
                    rule_id="POS-01",
                    rule_name="Single Position Concentration Limit",
                    message=(
                        f"Position '{position.name}' represents {position.weight_pct:.1f}% "
                        f"of portfolio, exceeding limit of {max_pct:.1f}%"
                    ),
                    current_value=position.weight_pct,
                    limit_value=max_pct,
                    affected_positions=[position.name],
                    recommendation=(
                        f"Reduce exposure to '{position.name}' by "
                        f"CHF {portfolio.total_value_chf * (position.weight_pct - max_pct) / 100:.0f} "
                        f"({(position.weight_pct - max_pct):.1f}% of portfolio)"
                    )
                ))

        return violations

    def _check_asset_class_concentration(
        self,
        portfolio: "PortfolioData",
        max_pct: float
    ) -> list[ComplianceViolation]:
        """Check if any asset class exceeds concentration limit."""
        violations = []

        for allocation in portfolio.asset_allocation:
            # Skip cash - it has its own rule
            if allocation.asset_class == "Cash":
                continue

            if allocation.weight_pct > max_pct:
                severity = "high" if allocation.weight_pct > max_pct * 1.2 else "medium"

                # Find positions in this asset class
                affected = [
                    pos.name for pos in portfolio.positions
                    if pos.asset_class == allocation.asset_class
                ]

                violations.append(ComplianceViolation(
                    severity=severity,
                    rule_id="ASSET-01",
                    rule_name="Asset Class Concentration Limit",
                    message=(
                        f"Asset class '{allocation.asset_class}' represents {allocation.weight_pct:.1f}% "
                        f"of portfolio, exceeding limit of {max_pct:.1f}%"
                    ),
                    current_value=allocation.weight_pct,
                    limit_value=max_pct,
                    affected_positions=affected,
                    recommendation=(
                        f"Rebalance to reduce '{allocation.asset_class}' exposure by "
                        f"{(allocation.weight_pct - max_pct):.1f}% "
                        f"(approximately CHF {portfolio.total_value_chf * (allocation.weight_pct - max_pct) / 100:.0f})"
                    )
                ))

        return violations

    def _check_currency_concentration(
        self,
        portfolio: "PortfolioData",
        max_pct: float
    ) -> list[ComplianceViolation]:
        """Check if any currency exceeds concentration limit."""
        violations = []

        for exposure in portfolio.currency_exposure:
            if exposure.weight_pct > max_pct:
                severity = "medium" if exposure.weight_pct > max_pct * 1.1 else "low"

                # Find positions in this currency
                affected = [
                    pos.name for pos in portfolio.positions
                    if pos.currency == exposure.name
                ]

                violations.append(ComplianceViolation(
                    severity=severity,
                    rule_id="CCY-01",
                    rule_name="Currency Concentration Limit",
                    message=(
                        f"Currency '{exposure.name}' represents {exposure.weight_pct:.1f}% "
                        f"of portfolio, exceeding limit of {max_pct:.1f}%"
                    ),
                    current_value=exposure.weight_pct,
                    limit_value=max_pct,
                    affected_positions=affected[:5],  # Limit to 5 positions in output
                    recommendation=(
                        f"Consider hedging {exposure.name} exposure or diversifying into other currencies. "
                        f"Target reduction: {(exposure.weight_pct - max_pct):.1f}%"
                    )
                ))

        return violations

    def _check_minimum_diversification(
        self,
        portfolio: "PortfolioData",
        min_count: int
    ) -> list[ComplianceViolation]:
        """Check if portfolio has minimum number of positions."""
        violations = []

        # Count non-cash positions
        non_cash_count = sum(
            1 for pos in portfolio.positions
            if pos.asset_class != "Cash"
        )

        if non_cash_count < min_count:
            violations.append(ComplianceViolation(
                severity="high",
                rule_id="DIV-01",
                rule_name="Minimum Diversification Requirement",
                message=(
                    f"Portfolio has only {non_cash_count} positions, "
                    f"below minimum of {min_count} for adequate diversification"
                ),
                current_value=float(non_cash_count),
                limit_value=float(min_count),
                affected_positions=[],
                recommendation=(
                    f"Add at least {min_count - non_cash_count} more positions "
                    f"to achieve minimum diversification. Consider ETFs or funds "
                    f"for broad market exposure."
                )
            ))

        return violations

    def _check_cash_allocation(
        self,
        portfolio: "PortfolioData",
        min_pct: float,
        max_pct: float
    ) -> list[ComplianceViolation]:
        """Check if cash allocation is within bounds."""
        violations = []

        # Find cash allocation
        cash_allocation = next(
            (a for a in portfolio.asset_allocation if a.asset_class == "Cash"),
            None
        )

        if not cash_allocation:
            # No cash position found
            if min_pct > 0:
                violations.append(ComplianceViolation(
                    severity="medium",
                    rule_id="CASH-01",
                    rule_name="Minimum Cash Allocation",
                    message=(
                        f"No cash allocation found. Minimum required: {min_pct:.1f}%"
                    ),
                    current_value=0.0,
                    limit_value=min_pct,
                    affected_positions=[],
                    recommendation=(
                        f"Allocate at least {min_pct:.1f}% to cash or cash equivalents "
                        f"(approximately CHF {portfolio.total_value_chf * min_pct / 100:.0f})"
                    )
                ))
            return violations

        cash_pct = cash_allocation.weight_pct

        # Check minimum
        if cash_pct < min_pct:
            violations.append(ComplianceViolation(
                severity="medium",
                rule_id="CASH-01",
                rule_name="Minimum Cash Allocation",
                message=(
                    f"Cash allocation of {cash_pct:.1f}% is below minimum of {min_pct:.1f}%"
                ),
                current_value=cash_pct,
                limit_value=min_pct,
                affected_positions=["Cash Account"],
                recommendation=(
                    f"Increase cash reserves by {(min_pct - cash_pct):.1f}% "
                    f"(approximately CHF {portfolio.total_value_chf * (min_pct - cash_pct) / 100:.0f})"
                )
            ))

        # Check maximum
        if cash_pct > max_pct:
            violations.append(ComplianceViolation(
                severity="low",
                rule_id="CASH-02",
                rule_name="Maximum Cash Allocation",
                message=(
                    f"Cash allocation of {cash_pct:.1f}% exceeds maximum of {max_pct:.1f}%. "
                    f"Consider deploying excess cash to investments."
                ),
                current_value=cash_pct,
                limit_value=max_pct,
                affected_positions=["Cash Account"],
                recommendation=(
                    f"Deploy {(cash_pct - max_pct):.1f}% of portfolio "
                    f"(approximately CHF {portfolio.total_value_chf * (cash_pct - max_pct) / 100:.0f}) "
                    f"into investment positions to improve returns"
                )
            ))

        return violations

    def _generate_summary(
        self,
        violations: list[ComplianceViolation],
        portfolio: "PortfolioData"
    ) -> str:
        """Generate human-readable summary of compliance status."""
        if not violations:
            return (
                f"✅ Portfolio is COMPLIANT with all rules. "
                f"{len(portfolio.positions)} positions totaling "
                f"CHF {portfolio.total_value_chf:,.2f} meet all regulatory "
                f"and policy requirements."
            )

        critical = sum(1 for v in violations if v.severity == "critical")
        high = sum(1 for v in violations if v.severity == "high")
        medium = sum(1 for v in violations if v.severity == "medium")
        low = sum(1 for v in violations if v.severity == "low")

        severity_summary = []
        if critical > 0:
            severity_summary.append(f"{critical} CRITICAL")
        if high > 0:
            severity_summary.append(f"{high} HIGH")
        if medium > 0:
            severity_summary.append(f"{medium} MEDIUM")
        if low > 0:
            severity_summary.append(f"{low} LOW")

        severity_str = ", ".join(severity_summary)

        status = "NON-COMPLIANT" if (critical > 0 or high > 0) else "COMPLIANT with warnings"

        return (
            f"⚠️ Portfolio is {status}. "
            f"Found {len(violations)} violation(s): {severity_str}. "
            f"Immediate action required for critical and high-severity issues."
        )

    def _generate_recommendations(
        self,
        violations: list[ComplianceViolation]
    ) -> list[str]:
        """Generate top 3-5 priority recommendations."""
        if not violations:
            return [
                "Portfolio meets all compliance requirements.",
                "Continue monitoring concentration levels regularly.",
                "Review compliance rules quarterly to ensure alignment with risk tolerance."
            ]

        # Prioritize critical and high violations
        priority_violations = sorted(
            violations,
            key=lambda v: {"critical": 0, "high": 1, "medium": 2, "low": 3}[v.severity]
        )

        recommendations = [v.recommendation for v in priority_violations[:5]]

        # Add general advice
        if len(violations) > 5:
            recommendations.append(
                f"Address remaining {len(violations) - 5} violations after resolving priority issues."
            )

        return recommendations
