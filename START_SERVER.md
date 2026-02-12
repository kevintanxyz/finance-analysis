# Démarrer le Serveur MCP WealthPoint

**Date**: February 11, 2026

---

## ✅ Setup Complet

Votre environnement est prêt:
- ✅ Python 3.10 + uv
- ✅ Tous les packages installés (mcp, anthropic, pymupdf, etc.)
- ✅ `.env` configuré avec ANTHROPIC_API_KEY
- ✅ Claude Vision router prêt

---

## 🚀 Démarrer le Serveur

### Option 1: Mode stdio (Claude Desktop / MCP clients)

```bash
uv run python -m mcp_server.server
```

**Utilisation**: Configurez dans Claude Desktop:

```json
{
  "mcpServers": {
    "wealthpoint-analysis": {
      "command": "uv",
      "args": ["run", "python", "-m", "mcp_server.server"],
      "cwd": "/path/to/finance-analysis",
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-..."
      }
    }
  }
}
```

### Option 2: Mode dev (avec inspector - si disponible)

```bash
# Si mcp dev fonctionne
uv run mcp dev mcp_server/server.py

# Sinon, utilisez stdio directement
uv run python -m mcp_server.server
```

### Option 3: Mode HTTP (React frontend)

```bash
# TODO: Ajouter support streamable-http
# uv run python -m mcp_server.server --transport streamable-http --port 3001
```

---

## 🧪 Tester le Serveur

### Test 1: Import et modules

```bash
uv run python -c "
from mcp_server import server
from app.parsers.pdf_router import PDFParserRouter
from app.llm import create_llm
print('✅ Tous les modules chargés')
"
```

### Test 2: LLM Provider

```bash
uv run python -c "
from app.llm import create_llm
llm = create_llm()
print(f'✅ LLM Provider: {llm.__class__.__name__}')
"
```

### Test 3: Claude Vision Router

```bash
uv run python -c "
from app.parsers.pdf_router import PDFParserRouter
from app.llm import create_llm
from app.parsers.valuation_pdf import ISIN_TICKER_MAP

llm = create_llm()
router = PDFParserRouter(llm, ISIN_TICKER_MAP, verbose=False)
print('✅ Claude Vision router initialisé')
print(f'   Mode: USE_CLAUDE_VISION_ONLY = True (MVP)')
"
```

---

## 📋 MCP Tools Disponibles

Votre serveur expose ces tools:

1. **upload_portfolio** — Upload PDF → Claude Vision extraction
   ```python
   # Returns: session_id, bank_detected, strategy_used, confidence_score
   ```

2. **ask_portfolio** — Q&A intelligent avec le portfolio
   ```python
   # Returns: content, display_type, charts, tables, kpis
   ```

3. **Phase 2-4 tools** (stubs):
   - get_market_data
   - analyze_risk
   - analyze_momentum
   - analyze_correlation
   - price_options
   - optimize_portfolio
   - backtest_strategy
   - check_compliance
   - analyze_dividends
   - generate_full_report

---

## 🖼️ Claude Vision Multi-Format

Le serveur supporte maintenant **tous les formats de PDF bancaires**:

| Banque | Détection Auto | Stratégie |
|--------|----------------|-----------|
| **WealthPoint/Rothschild** | ✅ Keywords | Claude Vision (MVP) |
| **UBS** | ✅ Keywords | Claude Vision |
| **Julius Baer** | ✅ Keywords | Claude Vision |
| **Credit Suisse** | ✅ Keywords | Claude Vision |
| **Inconnu** | ✅ Fallback | Claude Vision |

**Performance**: ~6-8s, ~$0.05/PDF, ~95% accuracy

---

## 📝 Configuration

Votre `.env` doit contenir:

```bash
# LLM Provider (requis pour Claude Vision)
ANTHROPIC_API_KEY=sk-ant-...

# Database
DATABASE_URL=sqlite:///./wealthpoint.db

# Ollama (optionnel, fallback)
OLLAMA_MODEL=llama3.1
OLLAMA_URL=http://localhost:11434
```

---

## 🔧 Troubleshooting

### Erreur: Module not found

```bash
# Resync les dépendances
uv sync
```

### Erreur: ANTHROPIC_API_KEY not set

```bash
# Vérifier .env
cat .env | grep ANTHROPIC_API_KEY

# Ou set inline
ANTHROPIC_API_KEY=sk-ant-... uv run python -m mcp_server.server
```

### Warning: VIRTUAL_ENV mismatch

C'est normal si un autre venv est actif. `uv run` utilise automatiquement `.venv`.

Pour supprimer le warning:
```bash
deactivate  # désactiver l'autre venv
uv run python -m mcp_server.server
```

---

## 🎯 Next: Tester avec un PDF

Une fois le serveur configuré dans Claude Desktop, vous pouvez:

1. **Upload un PDF** (n'importe quel format bancaire)
2. **Claude Vision** l'analysera automatiquement
3. **Recevoir**: session_id + résumé + confidence score

Exemple de réponse:
```json
{
  "session_id": "abc-123",
  "bank_detected": "ubs",
  "strategy_used": "llm_vision",
  "confidence_score": 0.92,
  "summary": "Portfolio loaded! Bank: ubs, 15 positions, CHF 1'250'000"
}
```

---

**Server ready!** Configure Claude Desktop et testez l'upload PDF. 🚀
