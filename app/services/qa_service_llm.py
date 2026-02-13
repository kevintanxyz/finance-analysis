"""
Q&A Service with LLM integration.

This service uses an LLM (Claude or Ollama) to interpret user questions
and generate responses with appropriate display_type for the frontend.

It combines:
1. Pattern matching to identify question type
2. Data extraction from portfolio
3. LLM to generate natural language response + display format
"""
import json
from typing import Any
from app.llm import LLMProvider
from app.llm.prompts import QA_SYSTEM_PROMPT


class QAService:
    """Q&A service with LLM integration."""

    def __init__(self, llm: LLMProvider):
        """
        Initialize Q&A service.

        Args:
            llm: LLM provider (Claude or Ollama)
        """
        self.llm = llm

    async def ask(self, portfolio_data: dict, question: str) -> dict:
        """
        Answer a question about the portfolio.

        Args:
            portfolio_data: Portfolio data as dict (from PortfolioData.model_dump())
            question: User question in French or English

        Returns:
            dict with:
            - content: Text answer
            - display_type: How to display (text, kpi_cards, pie_chart, etc.)
            - charts: Array of chart data (optional)
            - tables: Array of table data (optional)
            - kpis: Array of KPI cards (optional)
        """
        # Build user prompt with portfolio data
        user_prompt = self._build_user_prompt(portfolio_data, question)

        # Call LLM
        try:
            response_text = await self.llm.complete(
                system=QA_SYSTEM_PROMPT,
                user=user_prompt,
                response_format="json",
            )

            # Parse JSON response
            response = json.loads(response_text)

            # Ensure required fields
            if "content" not in response:
                response["content"] = response_text

            if "display_type" not in response:
                response["display_type"] = "text"

            return response

        except json.JSONDecodeError:
            # Fallback if LLM doesn't return valid JSON
            return {
                "content": response_text,
                "display_type": "text",
            }

        except Exception as e:
            return {
                "content": f"Error processing question: {str(e)}",
                "display_type": "text",
                "error": str(e),
            }

    def _build_user_prompt(self, portfolio_data: dict, question: str) -> str:
        """
        Build user prompt with portfolio data context.

        Args:
            portfolio_data: Portfolio data dict
            question: User question

        Returns:
            Formatted prompt string
        """
        # Extract key portfolio info for context
        summary = {
            "extraction_date": portfolio_data.get("extraction_date"),
            "valuation_date": portfolio_data.get("valuation_date"),
            "mandate": portfolio_data.get("mandate", {}),
            "portfolio_details": portfolio_data.get("portfolio_details", {}),
            "total_value_chf": portfolio_data.get("total_value_chf"),
            "positions_count": len(portfolio_data.get("positions", [])),
            "asset_allocation": portfolio_data.get("asset_allocation", []),
            "currency_exposure": portfolio_data.get("currency_exposure", []),
            "regional_exposure": portfolio_data.get("regional_exposure", []),
            "sector_exposure": portfolio_data.get("sector_exposure", []),
            "pnl_overview": portfolio_data.get("pnl_overview", {}),
            "pnl_detail": portfolio_data.get("pnl_detail", {}),
            "performance": portfolio_data.get("performance", []),
            "tops": portfolio_data.get("tops", []),
            "flops": portfolio_data.get("flops", []),
            "transactions_count": len(portfolio_data.get("transactions", [])),
            "risk_analysis": portfolio_data.get("risk_analysis", {}),
        }

        # Include full positions data if question seems position-specific
        q_lower = question.lower()
        if any(keyword in q_lower for keyword in ["position", "liste", "list", "détail", "detail"]):
            summary["positions"] = portfolio_data.get("positions", [])

        # Include full transactions if question seems transaction-specific
        if any(keyword in q_lower for keyword in ["transaction", "opération", "operation", "achat", "vente", "buy", "sell", "historique", "history"]):
            summary["transactions"] = portfolio_data.get("transactions", [])

        prompt = f"""**PORTFOLIO DATA:**
```json
{json.dumps(summary, indent=2, ensure_ascii=False)}
```

**USER QUESTION:**
{question}

**INSTRUCTIONS:**
Based on the portfolio data above, answer the user's question. Your response MUST be valid JSON with the following structure:

{{
  "content": "Natural language answer in the same language as the question",
  "display_type": "text|kpi_cards|pie_chart|bar_chart|table|line_chart|mixed",
  "charts": [],  // Optional: array of chart data
  "tables": [],  // Optional: array of table data
  "kpis": []     // Optional: array of KPI cards
}}

Choose the most appropriate display_type based on the question:
- Simple facts → "text"
- Key metrics → "kpi_cards"
- Allocation/exposure → "pie_chart"
- Top/flop performers → "bar_chart"
- Positions list → "table"
- Performance over time → "line_chart"
- Complex answer → "mixed" (text + charts/tables)

IMPORTANT: Use Swiss French number formatting (apostrophe as thousands separator: 2'988.44).
"""

        return prompt
