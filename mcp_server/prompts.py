"""
MCP Prompts - Pre-defined conversation templates.

Prompts are templates that MCP clients can suggest to users or use
to structure their queries. They help standardize common analysis requests.

Phase 1 prompts:
- portfolio-summary: Comprehensive overview
- risk-report: Deep risk analysis
- rebalance-plan: Rebalancing recommendations
- morning-briefing: Daily update

Phase 3-4 additions:
- More specialized prompts as agents are implemented
"""
from mcp_server import mcp


# ────────────────────────────────────────────────────────────────────────────
# Phase 1 Prompts
# ────────────────────────────────────────────────────────────────────────────


@mcp.prompt()
def portfolio_summary(session_id: str) -> str:
    """Generate a comprehensive portfolio summary with key metrics."""
    return f"""Analyse le portefeuille {session_id} et donne-moi:

1. Valeur totale et performance YTD
2. Allocation par classe d'actifs (avec graphique)
3. Top 3 et Flop 3 performers
4. Exposition par devise
5. Principaux risques identifiés
6. Recommandation en une phrase

Format: Utilise des KPI cards pour les métriques clés, un pie chart pour l'allocation,
et un bar chart pour les tops/flops.
"""


@mcp.prompt()
def risk_report(session_id: str) -> str:
    """Deep risk analysis of the portfolio."""
    return f"""Fais une analyse de risque complète du portefeuille {session_id}:

1. Risk metrics (VaR, Sharpe, Beta) pour chaque position cotée
2. Matrice de corrélation et diversification score
3. Stress test sur les scénarios historiques
4. Exposition devises et concentration par position
5. Recommandations pour réduire le risque

Note: Les tools d'analyse quantitative seront disponibles en Phase 2.
Pour l'instant, fais une analyse qualitative basée sur les expositions et concentrations.
"""


@mcp.prompt()
def rebalance_plan(session_id: str, target_profile: str = "moderate") -> str:
    """Generate a rebalancing plan."""
    return f"""Propose un plan de rebalancement pour le portefeuille {session_id}
vers un profil {target_profile}:

1. Allocation actuelle vs allocation cible
2. Positions à renforcer / alléger (avec montants suggérés)
3. Impact estimé sur le rendement et le risque
4. Ordres suggérés avec priorités

Profils de référence:
- Conservative: 60% Bonds, 30% Equities, 10% Cash
- Moderate: 50% Equities, 40% Bonds, 10% Cash/Others
- Aggressive: 70% Equities, 20% Bonds, 10% Alternatives

Format: Pie charts (actuel vs cible) + tableau des ajustements recommandés.
"""


@mcp.prompt()
def morning_briefing(session_id: str) -> str:
    """Daily morning briefing on portfolio positions."""
    return f"""Briefing matinal pour le portefeuille {session_id}:

1. Mouvements overnight sur les positions cotées
2. News impactant les positions (via web search si disponible)
3. Alertes techniques (RSI, MACD) — Phase 2
4. Actions suggérées pour aujourd'hui

Note: Les données de marché live et les alertes techniques seront disponibles en Phase 2.
Pour l'instant, donne un aperçu basé sur les positions du portefeuille.
"""


# ────────────────────────────────────────────────────────────────────────────
# Phase 3-4 Prompts (Placeholders)
# ────────────────────────────────────────────────────────────────────────────


@mcp.prompt()
def compliance_check(session_id: str) -> str:
    """Full compliance and concentration analysis."""
    return f"""Vérifie la conformité du portefeuille {session_id}:

1. Concentration par position (limite: 30% max)
2. Concentration par secteur (limite: 40% max)
3. Exposition devises (limite: 70% max par devise)
4. Liquidité (minimum 5% cash/équivalents)

[Phase 4] Le tool check_compliance() automatisera cette analyse.
"""


@mcp.prompt()
def dividend_analysis(session_id: str) -> str:
    """Dividend income optimization analysis."""
    return f"""Analyse l'optimisation du rendement dividende pour le portefeuille {session_id}:

1. Rendement actuel (yield total)
2. Historique des dividendes perçus
3. Positions à fort rendement (> 3% yield)
4. Opportunités d'optimisation

[Phase 4] Le tool analyze_dividends() automatisera cette analyse.
"""
