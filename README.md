# WealthPoint Analysis Intelligence Platform

**Model Context Protocol (MCP) Server** pour l'analyse de portefeuilles financiers avec interface React conversationnelle.

## 🎯 Architecture

```
┌─────────────────┐      ┌──────────────────────────────────────────┐
│  Portfolio PDF  │      │     WealthPoint MCP Server (Python)      │
│  (Pictet, UBS)  │─────▶│                                          │
└─────────────────┘      │  ┌──────────┐  ┌────────────────────┐   │
                         │  │  Claude  │  │  16 MCP Tools      │   │
                         │  │  Vision  │─▶│  ├─ upload_portfolio│   │
                         │  │  Parser  │  │  ├─ ask_portfolio   │   │
                         │  └──────────┘  │  ├─ analyze_risk    │   │
                         │                │  ├─ analyze_momentum │   │
                         │                │  ├─ get_market_data  │   │
                         │                │  └─ ... (11 more)   │   │
                         │                └────────────────────┘   │
                         └──────────────────────────────────────────┘
                                          │
                                          │ HTTP (JSON-RPC)
                                          │ Port 3001
                                          ▼
                         ┌──────────────────────────────────────────┐
                         │     React Frontend (TypeScript)          │
                         │                                          │
                         │  ┌────────────┐  ┌──────────────────┐   │
                         │  │  Chat UI   │  │  Dashboard       │   │
                         │  │  (Q&A)     │  │  (KPIs + Charts) │   │
                         │  └────────────┘  └──────────────────┘   │
                         │                                          │
                         │  Vite + React 18 + shadcn/ui + Recharts │
                         └──────────────────────────────────────────┘
                                   http://localhost:5173
```

---

## 🚀 Quick Start

### Prérequis

- **Python 3.10.16** (via pyenv recommandé)
- **Node.js 18+** (avec npm)
- **Claude API Key** (pour le parser Vision)

### 1. Installation Backend (MCP Server)

```bash
# Clone le repo
cd /Users/kevintan/Documents/Projects/wealthpoint-projects/finance-analysis

# Installer Python 3.10.16 avec pyenv (si pas déjà fait)
pyenv install 3.10.16
pyenv local 3.10.16

# Créer et activer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Installation Frontend (React)

```bash
# Aller dans le dossier frontend
cd frontend

# Installer les dépendances
npm install
```

### 3. Configuration

**Backend** - Créer `.env` à la racine avec:
```env
ANTHROPIC_API_KEY=your_claude_api_key_here
```

**Frontend** - Le fichier `frontend/.env` est déjà configuré:
```env
VITE_MCP_SERVER_URL=http://localhost:3001
VITE_MCP_TRANSPORT=streamable-http
```

---

## 🎮 Lancer l'Application

### Option A: Deux Terminaux (Recommandé)

#### Terminal 1: Backend MCP Server

```bash
# Aller à la racine du projet
cd /Users/kevintan/Documents/Projects/wealthpoint-projects/finance-analysis

# Activer l'environnement Python
source .venv/bin/activate

# Démarrer le serveur MCP en mode HTTP
python -m mcp_server.server --transport streamable-http --port 3001
```

**Sortie attendue:**
```
Starting WealthPoint Analysis MCP Server in Streamable HTTP mode on port 3001...
INFO:     Uvicorn running on http://0.0.0.0:3001 (Press CTRL+C to quit)
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

✅ **Le serveur MCP est prêt quand vous voyez** `Application startup complete.`

#### Terminal 2: Frontend React

```bash
# Aller dans le dossier frontend
cd /Users/kevintan/Documents/Projects/wealthpoint-projects/finance-analysis/frontend

# Démarrer le dev server Vite
npm run dev
```

**Sortie attendue:**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

✅ **Le frontend est prêt!** Ouvrir: **http://localhost:5173/**

---

### Option B: Script de Lancement (Un Seul Terminal)

Créer `start.sh` à la racine:

```bash
#!/bin/bash

# Démarrer le backend en arrière-plan
echo "🚀 Starting MCP Server..."
source .venv/bin/activate
python -m mcp_server.server --transport streamable-http --port 3001 &
BACKEND_PID=$!

# Attendre que le backend soit prêt
sleep 3

# Démarrer le frontend
echo "🎨 Starting Frontend..."
cd frontend
npm run dev

# Cleanup: tuer le backend quand on arrête le frontend
trap "kill $BACKEND_PID" EXIT
```

Utilisation:
```bash
chmod +x start.sh
./start.sh
```

Arrêter: `Ctrl+C` (tue les deux serveurs)

---

## 🎯 Utilisation

### 1. Upload un PDF de Portfolio

1. Ouvrir **http://localhost:5173/**
2. Cliquer sur **"Upload PDF"**
3. Sélectionner un PDF de valuation (Pictet, UBS, WealthPoint)
4. Cliquer sur **"Upload & Analyze"**
5. Attendre le toast de confirmation → Session ID apparaît

### 2. Chat Conversationnel

Une fois le PDF uploadé, poser des questions en langage naturel:

**Exemples de questions:**
- "Quelle est l'allocation de mon portefeuille ?"
- "Montre-moi les 5 meilleures performances"
- "Analyse le risque de mon portefeuille"
- "Quel est l'effet momentum sur mes actions ?"
- "Calcule la corrélation entre mes positions"
- "Donne-moi le prix live de toutes mes positions"

Les réponses peuvent inclure:
- Texte formaté (Markdown)
- Tableaux interactifs
- Graphiques (Recharts)

### 3. Dashboard Visuel

1. Aller sur **http://localhost:5173/dashboard**
2. Voir les KPIs:
   - Valeur totale du portefeuille (CHF)
   - Performance YTD (%)
   - Allocation Equities (%)
   - Score de risque
3. Graphiques:
   - **Pie Chart**: Allocation par classe d'actifs
   - **Line Chart**: Performance historique
4. Table détaillée de l'allocation

---

## 📦 16 Outils MCP Disponibles

### Upload & Data
1. **upload_portfolio** - Upload PDF et extraction avec Claude Vision
2. **get_portfolio_allocation** - Allocation par classe d'actifs

### Analyse de Marché
3. **get_market_data** - Prix live, P/E, beta, volume
4. **analyze_risk** - Sharpe, Sortino, VaR, Max Drawdown
5. **analyze_momentum** - RSI, MACD, SMA crossovers
6. **analyze_correlation** - Matrice de corrélation + diversification
7. **price_options** - Valorisation d'options (Black-Scholes)

### Optimisation & Stratégie
8. **optimize_portfolio** - Optimisation Markowitz (frontière efficiente)
9. **recommend_rebalancing** - Recommandations de rebalancing
10. **analyze_portfolio_profile** - Profil investisseur + risk score

### Analyse Avancée
11. **check_compliance** - Vérification limites réglementaires
12. **analyze_dividends** - Analyse des dividendes (yield, payout)
13. **analyze_margin** - Analyse de marge et levier

### Agents
14. **research_investment** - Recherche Perplexity sur un ticker
15. **generate_full_report** - Rapport PDF complet (8 sections)
16. **ask_portfolio** - Q&A naturel sur le portefeuille

---

## 🛠️ Technologies

### Backend (Python 3.10.16)
- **FastMCP** - MCP server framework
- **Anthropic Claude API** - PDF parsing avec Vision
- **uvicorn** - ASGI server pour HTTP transport
- **yfinance** - Market data
- **pdfplumber** - Fallback PDF extraction
- **numpy/scipy** - Calculs financiers

### Frontend (React 18 + TypeScript)
- **Vite** - Build tool
- **React Router** - Routing
- **shadcn/ui** - Component library (Radix UI + Tailwind)
- **Recharts** - Data visualization
- **TanStack Query** - Server state management
- **Axios** - HTTP client pour MCP JSON-RPC
- **React Markdown** - Markdown rendering

---

## 📂 Structure du Projet

```
finance-analysis/
├── mcp_server/                    # Backend MCP Server
│   ├── server.py                  # Point d'entrée (FastMCP + uvicorn)
│   ├── tools.py                   # 16 MCP tools implementations
│   ├── prompts.py                 # Prompts pour ask_portfolio
│   ├── resources.py               # MCP resources (portfolio data)
│   └── __init__.py
│
├── app/                           # Core business logic
│   ├── parsers/
│   │   ├── llm_extractor.py       # Claude Vision PDF parser
│   │   ├── pdf_router.py          # Strategy pattern (Vision/pdfplumber)
│   │   ├── valuation_pdf.py       # Regex fallback parser
│   │   └── bank_configs.py        # Bank-specific configs
│   ├── analysis/
│   │   ├── risk_calculator.py     # Risk metrics (Sharpe, VaR, etc.)
│   │   ├── momentum_calculator.py # Technical indicators
│   │   ├── correlation_calculator.py
│   │   ├── options_calculator.py  # Black-Scholes
│   │   └── portfolio_optimizer.py # Markowitz optimization
│   ├── models/
│   │   ├── portfolio.py           # Pydantic data models
│   │   └── analysis.py
│   ├── llm/
│   │   └── claude.py              # Anthropic API client
│   └── services/
│       ├── session_store.py       # Session management
│       └── market_service.py      # yfinance wrapper
│
├── frontend/                      # React Frontend
│   ├── src/
│   │   ├── App.tsx                # Routes
│   │   ├── pages/
│   │   │   ├── Chat.tsx           # Chat UI principale
│   │   │   ├── Dashboard.tsx      # Dashboard avec KPIs
│   │   │   ├── Positions.tsx
│   │   │   ├── Transactions.tsx
│   │   │   └── Settings.tsx
│   │   ├── components/
│   │   │   ├── chat/              # Chat UI components
│   │   │   │   ├── ChatContainer.tsx
│   │   │   │   ├── ChatMessage.tsx
│   │   │   │   ├── ChatToolResult.tsx
│   │   │   │   ├── ChatInput.tsx
│   │   │   │   └── ChatMessageList.tsx
│   │   │   ├── charts/            # Recharts components
│   │   │   │   ├── AllocationPieChart.tsx
│   │   │   │   └── PerformanceLineChart.tsx
│   │   │   ├── portfolio/
│   │   │   │   └── PDFUploadDialog.tsx
│   │   │   └── ui/                # shadcn/ui primitives
│   │   ├── services/
│   │   │   ├── mcp-client.ts      # HTTP client (JSON-RPC)
│   │   │   ├── mcp-tools.ts       # Typed wrappers pour 16 tools
│   │   │   └── mcp-types.ts       # TypeScript types
│   │   └── contexts/
│   │       └── ThemeContext.tsx
│   ├── package.json
│   └── .env                       # Config MCP server URL
│
├── tests/                         # Tests unitaires
├── requirements.txt               # Python dependencies
├── .env                           # Backend config (ANTHROPIC_API_KEY)
├── PROGRESS.md                    # Phase-by-phase progress
├── CONVENTIONS.md                 # Coding conventions
├── PHASE_5_SUMMARY.md             # Phase 5 React implementation
└── README.md                      # Ce fichier
```

---

## 🔧 Debugging

### Backend ne démarre pas

**Erreur: `Python version incorrect`**
```bash
# Vérifier la version
python --version  # Doit être 3.10.16

# Si pas 3.10.16, forcer pyenv
eval "$(pyenv init --path)" && eval "$(pyenv init -)"
pyenv local 3.10.16
source .venv/bin/activate
```

**Erreur: `ModuleNotFoundError`**
```bash
# Réinstaller les dépendances
source .venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

**Erreur: `Port 3001 already in use`**
```bash
# Trouver le processus
lsof -ti:3001

# Tuer le processus
kill -9 $(lsof -ti:3001)

# Ou utiliser un autre port
python -m mcp_server.server --transport streamable-http --port 3002
# Et modifier frontend/.env: VITE_MCP_SERVER_URL=http://localhost:3002
```

### Frontend ne se connecte pas au backend

**Erreur: `Network Error` dans la console**

1. Vérifier que le backend est démarré (`http://localhost:3001/mcp` doit répondre)
2. Vérifier `frontend/.env`:
   ```env
   VITE_MCP_SERVER_URL=http://localhost:3001
   ```
3. Redémarrer le frontend: `npm run dev`

**Erreur: `CORS`**
- FastMCP gère automatiquement CORS pour localhost
- Si problème, vérifier `mcp_server/server.py` (ligne ~65)

### PDF Upload échoue

**Erreur: `ANTHROPIC_API_KEY not found`**
```bash
# Vérifier que .env existe à la racine
cat .env

# Doit contenir:
# ANTHROPIC_API_KEY=sk-ant-...

# Redémarrer le backend
```

**Erreur: `PDF parsing failed`**
- Claude Vision peut échouer sur certains formats
- Fallback pdfplumber devrait prendre le relais
- Vérifier les logs backend pour détails

---

## 📊 Performance & Caching

### Cache Claude Vision
- Les PDFs parsés par Claude Vision sont cachés dans `./cache/claude_vision/`
- Basé sur le hash SHA256 du PDF
- Cache hit → Pas d'appel API → Instantané

### Cache Market Data
- yfinance data cachée 5 minutes par défaut
- Configurable dans `app/services/market_service.py`

### Session Storage
- Sessions stockées en mémoire (dict)
- Perdu au redémarrage du serveur
- TODO: Persister dans SQLite/Redis

---

## 🧪 Testing

### Test Backend MCP

```bash
# Test healthcheck
curl http://localhost:3001/

# Test MCP endpoint (nécessite un JSON-RPC request)
curl -X POST http://localhost:3001/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

### Test Frontend

```bash
cd frontend
npm run test       # Jest tests (si configuré)
npm run build      # Test production build
npm run preview    # Preview production build
```

### Test Integration Complet

Voir [CLAUDE_DESKTOP_TEST_PROMPTS.md](CLAUDE_DESKTOP_TEST_PROMPTS.md) pour une liste complète de prompts de test.

---

## 🚀 Déploiement

### Backend (Production)

**Option 1: Serveur Linux**
```bash
# Utiliser gunicorn + uvicorn workers
gunicorn mcp_server.server:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:3001
```

**Option 2: Docker**
```dockerfile
FROM python:3.10.16-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "mcp_server.server", "--transport", "streamable-http", "--port", "3001"]
```

### Frontend (Production)

```bash
cd frontend

# Build
npm run build

# Deploy le dossier dist/ sur:
# - Vercel
# - Netlify
# - Cloudflare Pages
# - S3 + CloudFront

# Ou servir avec nginx:
# nginx.conf:
# location / {
#   root /var/www/finance-analysis/dist;
#   try_files $uri /index.html;
# }
```

**Variables d'environnement production:**
```env
# .env.production
VITE_MCP_SERVER_URL=https://your-mcp-server.com
VITE_MCP_TRANSPORT=streamable-http
```

---

## 📚 Documentation Complète

- **[PROGRESS.md](PROGRESS.md)** - Historique détaillé des phases 1-5
- **[CONVENTIONS.md](CONVENTIONS.md)** - Conventions de code Python + React
- **[PHASE_5_SUMMARY.md](PHASE_5_SUMMARY.md)** - Implémentation React détaillée
- **[PHASE_5_PDF_DASHBOARD_COMPLETE.md](PHASE_5_PDF_DASHBOARD_COMPLETE.md)** - PDF Upload + Dashboard
- **[CLAUDE_DESKTOP_SETUP.md](CLAUDE_DESKTOP_SETUP.md)** - Configuration Claude Desktop
- **[CLAUDE_DESKTOP_TEST_PROMPTS.md](CLAUDE_DESKTOP_TEST_PROMPTS.md)** - Prompts de test
- **[PORTFOLIO_TOOLS_BUGS.md](PORTFOLIO_TOOLS_BUGS.md)** - Bugs connus et fixes

---

## 🤝 Contributing

### Ajouter un nouvel outil MCP

1. Définir la fonction dans `mcp_server/tools.py`:
```python
@mcp.tool()
async def my_new_tool(session_id: str, param: str) -> dict:
    """Description de l'outil"""
    # Implémentation
    return {"result": "data"}
```

2. Ajouter le wrapper TypeScript dans `frontend/src/services/mcp-tools.ts`:
```typescript
export async function myNewTool(sessionId: string, param: string) {
  return mcpClient.callTool<{ result: string }>(
    "my_new_tool",
    { session_id: sessionId, param }
  );
}
```

3. Tester dans le chat: `"Appelle my_new_tool avec param=test"`

### Ajouter un nouveau type de graphique

1. Créer le composant dans `frontend/src/components/charts/`:
```typescript
// MyChart.tsx
export function MyChart({ data }: MyChartProps) {
  return <ResponsiveContainer>...</ResponsiveContainer>;
}
```

2. Intégrer dans `ChatToolResult.tsx`:
```typescript
// Detect my custom data shape
if ("my_field" in chartData[0]) {
  return <MyChart data={chartData} />;
}
```

---

## 📄 Licence

MIT

---

## 🙋 Support

Pour questions ou bugs:
1. Consulter [PROGRESS.md](PROGRESS.md) pour l'historique
2. Vérifier [PORTFOLIO_TOOLS_BUGS.md](PORTFOLIO_TOOLS_BUGS.md) pour bugs connus
3. Ouvrir une issue GitHub

---

**Version**: 1.0.0 (Phase 5 Complete)
**Last Updated**: February 12, 2026
**Status**: ✅ MVP Ready for Production
