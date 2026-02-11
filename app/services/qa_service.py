"""
Q&A Service — answers questions about the portfolio.

Two modes:
1. Rule-based: pattern matching for common financial questions (no LLM needed)
2. LLM-based: forwards structured data + question to Claude/OpenAI (optional)
"""
from __future__ import annotations

import re
from typing import Optional

from app.models.portfolio import PortfolioData


class PortfolioQA:
    """Answer questions about a parsed portfolio."""

    def __init__(self, data: PortfolioData, raw_text: str = ""):
        self.data = data
        self.raw_text = raw_text

    def answer(self, question: str) -> dict:
        """Route question to the best handler. Returns {answer, data}."""
        q = question.lower().strip()

        # ── Total value ────────────────────────────────────────────────
        if any(w in q for w in ["total", "valeur totale", "combien", "worth", "nav"]):
            if any(w in q for w in ["total", "valeur", "combien", "worth", "nav", "portefeuille"]):
                return self._total_value()

        # ── Allocation ─────────────────────────────────────────────────
        if any(w in q for w in ["allocation", "répartition", "breakdown", "composition"]):
            return self._allocation()

        # ── Performance ────────────────────────────────────────────────
        if any(w in q for w in ["performance", "rendement", "return", "p&l", "pnl", "profit"]):
            return self._performance()

        # ── Top / Best performers ──────────────────────────────────────
        if any(w in q for w in ["top", "best", "meilleur", "performer"]):
            return self._tops()

        # ── Flop / Worst performers ────────────────────────────────────
        if any(w in q for w in ["flop", "worst", "pire", "loss", "perdant"]):
            return self._flops()

        # ── Currency exposure ──────────────────────────────────────────
        if any(w in q for w in ["currency", "devise", "fx", "dollar", "euro", "chf", "usd", "eur"]):
            if any(w in q for w in ["exposure", "exposition", "répartition", "allocation"]):
                return self._currency_exposure()

        # ── Regional exposure ──────────────────────────────────────────
        if any(w in q for w in ["region", "géograph", "country", "pays", "zone"]):
            return self._regional_exposure()

        # ── Sector exposure ────────────────────────────────────────────
        if any(w in q for w in ["sector", "secteur", "industry"]):
            return self._sector_exposure()

        # ── Specific position ──────────────────────────────────────────
        for pos in self.data.positions:
            name_lower = pos.name.lower()
            # Check if the question mentions this position
            if any(word in q for word in name_lower.split() if len(word) > 3):
                return self._position_detail(pos.name)

        # ── Listed / Tickers ───────────────────────────────────────────
        if any(w in q for w in ["listed", "coté", "ticker", "action", "equity", "stock"]):
            return self._listed_positions()

        # ── Risk ───────────────────────────────────────────────────────
        if any(w in q for w in ["risk", "risque", "scenario", "stress", "drawdown"]):
            return self._risk()

        # ── Bonds ──────────────────────────────────────────────────────
        if any(w in q for w in ["bond", "obligation", "fixed income", "yield", "duration"]):
            return self._bonds()

        # ── Transactions ───────────────────────────────────────────────
        if any(w in q for w in ["transaction", "achat", "vente", "buy", "sell", "trade"]):
            return self._transactions()

        # ── Summary ────────────────────────────────────────────────────
        if any(w in q for w in ["summary", "résumé", "overview", "aperçu"]):
            return self._summary()

        # ── Fallback ───────────────────────────────────────────────────
        return {
            "answer": (
                "Je peux répondre aux questions sur: la valeur totale, "
                "l'allocation, la performance, les tops/flops, l'exposition "
                "devises/régions/secteurs, les positions individuelles, "
                "le risque, les obligations, et les transactions. "
                "Essayez de reformuler votre question."
            ),
            "data": {"available_topics": [
                "total value", "allocation", "performance", "tops", "flops",
                "currency exposure", "regional exposure", "sector exposure",
                "positions", "listed positions", "risk", "bonds", "transactions",
                "summary",
            ]},
        }

    # ── Handlers ───────────────────────────────────────────────────────

    def _total_value(self) -> dict:
        d = self.data
        return {
            "answer": (
                f"La valeur totale du portefeuille est de CHF {d.total_value_chf:,.2f} "
                f"au {d.valuation_date}."
            ),
            "data": {
                "total_value_chf": d.total_value_chf,
                "valuation_date": d.valuation_date,
                "currency": d.portfolio_details.currency,
            },
        }

    def _allocation(self) -> dict:
        alloc = {a.asset_class: {"value_chf": a.value_chf, "weight_pct": a.weight_pct}
                 for a in self.data.asset_allocation}
        lines = [f"- {a.asset_class}: CHF {a.value_chf:,.2f} ({a.weight_pct:.2f}%)"
                 for a in self.data.asset_allocation]
        return {
            "answer": "Allocation du portefeuille:\n" + "\n".join(lines),
            "data": {"allocation": alloc},
        }

    def _performance(self) -> dict:
        pnl = self.data.pnl_overview
        detail = self.data.pnl_detail
        return {
            "answer": (
                f"Performance totale: {pnl.total_pnl_pct:.2f}% (CHF {pnl.total_pnl_value:,.2f}). "
                f"P&L non réalisé marché: CHF {detail.unrealized_market_pnl:,.2f}, "
                f"P&L non réalisé FX: CHF {detail.unrealized_fx_pnl:,.2f}."
            ),
            "data": {
                "total_pnl_pct": pnl.total_pnl_pct,
                "total_pnl_value": pnl.total_pnl_value,
                "unrealized_market": detail.unrealized_market_pnl,
                "unrealized_fx": detail.unrealized_fx_pnl,
                "periods": [p.model_dump() for p in self.data.performance],
            },
        }

    def _tops(self) -> dict:
        lines = [f"- {t.name} ({t.currency}): {t.pct:+.2f}%"
                 for t in self.data.tops]
        return {
            "answer": "Meilleures performances YTD:\n" + "\n".join(lines),
            "data": {"tops": [t.model_dump() for t in self.data.tops]},
        }

    def _flops(self) -> dict:
        lines = [f"- {t.name} ({t.currency}): {t.pct:+.2f}%"
                 for t in self.data.flops]
        return {
            "answer": "Pires performances YTD:\n" + "\n".join(lines),
            "data": {"flops": [t.model_dump() for t in self.data.flops]},
        }

    def _currency_exposure(self) -> dict:
        lines = [f"- {e.name}: CHF {e.value_chf:,.2f} ({e.weight_pct:.2f}%)"
                 for e in self.data.currency_exposure]
        return {
            "answer": "Exposition par devise:\n" + "\n".join(lines),
            "data": {"currencies": [e.model_dump() for e in self.data.currency_exposure]},
        }

    def _regional_exposure(self) -> dict:
        lines = [f"- {e.name}: CHF {e.value_chf:,.2f} ({e.weight_pct:.2f}%)"
                 for e in self.data.regional_exposure]
        return {
            "answer": "Exposition géographique:\n" + "\n".join(lines),
            "data": {"regions": [e.model_dump() for e in self.data.regional_exposure]},
        }

    def _sector_exposure(self) -> dict:
        lines = [f"- {e.name}: CHF {e.value_chf:,.2f} ({e.weight_pct:.2f}%)"
                 for e in self.data.sector_exposure]
        return {
            "answer": "Exposition sectorielle:\n" + "\n".join(lines),
            "data": {"sectors": [e.model_dump() for e in self.data.sector_exposure]},
        }

    def _position_detail(self, name: str) -> dict:
        pos = next((p for p in self.data.positions if p.name == name), None)
        if not pos:
            return {"answer": f"Position '{name}' non trouvée.", "data": None}
        info = {
            "name": pos.name,
            "asset_class": pos.asset_class.value,
            "currency": pos.currency,
            "isin": pos.isin,
            "quantity": pos.quantity,
            "cost_price": pos.cost_price,
            "current_quote": pos.quote,
            "value_chf": pos.value_chf,
            "weight_pct": pos.weight_pct,
            "perf_ytd_pct": pos.perf_ytd_pct,
            "is_listed": pos.is_listed,
            "ticker": pos.ticker,
        }
        pnl = ""
        if pos.cost_price and pos.quote:
            gain = pos.quote - pos.cost_price
            gain_pct = (gain / pos.cost_price) * 100
            pnl = f" P&L: {gain:+.2f} ({gain_pct:+.2f}%)."

        return {
            "answer": (
                f"{pos.name} ({pos.currency}): quote {pos.quote}, "
                f"valeur CHF {pos.value_chf:,.2f} ({pos.weight_pct:.2f}% du portefeuille). "
                f"Perf YTD: {pos.perf_ytd_pct:+.2f}%.{pnl}"
            ),
            "data": info,
        }

    def _listed_positions(self) -> dict:
        listed = self.data.listed_positions
        lines = [
            f"- {p.name} ({p.ticker}): CHF {p.value_chf:,.2f} ({p.weight_pct:.2f}%), "
            f"Perf YTD: {p.perf_ytd_pct:+.2f}%"
            for p in listed
        ]
        return {
            "answer": (
                f"{len(listed)} positions cotées (analysables via Finance-Guru):\n"
                + "\n".join(lines)
            ),
            "data": {
                "listed_positions": [
                    {"name": p.name, "ticker": p.ticker, "value_chf": p.value_chf,
                     "weight_pct": p.weight_pct, "perf_ytd_pct": p.perf_ytd_pct}
                    for p in listed
                ],
                "tickers": self.data.listed_tickers,
            },
        }

    def _risk(self) -> dict:
        ra = self.data.risk_analysis
        lines = [f"- {s.scenario}: {s.impact_pct:+.2f}%" for s in ra.scenarios]
        return {
            "answer": "Analyse de scénarios de stress:\n" + "\n".join(lines),
            "data": {"scenarios": [s.model_dump() for s in ra.scenarios]},
        }

    def _bonds(self) -> dict:
        bonds = [p for p in self.data.positions
                 if p.asset_class == "Bonds"]
        lines = []
        for b in bonds:
            extra = ""
            if b.ytm:
                extra += f" YTM: {b.ytm}%"
            if b.modified_duration:
                extra += f" Duration: {b.modified_duration}"
            if b.maturity_date:
                extra += f" Maturity: {b.maturity_date}"
            lines.append(
                f"- {b.name} ({b.currency}): CHF {b.value_chf:,.2f} "
                f"({b.weight_pct:.2f}%){extra}"
            )
        return {
            "answer": f"{len(bonds)} positions obligataires:\n" + "\n".join(lines),
            "data": {"bonds": [b.model_dump() for b in bonds]},
        }

    def _transactions(self) -> dict:
        txns = self.data.transactions
        lines = [
            f"- {t.date}: {t.operation_type} {t.instrument} — "
            f"{t.amount} @ {t.price} {t.settlement_ccy} ({t.op_value:,.2f})"
            for t in txns[:20]  # Limit to 20
        ]
        return {
            "answer": f"{len(txns)} transactions:\n" + "\n".join(lines),
            "data": {"transactions": [t.model_dump() for t in txns]},
        }

    def _summary(self) -> dict:
        d = self.data
        listed = d.listed_positions
        return {
            "answer": (
                f"📊 Portefeuille au {d.valuation_date}\n"
                f"Valeur totale: CHF {d.total_value_chf:,.2f}\n"
                f"Performance: {d.pnl_overview.total_pnl_pct:.2f}%\n"
                f"Positions: {len(d.positions)} (dont {len(listed)} cotées)\n"
                f"Devises: {', '.join(e.name for e in d.currency_exposure)}\n"
                f"Top performer: {d.tops[0].name if d.tops else 'N/A'} "
                f"({d.tops[0].pct:+.2f}%)" if d.tops else ""
            ),
            "data": {
                "total_value": d.total_value_chf,
                "performance_pct": d.pnl_overview.total_pnl_pct,
                "positions_count": len(d.positions),
                "listed_count": len(listed),
                "tickers": d.listed_tickers,
            },
        }
