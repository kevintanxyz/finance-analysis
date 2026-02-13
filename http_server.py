"""
Simple HTTP server wrapper for MCP tools
Designed for React frontend - no complex session management

Architecture:
- /tools/call: Direct MCP tool calls (for simple use cases)
- /chat: Claude API integration with MCP tools (conversational AI)
- /upload: PDF upload convenience endpoint
"""
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import base64
import sys
import uvicorn
import os
from typing import Optional

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import MCP tools
from mcp_server import mcp

# Import and register all tools
from mcp_server import tools, resources, prompts  # noqa: F401

# Import external MCP servers manager
from app.external_mcp import get_external_servers

# Import Anthropic SDK for Claude API
try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Warning: anthropic package not installed. /chat endpoint will not work.", file=sys.stderr)

app = FastAPI(title="WealthPoint MCP HTTP API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup: Initialize external MCP servers
@app.on_event("startup")
async def startup_event():
    """Initialize external MCP servers on startup"""
    print("🚀 Initializing external MCP servers (Exa, Bright Data, Sequential Thinking, EODHD)...", file=sys.stderr)
    try:
        external_servers = await get_external_servers()
        tools = await external_servers.get_all_tools()
        print(f"✅ External MCP servers ready with {len(tools)} tools", file=sys.stderr)
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize external MCP servers: {e}", file=sys.stderr)
        print("   Continuing without external tools...", file=sys.stderr)


# Shutdown: Cleanup external MCP servers
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown external MCP servers on application exit"""
    print("🛑 Shutting down external MCP servers...", file=sys.stderr)
    try:
        external_servers = await get_external_servers()
        await external_servers.shutdown()
    except Exception as e:
        print(f"Error during shutdown: {e}", file=sys.stderr)


class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: dict = {}


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    history: list[ChatMessage] = []


def get_user_friendly_status(tool_name: str) -> str:
    """
    Convert technical tool names to user-friendly French messages
    """
    # Mapping of tool names to user-friendly messages
    friendly_messages = {
        # Portfolio data retrieval
        "get_portfolio_allocation": "📊 Récupération de votre allocation...",
        "ask_portfolio_question": "🔍 Analyse de votre portefeuille...",
        "get_portfolio_summary": "📋 Génération du résumé...",
        "get_positions": "💼 Chargement de vos positions...",
        "get_portfolio_metadata": "ℹ️ Récupération des informations...",

        # Market data
        "get_market_data": "📈 Mise à jour des prix du marché...",
        "get_price_history": "📉 Chargement de l'historique des prix...",
        "get_intraday_prices": "⚡ Récupération des prix en temps réel...",

        # Risk analysis
        "calculate_var": "⚠️ Calcul du risque (VaR)...",
        "calculate_volatility": "📊 Analyse de la volatilité...",
        "calculate_max_drawdown": "📉 Calcul du drawdown maximum...",
        "stress_test": "🔬 Test de résistance en cours...",
        "calculate_sharpe_ratio": "📈 Calcul du ratio de Sharpe...",
        "calculate_beta": "📊 Calcul du beta...",

        # Technical analysis
        "calculate_rsi": "📊 Calcul du RSI...",
        "calculate_macd": "📈 Calcul du MACD...",
        "detect_trend": "🔍 Détection de la tendance...",

        # Correlation
        "calculate_correlation": "🔗 Analyse de corrélation...",
        "get_correlation_matrix": "📊 Génération de la matrice de corrélation...",

        # Portfolio optimization
        "optimize_portfolio": "⚙️ Optimisation du portefeuille...",
        "calculate_efficient_frontier": "📈 Calcul de la frontière efficiente...",

        # Options & derivatives
        "calculate_black_scholes": "📊 Valorisation d'option (Black-Scholes)...",
        "calculate_greeks": "📈 Calcul des Greeks...",

        # Dividends
        "get_dividend_yield": "💰 Calcul du rendement dividende...",
        "project_dividend_income": "📅 Projection des revenus futurs...",

        # Compliance
        "check_compliance": "✅ Vérification de conformité...",

        # Rebalancing
        "recommend_rebalancing": "⚖️ Analyse de rééquilibrage...",

        # Profile analysis
        "analyze_portfolio_profile": "👤 Analyse de votre profil d'investisseur...",

        # Deep analysis
        "analyze_position_deep": "🔬 Analyse approfondie en cours...",

        # Reporting
        "generate_full_report": "📄 Génération du rapport complet...",

        # News & research (external MCP servers)
        "exa_search": "🔍 Recherche d'actualités...",
        "bright_data_search": "🌐 Recherche d'informations...",
        "sequential_thinking": "🤔 Analyse en cours...",
    }

    # Return friendly message if found, otherwise create a generic one
    return friendly_messages.get(
        tool_name,
        f"⚙️ {tool_name.replace('_', ' ').title()}..."
    )


@app.get("/api/health")
async def health():
    return {"message": "WealthPoint MCP HTTP API", "status": "running"}


@app.get("/tools")
async def list_tools():
    """List all available MCP tools"""
    tools_list = []
    for tool_name, tool_func in mcp._tool_manager._tools.items():
        tools_list.append({
            "name": tool_name,
            "description": tool_func.__doc__ or "No description",
        })
    return {"tools": tools_list}


@app.post("/tools/call")
async def call_tool(request: ToolCallRequest):
    """Call an MCP tool directly"""
    tool_name = request.tool_name
    tool_args = request.arguments

    # Get the tool object
    if tool_name not in mcp._tool_manager._tools:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    tool_obj = mcp._tool_manager._tools[tool_name]

    try:
        # FastMCP Tool objects have a 'fn' attribute with the actual function
        # Try to get the callable function from the Tool object
        if hasattr(tool_obj, 'fn'):
            tool_func = tool_obj.fn
        elif callable(tool_obj):
            tool_func = tool_obj
        else:
            # Fallback: the tool_obj itself might be callable
            tool_func = tool_obj

        # Call the tool
        result = await tool_func(**tool_args)
        return {"result": result, "error": None}
    except Exception as e:
        print(f"Error calling tool {tool_name}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return {"result": None, "error": str(e)}


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint with Claude API integration.

    Claude has access to all MCP tools and decides which ones to call.
    This provides the same experience as Claude Desktop.
    """
    if not ANTHROPIC_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="Anthropic SDK not installed. Run: uv pip install anthropic"
        )

    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY environment variable not set"
        )

    try:
        # Initialize Anthropic client
        client = AsyncAnthropic(api_key=api_key)

        # Build tool definitions from MCP tools (WealthPoint + External)
        tools_definitions = await build_anthropic_tools()

        # Build messages for Claude API
        messages = []

        # Add conversation history
        for msg in request.history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # Add current user message
        messages.append({
            "role": "user",
            "content": request.message
        })

        # Build system prompt with portfolio context
        system_prompt = """You are an AI assistant helping with portfolio analysis.

You have access to a comprehensive set of tools:

**Portfolio Analysis Tools** (WealthPoint):
- Portfolio allocation, positions, and performance
- Risk analysis, momentum analysis, correlation analysis
- Portfolio optimization and rebalancing recommendations
- Dividend analysis and compliance checks
- Market data (real-time prices, technical indicators)

**External Research Tools**:
- exa_*: Web search and research (powered by Exa AI)
- bright-data_*: Market news and data (powered by Bright Data)
- sequential-thinking_*: Enhanced reasoning capabilities
- eodhd_*: Financial market data - quotes, fundamentals, news, technical indicators, economic data (powered by EODHD)

Use these tools to provide comprehensive, well-researched answers.
"""

        # Add portfolio context if session_id exists
        if request.session_id:
            system_prompt += f"""

**IMPORTANT: A portfolio is already loaded!**
- Session ID: {request.session_id}
- The user has uploaded their portfolio and it's ready for analysis
- DO NOT ask the user to upload a portfolio - it's already loaded!
- When the user asks about their portfolio, allocation, positions, or performance, use the appropriate tools with this session_id: {request.session_id}

Available tools you can use:
- get_portfolio_allocation: Get allocation by asset class
- get_market_data: Get real-time market data
- analyze_risk: Analyze risk for a specific ticker
- analyze_momentum: Analyze momentum and technical indicators
- analyze_correlation: Analyze correlation between positions
- analyze_security: Deep analysis of a security
- optimize_portfolio: Portfolio optimization
- recommend_rebalancing: Rebalancing recommendations
- check_compliance: Compliance checks
- analyze_dividends: Dividend analysis
- generate_full_report: Generate complete report

Always use the session_id ({request.session_id}) when calling these tools.
"""

        system_prompt += """

**RESPONSE STYLE - CRITICAL INSTRUCTIONS:**
- Be CONCISE and DIRECT - answer the specific question asked
- For simple queries (e.g., "tops and flops"), provide a brief, structured answer
- Only provide deep analysis when explicitly requested (e.g., "analyze in detail", "explain why")
- Don't repeat information or add unnecessary context
- **DO NOT add suggestions, next steps, or additional recommendations at the end unless EXPLICITLY asked**
- **Answer the question, then STOP. Don't be overly helpful with unsolicited advice**

**PROFESSIONAL TONE - ABSOLUTELY CRITICAL:**
You are a PROFESSIONAL FINANCIAL ANALYST, not a casual chatbot. Maintain a serious, respectable tone:
- **NO multiple emojis** (❌ "🚀🚀🚀", "⭐⭐⭐", "💰💰")
- **NO childish language** (❌ "GAGNANT!", "SUPER!", "Génial!")
- **NO excessive exclamation marks** (❌ "Performance Exceptionnelle!!!", use "Performance exceptionnelle" instead)
- **USE professional terminology** (✅ "Performance supérieure", "Sous-performance", "Volatilité élevée")
- Emojis: MAX 1 per section header for visual clarity ONLY (e.g., "📊 Performance" is OK, "🚀🚀 GAGNANT!" is NOT)
- Write like a Bloomberg analyst or Swiss private bank report - professional, factual, precise

**Example:**
- Question: "Quels sont mes top et flop performers?"
- ❌ BAD: "🏆 GAGNANT: TotalEnergies (+12.69%) 🚀🚀 Performance Exceptionnelle!!!"
- ✅ GOOD: "Meilleure performance: TotalEnergies (+12.69% sur 1 mois) - Soutenu par la hausse du pétrole et dividende attractif (5.29%)"
- THEN STOP.

When presenting financial data:
- Use Swiss formatting (apostrophe as thousands separator: 1'234.56)
- Provide context and interpretation, but ONLY what's relevant to the question
- Highlight risks and opportunities ONLY when asked or critical
- Be conservative in recommendations

## Rich Formatting Support

You can return responses in TWO formats:

**Format 1 - Simple text** (default):
Return plain text with markdown formatting. Use this for simple explanations and conversations.

**Format 2 - Structured blocks** (for rich content):
When your response contains news, tables, or charts, return ONLY a JSON object (no additional text before or after) with this structure:

```json
{
  "blocks": [
    {
      "type": "text",
      "content": "Your markdown text here..."
    },
    {
      "type": "news",
      "items": [
        {
          "title": "News title",
          "url": "https://...",
          "summary": "Brief summary",
          "source": "Source name",
          "date": "2025-01-15"
        }
      ]
    },
    {
      "type": "table",
      "caption": "Table caption (optional)",
      "headers": ["Column 1", "Column 2", "Column 3"],
      "rows": [
        ["Data 1", "Data 2", "Data 3"],
        ["Data 4", "Data 5", "Data 6"]
      ]
    },
    {
      "type": "chart",
      "chartType": "line",
      "title": "Chart title",
      "data": [
        {"date": "2025-01", "value": 100},
        {"date": "2025-02", "value": 105}
      ],
      "config": {
        "xKey": "date",
        "yKey": "value",
        "xLabel": "Period",
        "yLabel": "Performance (%)"
      }
    },
    {
      "type": "chart",
      "chartType": "pie",
      "title": "Allocation",
      "data": [
        {"name": "Equities", "value": 60, "color": "#3b82f6"},
        {"name": "Bonds", "value": 30, "color": "#10b981"},
        {"name": "Cash", "value": 10, "color": "#f59e0b"}
      ]
    }
  ]
}
```

**When to use structured blocks:**
- News/articles: Use "news" blocks with clickable links
- Performance/timeseries data: Use "chart" type "line"
- Allocations/distributions: Use "chart" type "pie"
- Comparative data: Use "table" blocks
- Mix text + visualizations: Combine multiple block types

**Chart types:**
- `line`: For timeseries, performance evolution
- `pie`: For allocations, distributions, breakdowns
- `bar`: For comparisons, rankings

**IMPORTANT**:
- If using structured format, return ONLY the JSON (no markdown wrapper)
- All text content in blocks should use markdown formatting
- Swiss number format: 1'234.56 (apostrophe separator)
"""

        # Call Claude API with tools and prompt caching
        # Prompt caching reduces token costs by ~90% for repeated system prompts
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=8192,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}  # Cache this prompt for 5 minutes
                }
            ],
            messages=messages,
            tools=tools_definitions if tools_definitions else None,
        )

        # Process response - handle tool calls
        assistant_message = ""
        tool_results = []

        # Limit tool call iterations to prevent infinite loops and reduce latency
        max_iterations = 5
        iteration_count = 0

        # Check if Claude wants to use tools
        while response.stop_reason == "tool_use" and iteration_count < max_iterations:
            iteration_count += 1
            print(f"🔄 Tool call iteration {iteration_count}/{max_iterations}", file=sys.stderr)
            # Extract tool calls from response
            for content_block in response.content:
                if content_block.type == "text":
                    assistant_message += content_block.text
                elif content_block.type == "tool_use":
                    tool_name = content_block.name
                    tool_input = content_block.input
                    tool_use_id = content_block.id

                    print(f"Claude is calling tool: {tool_name} with args: {tool_input}", file=sys.stderr)

                    # Execute the MCP tool
                    tool_result = await execute_mcp_tool(tool_name, tool_input)

                    # Truncate large results to prevent context overflow
                    tool_result_str = str(tool_result)
                    truncated_result = truncate_tool_result(tool_result_str)

                    # Add tool result for next API call
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": truncated_result
                    })

            # If we have tool results, continue the conversation
            if tool_results:
                # Add assistant's message with tool use
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Add tool results
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

                # Call Claude again with tool results (with prompt caching)
                response = await client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=8192,
                    system=[
                        {
                            "type": "text",
                            "text": system_prompt,
                            "cache_control": {"type": "ephemeral"}  # Reuse cached prompt
                        }
                    ],
                    messages=messages,
                    tools=tools_definitions if tools_definitions else None,
                )

                # Reset for next iteration
                tool_results = []
            else:
                break

        # Extract final text response
        final_text = ""
        for content_block in response.content:
            if content_block.type == "text":
                final_text += content_block.text

        # Warn if we hit the iteration limit
        if iteration_count >= max_iterations and response.stop_reason == "tool_use":
            final_text += f"\n\n⚠️ *Note: Maximum tool call limit reached ({max_iterations} iterations). Response may be incomplete.*"
            print(f"⚠️  Reached max tool iterations ({max_iterations}). Stopping.", file=sys.stderr)

        return {
            "message": final_text,
            "session_id": request.session_id,
            "model": "claude-sonnet-4-5-20250929",
            "stop_reason": response.stop_reason,
        }

    except Exception as e:
        print(f"Error in chat endpoint: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()

        # Handle specific "prompt too long" error with user-friendly message
        error_str = str(e)
        if "prompt is too long" in error_str or "too many tokens" in error_str:
            raise HTTPException(
                status_code=400,
                detail="La réponse contient trop de données. Essayez de limiter votre requête (par exemple, demandez les 30 derniers jours au lieu de toutes les données historiques)."
            )

        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint with Claude API integration.

    Returns Server-Sent Events (SSE) stream for real-time response updates.
    """
    if not ANTHROPIC_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="Anthropic SDK not installed. Run: uv pip install anthropic"
        )

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY environment variable not set"
        )

    async def generate_stream():
        """Generator function for SSE stream"""
        try:
            client = AsyncAnthropic(api_key=api_key)
            tools_definitions = await build_anthropic_tools()

            # Build messages
            messages = []
            for msg in request.history:
                messages.append({"role": msg.role, "content": msg.content})
            messages.append({"role": "user", "content": request.message})

            # Build system prompt
            system_prompt = """You are an AI assistant helping with portfolio analysis.

You have access to a comprehensive set of tools:

**Portfolio Analysis Tools** (WealthPoint):
- Portfolio allocation, positions, and performance
- Risk analysis, momentum analysis, correlation analysis
- Portfolio optimization and rebalancing recommendations
- Dividend analysis and compliance checks
- Market data (real-time prices, technical indicators)

**External Research Tools**:
- exa_*: Web search and research (powered by Exa AI)
- bright-data_*: Market news and data (powered by Bright Data)
- sequential-thinking_*: Enhanced reasoning capabilities
- eodhd_*: Financial market data - quotes, fundamentals, news, technical indicators, economic data (powered by EODHD)

Use these tools to provide comprehensive, well-researched answers.
"""

            if request.session_id:
                system_prompt += f"""

**IMPORTANT: A portfolio is already loaded!**
- Session ID: {request.session_id}
- The user has uploaded their portfolio and it's ready for analysis
- DO NOT ask the user to upload a portfolio - it's already loaded!
- When the user asks about their portfolio, allocation, positions, or performance, use the appropriate tools with this session_id: {request.session_id}

Available tools you can use:
- get_portfolio_allocation: Get allocation by asset class
- get_market_data: Get real-time market data
- analyze_risk: Analyze risk for a specific ticker
- analyze_momentum: Analyze momentum and technical indicators
- analyze_correlation: Analyze correlation between positions
- analyze_security: Deep analysis of a security
- optimize_portfolio: Portfolio optimization
- recommend_rebalancing: Rebalancing recommendations
- check_compliance: Compliance checks
- analyze_dividends: Dividend analysis
- generate_full_report: Generate complete report

Always use the session_id ({request.session_id}) when calling these tools.
"""

            system_prompt += """

**RESPONSE STYLE - CRITICAL INSTRUCTIONS:**
- Be CONCISE and DIRECT - answer the specific question asked
- For simple queries (e.g., "tops and flops"), provide a brief, structured answer
- Only provide deep analysis when explicitly requested (e.g., "analyze in detail", "explain why")
- Don't repeat information or add unnecessary context
- **DO NOT add suggestions, next steps, or additional recommendations at the end unless EXPLICITLY asked**
- **Answer the question, then STOP. Don't be overly helpful with unsolicited advice**

**PROFESSIONAL TONE - ABSOLUTELY CRITICAL:**
You are a PROFESSIONAL FINANCIAL ANALYST, not a casual chatbot. Maintain a serious, respectable tone:
- **NO multiple emojis** (❌ "🚀🚀🚀", "⭐⭐⭐", "💰💰")
- **NO childish language** (❌ "GAGNANT!", "SUPER!", "Génial!")
- **NO excessive exclamation marks** (❌ "Performance Exceptionnelle!!!", use "Performance exceptionnelle" instead)
- **USE professional terminology** (✅ "Performance supérieure", "Sous-performance", "Volatilité élevée")
- Emojis: MAX 1 per section header for visual clarity ONLY (e.g., "📊 Performance" is OK, "🚀🚀 GAGNANT!" is NOT)
- Write like a Bloomberg analyst or Swiss private bank report - professional, factual, precise

**Example:**
- Question: "Quels sont mes top et flop performers?"
- ❌ BAD: "🏆 GAGNANT: TotalEnergies (+12.69%) 🚀🚀 Performance Exceptionnelle!!!"
- ✅ GOOD: "Meilleure performance: TotalEnergies (+12.69% sur 1 mois) - Soutenu par la hausse du pétrole et dividende attractif (5.29%)"
- THEN STOP.

When presenting financial data:
- Use Swiss formatting (apostrophe as thousands separator: 1'234.56)
- Provide context and interpretation, but ONLY what's relevant to the question
- Highlight risks and opportunities ONLY when asked or critical
- Be conservative in recommendations

## Rich Formatting Support

You can return responses in TWO formats:

**Format 1 - Simple text** (default):
Return plain text with markdown formatting. Use this for simple explanations and conversations.

**Format 2 - Structured blocks** (for rich content):
When your response contains news, tables, or charts, return ONLY a JSON object (no additional text before or after) with this structure:

```json
{
  "blocks": [
    {
      "type": "text",
      "content": "Your markdown text here..."
    },
    {
      "type": "news",
      "items": [
        {
          "title": "News title",
          "url": "https://...",
          "summary": "Brief summary",
          "source": "Source name",
          "date": "2025-01-15"
        }
      ]
    },
    {
      "type": "table",
      "caption": "Table caption (optional)",
      "headers": ["Column 1", "Column 2", "Column 3"],
      "rows": [
        ["Data 1", "Data 2", "Data 3"],
        ["Data 4", "Data 5", "Data 6"]
      ]
    },
    {
      "type": "chart",
      "chartType": "line",
      "title": "Chart title",
      "data": [
        {"date": "2025-01", "value": 100},
        {"date": "2025-02", "value": 105}
      ],
      "config": {
        "xKey": "date",
        "yKey": "value",
        "xLabel": "Period",
        "yLabel": "Performance (%)"
      }
    },
    {
      "type": "chart",
      "chartType": "pie",
      "title": "Allocation",
      "data": [
        {"name": "Equities", "value": 60, "color": "#3b82f6"},
        {"name": "Bonds", "value": 30, "color": "#10b981"},
        {"name": "Cash", "value": 10, "color": "#f59e0b"}
      ]
    }
  ]
}
```

**When to use structured blocks:**
- News/articles: Use "news" blocks with clickable links
- Performance/timeseries data: Use "chart" type "line"
- Allocations/distributions: Use "chart" type "pie"
- Comparative data: Use "table" blocks
- Mix text + visualizations: Combine multiple block types

**Chart types:**
- `line`: For timeseries, performance evolution
- `pie`: For allocations, distributions, breakdowns
- `bar`: For comparisons, rankings

**IMPORTANT**:
- If using structured format, return ONLY the JSON (no markdown wrapper)
- All text content in blocks should use markdown formatting
- Swiss number format: 1'234.56 (apostrophe separator)
"""

            # Stream the response
            max_iterations = 5
            iteration_count = 0

            async with client.messages.stream(
                model="claude-sonnet-4-5-20250929",
                max_tokens=8192,
                system=[{
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }],
                messages=messages,
                tools=tools_definitions if tools_definitions else None,
            ) as stream:
                async for text in stream.text_stream:
                    # Send text chunks as SSE
                    import json
                    yield f"data: {json.dumps({'type': 'text', 'content': text})}\n\n"

                # Get the final message to check for tool calls
                final_message = await stream.get_final_message()

                # Handle tool calls if present
                while final_message.stop_reason == "tool_use" and iteration_count < max_iterations:
                    iteration_count += 1
                    print(f"🔄 Tool call iteration {iteration_count}/{max_iterations}", file=sys.stderr)

                    tool_results = []
                    for content_block in final_message.content:
                        if content_block.type == "tool_use":
                            tool_name = content_block.name
                            tool_input = content_block.input
                            tool_use_id = content_block.id

                            # Send status update to frontend with user-friendly French messages
                            import json
                            status_msg = get_user_friendly_status(tool_name)
                            yield f"data: {json.dumps({'type': 'status', 'message': status_msg})}\n\n"

                            print(f"Claude is calling tool: {tool_name}", file=sys.stderr)

                            # Execute tool
                            tool_result = await execute_mcp_tool(tool_name, tool_input)
                            truncated_result = truncate_tool_result(str(tool_result))

                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": truncated_result
                            })

                    if tool_results:
                        # Add assistant message and tool results
                        messages.append({"role": "assistant", "content": final_message.content})
                        messages.append({"role": "user", "content": tool_results})

                        # Stream next response
                        async with client.messages.stream(
                            model="claude-sonnet-4-5-20250929",
                            max_tokens=8192,
                            system=[{
                                "type": "text",
                                "text": system_prompt,
                                "cache_control": {"type": "ephemeral"}
                            }],
                            messages=messages,
                            tools=tools_definitions if tools_definitions else None,
                        ) as new_stream:
                            async for text in new_stream.text_stream:
                                # Send text chunks as SSE with proper JSON format
                                import json
                                yield f"data: {json.dumps({'type': 'text', 'content': text})}\n\n"

                            final_message = await new_stream.get_final_message()
                    else:
                        break

        except Exception as e:
            print(f"Error in streaming endpoint: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            import json
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


async def build_anthropic_tools() -> list[dict]:
    """
    Build Anthropic tool definitions from MCP tools.

    Combines:
    - WealthPoint internal tools (portfolio analysis, risk, etc.)
    - External MCP tools (Exa search, Bright Data news, Sequential Thinking, EODHD financial data)

    Converts FastMCP tool schemas to Anthropic API format.
    """
    tools = []

    # 1. Add WealthPoint internal tools
    for tool_name, tool_obj in mcp._tool_manager._tools.items():
        # Get tool metadata
        if hasattr(tool_obj, 'fn'):
            fn = tool_obj.fn
            description = fn.__doc__ or f"Tool: {tool_name}"
        else:
            description = f"Tool: {tool_name}"

        # Get parameter schema from FastMCP
        if hasattr(tool_obj, 'parameters'):
            params_schema = tool_obj.parameters
        else:
            # Fallback: empty schema
            params_schema = {
                "type": "object",
                "properties": {},
                "required": []
            }

        # Build Anthropic tool definition
        tool_def = {
            "name": tool_name,
            "description": description.split("\n")[0][:1024],  # First line, max 1024 chars
            "input_schema": params_schema
        }

        tools.append(tool_def)

    # 2. Add external MCP tools (Exa, Bright Data, Sequential Thinking)
    try:
        external_servers = await get_external_servers()
        external_tools = await external_servers.get_all_tools()

        for ext_tool in external_tools:
            tool_def = {
                "name": ext_tool["name"],  # Already prefixed with server name
                "description": ext_tool["description"][:1024],
                "input_schema": ext_tool["input_schema"]
            }
            tools.append(tool_def)

        print(f"📦 Combined {len(tools)} tools: {len(mcp._tool_manager._tools)} WealthPoint + {len(external_tools)} external", file=sys.stderr)
    except Exception as e:
        print(f"⚠️  Could not load external tools: {e}", file=sys.stderr)
        print("   Continuing with WealthPoint tools only...", file=sys.stderr)

    # Enable tool caching: mark the last tool to cache ALL tools
    # This reduces token usage by ~90% for tool definitions on subsequent calls
    if tools:
        tools[-1]["cache_control"] = {"type": "ephemeral"}
        print(f"🔧 Tool caching enabled for {len(tools)} tools (saves ~{len(tools) * 100} tokens per call)", file=sys.stderr)

    return tools


def truncate_tool_result(result: str, max_chars: int = 15000) -> str:
    """
    Truncate tool results that are too large to prevent token overflow (TPM limits).

    Args:
        result: The tool result string
        max_chars: Maximum characters allowed (default: 15k chars ≈ 4-7k tokens)

    Returns:
        Truncated result with summary if needed
    """
    if len(result) <= max_chars:
        return result

    # Try to parse as JSON and intelligently truncate
    try:
        import json
        data = json.loads(result)

        # If it's a list, take first N items
        if isinstance(data, list):
            sample_size = min(20, len(data))  # Max 20 items to reduce token usage
            truncated_data = data[:sample_size]
            summary = {
                "truncated": True,
                "original_count": len(data),
                "sample_count": sample_size,
                "message": f"⚠️ Result truncated: showing {sample_size} of {len(data)} items to reduce token usage (TPM limits)",
                "data": truncated_data
            }
            return json.dumps(summary, ensure_ascii=False)

        # If it's a dict with a large array field
        elif isinstance(data, dict):
            modified = False
            for key, value in list(data.items()):
                if isinstance(value, list) and len(value) > 50:
                    data[key] = value[:50]
                    data[f"{key}_truncated"] = True
                    data[f"{key}_original_count"] = len(value)
                    modified = True
            if modified:
                data["_truncation_warning"] = "⚠️ Large arrays truncated to 50 items to stay within context limits"
            return json.dumps(data, ensure_ascii=False)
    except:
        pass

    # Fallback: simple string truncation
    truncated = result[:max_chars]
    return f"{truncated}\n\n⚠️ [Result truncated at {max_chars} characters to prevent context overflow. Original length: {len(result)} characters]"


async def execute_mcp_tool(tool_name: str, tool_args: dict) -> dict:
    """
    Execute an MCP tool and return the result.

    Routes to either:
    - WealthPoint internal tools (portfolio analysis, risk, etc.)
    - External MCP servers (exa_*, bright-data_*, sequential-thinking_*, eodhd_*)

    Args:
        tool_name: Name of the MCP tool
        tool_args: Arguments for the tool

    Returns:
        Tool execution result
    """
    # Check if this is an external tool (prefixed with server name)
    external_prefixes = ["exa_", "bright-data_", "sequential-thinking_", "eodhd_"]
    is_external = any(tool_name.startswith(prefix) for prefix in external_prefixes)

    if is_external:
        # Route to external MCP server
        try:
            external_servers = await get_external_servers()
            result = await external_servers.call_tool(tool_name, tool_args)

            # MCP tool results are wrapped in a result object
            if hasattr(result, 'content'):
                # Extract content from MCP result
                content_list = result.content
                if content_list and len(content_list) > 0:
                    first_content = content_list[0]
                    if hasattr(first_content, 'text'):
                        return {"result": first_content.text}
                    else:
                        return {"result": str(first_content)}
                return {"result": str(result)}
            else:
                return {"result": str(result)}
        except Exception as e:
            print(f"Error calling external tool {tool_name}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    # Execute WealthPoint internal tool
    if tool_name not in mcp._tool_manager._tools:
        return {"error": f"Tool '{tool_name}' not found"}

    tool_obj = mcp._tool_manager._tools[tool_name]

    try:
        # Extract callable function
        if hasattr(tool_obj, 'fn'):
            tool_func = tool_obj.fn
        elif callable(tool_obj):
            tool_func = tool_obj
        else:
            return {"error": f"Tool '{tool_name}' is not callable"}

        # Call the tool
        result = await tool_func(**tool_args)
        return result

    except Exception as e:
        print(f"Error executing tool {tool_name}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF file - convenience endpoint"""
    try:
        # Read file content
        content = await file.read()

        # Convert to base64
        pdf_base64 = base64.b64encode(content).decode('utf-8')

        # Call upload_portfolio tool
        tool_obj = mcp._tool_manager._tools.get("upload_portfolio")
        if not tool_obj:
            raise HTTPException(status_code=500, detail="upload_portfolio tool not found")

        # Extract the actual callable function
        if hasattr(tool_obj, 'fn'):
            tool_func = tool_obj.fn
        elif callable(tool_obj):
            tool_func = tool_obj
        else:
            tool_func = tool_obj

        result = await tool_func(
            pdf_base64=pdf_base64,
            filename=file.filename or "portfolio.pdf"
        )

        return {"result": result, "error": None}
    except Exception as e:
        print(f"Error uploading PDF: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return {"result": None, "error": str(e)}


# Serve frontend static files (React build)
# This must be AFTER all API routes to avoid conflicts
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_dist):
    # Mount static files - html=True serves index.html for all unmatched routes (SPA)
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
    print(f"✅ Frontend static files mounted from: {frontend_dist}", file=sys.stderr)
else:
    print(f"⚠️  Frontend build not found at: {frontend_dist}", file=sys.stderr)
    print("   Run 'cd frontend && npm run build' to build the frontend", file=sys.stderr)


if __name__ == "__main__":
    port = 3001

    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])

    print(f"Starting WealthPoint HTTP API on port {port}...", file=sys.stderr)
    print(f"API docs: http://localhost:{port}/docs", file=sys.stderr)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
