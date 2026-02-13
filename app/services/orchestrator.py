"""
MCP Tool Orchestrator - Routes user questions to appropriate MCP tools.

Uses LLM to analyze the user's question and determine which specialized tool to call:
- Risk analysis → analyze_risk
- Correlation → analyze_correlation
- Portfolio optimization → optimize_portfolio
- Rebalancing → recommend_rebalancing
- Simple Q&A → ask_portfolio (fallback)
"""
import json
from typing import Any
from app.llm import LLMProvider


# Tool catalog with user-friendly descriptions
TOOL_CATALOG = {
    "get_market_data": {
        "description": "Obtenir les données de marché en temps réel pour les positions cotées",
        "keywords": ["marché", "market", "prix", "price", "cours", "quote", "actualiser", "refresh"],
        "params": ["session_id"],
    },
    "analyze_risk": {
        "description": "Analyser le risque d'une position spécifique (VaR, stress tests, drawdown)",
        "keywords": ["risque", "risk", "var", "stress", "drawdown", "volatilité", "volatility"],
        "params": ["session_id", "ticker"],
    },
    "analyze_momentum": {
        "description": "Analyser le momentum d'une position (tendances, signaux techniques)",
        "keywords": ["momentum", "tendance", "trend", "rsi", "macd", "technique", "technical"],
        "params": ["session_id", "ticker"],
    },
    "analyze_correlation": {
        "description": "Analyser la corrélation entre plusieurs positions",
        "keywords": ["corrélation", "correlation", "diversification", "lien", "relation"],
        "params": ["session_id", "tickers"],
    },
    "price_options": {
        "description": "Valoriser des options (calls/puts) avec Black-Scholes",
        "keywords": ["option", "call", "put", "strike", "black-scholes", "greek"],
        "params": ["session_id", "ticker", "strike_price", "maturity_days", "option_type"],
    },
    "optimize_portfolio": {
        "description": "Optimiser l'allocation du portefeuille (Markowitz, frontière efficiente)",
        "keywords": ["optimiser", "optimize", "markowitz", "allocation optimale", "frontière", "efficient frontier"],
        "params": ["session_id", "tickers", "target_return"],
    },
    "check_compliance": {
        "description": "Vérifier la conformité du portefeuille (limites de concentration)",
        "keywords": ["conformité", "compliance", "limite", "concentration", "règle", "regulation"],
        "params": ["session_id", "max_single_position_pct", "max_sector_pct"],
    },
    "analyze_dividends": {
        "description": "Analyser les dividendes du portefeuille (rendement, historique)",
        "keywords": ["dividende", "dividend", "rendement", "yield", "distribution"],
        "params": ["session_id"],
    },
    "analyze_margin": {
        "description": "Analyser l'utilisation de la marge et les coûts associés",
        "keywords": ["marge", "margin", "levier", "leverage", "emprunt", "borrowing"],
        "params": ["session_id", "margin_interest_rate"],
    },
    "generate_full_report": {
        "description": "Générer un rapport complet du portefeuille (PDF exportable)",
        "keywords": ["rapport", "report", "export", "pdf", "complet", "full", "résumé global"],
        "params": ["session_id"],
    },
    "analyze_portfolio_profile": {
        "description": "Analyser le profil d'investisseur (tolérance au risque, objectifs)",
        "keywords": ["profil", "profile", "investisseur", "investor", "caractéristique", "tolérance"],
        "params": ["session_id"],
    },
    "analyze_security": {
        "description": "Analyser en détail une valeur spécifique (fondamentaux, valorisation)",
        "keywords": ["analyser", "analyze", "valeur", "security", "fondamentaux", "fundamentals", "valorisation"],
        "params": ["session_id", "ticker"],
    },
    "recommend_rebalancing": {
        "description": "Recommander un rééquilibrage du portefeuille vers une allocation cible",
        "keywords": ["rééquilibrage", "rebalancing", "réallocation", "ajuster", "adjust", "modifier allocation"],
        "params": ["session_id", "target_equity_pct", "target_bonds_pct", "target_cash_pct"],
    },
    "get_portfolio_allocation": {
        "description": "Afficher l'allocation actuelle par classe d'actifs (actions, obligations, cash)",
        "keywords": ["allocation", "répartition", "breakdown", "composition", "asset class"],
        "params": ["session_id"],
    },
}


ORCHESTRATOR_SYSTEM_PROMPT = """You are a portfolio analysis tool orchestrator. Your job is to analyze user questions and determine which specialized MCP tool to call.

Available tools:
{tool_catalog}

Based on the user's question, determine:
1. Which tool is most appropriate
2. What parameters to extract from the question
3. If the question is too vague, suggest clarifications

Your response MUST be valid JSON with this structure:
{{
  "tool_name": "tool_name or null if none matches",
  "confidence": 0.0-1.0,
  "params": {{"param1": "value1", "param2": "value2"}},
  "reasoning": "Why you chose this tool",
  "missing_params": ["param1", "param2"],  // If tool needs params not provided in question
  "clarification_needed": "Question to ask user if params missing"
}}

Rules:
- If the question is a simple fact query (total value, allocation, performance), set tool_name to null (will use simple Q&A)
- If the question requires specialized analysis (risk, optimization, correlation), select the appropriate tool
- Extract ticker symbols from position names if mentioned in the question
- For French questions, recognize position names like "Roche", "Nestlé", "LVMH" and map to tickers
- If a required parameter is missing, set "clarification_needed" with a question to ask the user

Examples:
- "Quel est le risque de Roche?" → analyze_risk with ticker=ROG.SW
- "Corrélation entre Apple et Microsoft" → analyze_correlation with tickers=["AAPL", "MSFT"]
- "Optimise mon portefeuille pour 8% de rendement" → optimize_portfolio with target_return=0.08
- "Quelle est la valeur totale?" → null (simple Q&A)
"""


class ToolOrchestrator:
    """Determines which MCP tool to call based on user question."""

    def __init__(self, llm: LLMProvider):
        """
        Initialize orchestrator.

        Args:
            llm: LLM provider for tool selection
        """
        self.llm = llm

    async def route(self, question: str, portfolio_data: dict) -> dict:
        """
        Determine which tool to call and extract parameters.

        Args:
            question: User question
            portfolio_data: Portfolio data for context (tickers, positions, etc.)

        Returns:
            dict with:
            - tool_name: str | None (None = use simple Q&A)
            - confidence: float
            - params: dict
            - reasoning: str
            - missing_params: list[str]
            - clarification_needed: str | None
        """
        # Build tool catalog description
        catalog_desc = "\n".join([
            f"- {name}: {info['description']}\n  Params: {', '.join(info['params'])}\n  Keywords: {', '.join(info['keywords'])}"
            for name, info in TOOL_CATALOG.items()
        ])

        # Build context with available tickers
        tickers = [p.get("ticker") for p in portfolio_data.get("positions", []) if p.get("ticker")]
        position_names = [p.get("name") for p in portfolio_data.get("positions", []) if p.get("name")]

        user_prompt = f"""**USER QUESTION:**
{question}

**PORTFOLIO CONTEXT:**
- Available tickers: {', '.join(tickers[:20])}
- Position names: {', '.join(position_names[:20])}

Determine which tool to call and extract parameters.
"""

        try:
            response_text = await self.llm.complete(
                system=ORCHESTRATOR_SYSTEM_PROMPT.format(tool_catalog=catalog_desc),
                user=user_prompt,
                response_format="json",
            )

            response = json.loads(response_text)

            # Ensure required fields
            if "tool_name" not in response:
                response["tool_name"] = None
            if "confidence" not in response:
                response["confidence"] = 0.5
            if "params" not in response:
                response["params"] = {}
            if "missing_params" not in response:
                response["missing_params"] = []
            if "clarification_needed" not in response:
                response["clarification_needed"] = None

            return response

        except json.JSONDecodeError:
            # Fallback: use simple Q&A
            return {
                "tool_name": None,
                "confidence": 0.3,
                "params": {},
                "reasoning": "Failed to parse LLM response, defaulting to simple Q&A",
                "missing_params": [],
                "clarification_needed": None,
            }

        except Exception as e:
            return {
                "tool_name": None,
                "confidence": 0.0,
                "params": {},
                "reasoning": f"Error during routing: {str(e)}",
                "missing_params": [],
                "clarification_needed": None,
                "error": str(e),
            }

    def get_available_capabilities(self) -> list[dict]:
        """
        Get list of available capabilities for display to user.

        Returns:
            List of dicts with user-friendly capability descriptions
        """
        return [
            {
                "category": "Données de marché",
                "capabilities": [
                    "Actualiser les prix et données de marché",
                    "Voir les variations du jour (1d, 5d, 1m)",
                ],
            },
            {
                "category": "Analyse de risque",
                "capabilities": [
                    "Analyser le risque d'une position (VaR, drawdown)",
                    "Effectuer des stress tests",
                    "Calculer la volatilité",
                ],
            },
            {
                "category": "Analyse technique",
                "capabilities": [
                    "Analyser le momentum d'une position",
                    "Identifier les tendances (RSI, MACD)",
                    "Analyser la corrélation entre positions",
                ],
            },
            {
                "category": "Optimisation",
                "capabilities": [
                    "Optimiser l'allocation du portefeuille",
                    "Recommander un rééquilibrage",
                    "Calculer la frontière efficiente",
                ],
            },
            {
                "category": "Options & Dérivés",
                "capabilities": [
                    "Valoriser des options (calls/puts)",
                    "Calculer les Greeks",
                ],
            },
            {
                "category": "Revenus",
                "capabilities": [
                    "Analyser les dividendes",
                    "Projeter les revenus futurs",
                ],
            },
            {
                "category": "Conformité",
                "capabilities": [
                    "Vérifier les limites de concentration",
                    "Contrôler la conformité réglementaire",
                ],
            },
            {
                "category": "Rapports",
                "capabilities": [
                    "Générer un rapport complet (PDF)",
                    "Analyser le profil d'investisseur",
                    "Obtenir un résumé global",
                ],
            },
        ]
