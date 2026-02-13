# PROMPT — WealthPoint Analysis Intelligence Platform

> Colle ce fichier dans ton IDE (Cursor, Windsurf, Claude Code) à la racine du projet.
> Il contient tout le contexte pour construire la plateforme.
>
> **Setup du projet :**
> ```bash
> # Le code existant (portfolio-api v1) est à la racine
> # Finance-Guru a été cloné comme référence :
> git clone https://github.com/AojdevStudio/Finance-Guru.git finance-guru-ref
> # ⚠️ finance-guru-ref/ est en LECTURE SEULE — ne jamais modifier ces fichiers
> # On s'en sert uniquement comme source pour adapter le code dans app/
> ```

---

## 1. VISION DU PROJET

On construit **WealthPoint** — une plateforme d'analyse de portefeuille multi-client (family office) qui :

1. **Ingère** des PDFs de valorisation bancaire (format WealthPoint/Rothschild, extensible à UBS, Julius Baer, etc.)
2. **Structure** les données financières (positions, allocation, P&L, expositions, risque)
3. **Analyse** via 8 agents IA spécialisés (repris de Finance-Guru)
4. **Répond** aux questions en langage naturel (FR/EN) via LLM (Claude + Ollama fallback)
5. **S'expose comme serveur MCP** — n'importe quel client MCP (Claude Desktop, Claude Code, Cursor, ChatGPT, custom apps) peut se connecter et utiliser les outils/agents

### Architecture en 2 couches

```
┌─────────────────────────────────────────────────────────────┐
│  CLIENTS                                                    │
│  Claude Desktop │ Claude Code │ Cursor │ React Chat │ ...   │
└───────────────────────────┬─────────────────────────────────┘
                            │ MCP Protocol (stdio / Streamable HTTP)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  MCP SERVER  (mcp-server-wealthpoint)                             │
│                                                             │
│  Tools:     upload_pdf, ask_portfolio, analyze_risk, ...    │
│  Resources: portfolio://{id}, positions://{id}, ...         │
│  Prompts:   portfolio-summary, risk-report, rebalance, ...  │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  MOTEUR INTERNE (modules Python appelés directement)   │ │
│  │  parsers/    → PDF → PortfolioData                     │ │
│  │  analysis/   → Risk, Momentum, Correlation, Options    │ │
│  │  services/   → yfinance, LLM (Claude/Ollama), SQLite   │ │
│  │  llm/        → Abstraction Claude + Ollama             │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Pas de FastAPI.** Les MCP tools appellent directement les modules Python. Le frontend React se connecte au MCP server via Streamable HTTP. Un seul serveur, une seule surface d'exposition.

Le flow est : **prompt utilisateur → MCP client → MCP server → orchestrateur détermine le(s) agent(s) nécessaire(s) → exécute → retourne le résultat structuré**

---

## 2. DÉCISIONS TECHNIQUES

| Aspect | Choix |
|--------|-------|
| **MCP SDK** | mcp (Python SDK v1.x — stable, recommandé pour prod) |
| **MCP Transport** | Streamable HTTP (frontend React + remote) + stdio (Claude Desktop/local) |
| **HTTP frontend** | Un seul endpoint `/chat` via Streamable HTTP ou mini serveur intégré au MCP |
| **LLM principal** | Anthropic Claude (API) |
| **LLM fallback** | Ollama (local) |
| **Données marché** | yfinance (v1) |
| **Base de données** | SQLite (v1, migratable PostgreSQL) |
| **PDF parsing** | Hybrid : pdfplumber (tables) + Claude Vision API (structuration LLM) + Camelot (fallback) |
| **Calculs** | pandas, numpy, scipy |
| **Périmètre analyse** | Tout le portefeuille (coté + obligations + structurés + PE) |
| **Usage** | Multi-client family office |
| **Tax optimizer** | Pas en v1 (stub agent uniquement) |
| **Auth** | Simple API key pour v1 |
| **Python** | 3.12+ |
| **Validation** | Pydantic v2 |

---

## 3. CE QUI EXISTE DÉJÀ (portfolio-api v1.0) — À MIGRER VERS MCP

> **Le code v1 utilise FastAPI.** On le migre vers un MCP server pur.
> Les modules réutilisables : `models/`, `parsers/`, `services/`. Le reste (routers, main.py) est remplacé par `mcp_server/`.

### 3.1 Structure actuelle

```
portfolio-api/
├── app/
│   ├── main.py                 # FastAPI app (CORS, health, router)
│   ├── models/
│   │   └── portfolio.py        # Pydantic: PortfolioData, Position, MarketAnalysis...
│   ├── parsers/
│   │   ├── __init__.py         # detect_pdf_type(), extract_raw_text(), parse_pdf()
│   │   └── valuation_pdf.py    # Parser WealthPoint (positions HARDCODÉES — à refactorer)
│   ├── routers/
│   │   └── portfolio.py        # Endpoints REST
│   └── services/
│       ├── market_service.py   # yfinance: prix, risk metrics, momentum, corrélation
│       ├── qa_service.py       # Q&A rule-based (pattern matching FR/EN)
│       └── session_store.py    # In-memory dict (à remplacer par SQLite)
├── scripts/
│   ├── demo.sh
│   └── test_client.py
├── requirements.txt
├── Dockerfile / docker-compose.yml
└── README.md
```

### 3.2 Endpoints existants (v1 — seront remplacés par MCP tools)

```
POST /api/v1/upload                          → Upload PDF, retourne session_id
GET  /api/v1/portfolio/{session_id}          → Portfolio JSON complet
GET  /api/v1/portfolio/{session_id}/positions → Positions filtrables
POST /api/v1/ask/{session_id}                → Q&A naturel
GET  /api/v1/listed/{session_id}             → Positions cotées + tickers
GET  /api/v1/market/{session_id}             → Données marché live
GET  /api/v1/risk/{session_id}/{ticker}      → Risk metrics (Sharpe, VaR, Beta...)
GET  /api/v1/momentum/{session_id}/{ticker}  → RSI, MACD, SMA
GET  /api/v1/correlation/{session_id}        → Matrice corrélation
```

### 3.3 Modèle de données principal

```python
class PortfolioData(BaseModel):
    valuation_date: str
    mandate: MandateDetails          # mandate, custody_bank, portfolio_number
    portfolio_details: PortfolioDetails  # currency (CHF), profile
    asset_allocation: list[AllocationItem]
    total_value_chf: float
    currency_exposure: list[ExposureItem]
    regional_exposure: list[ExposureItem]
    sector_exposure: list[ExposureItem]
    pnl_overview: PnLOverview
    pnl_detail: PnLDetail
    tops: list[TopFlop]
    flops: list[TopFlop]
    performance: list[PerformancePeriod]
    positions: list[Position]        # Toutes les positions
    transactions: list[Transaction]
    risk_analysis: RiskAnalysis      # Stress test scenarios

class Position(BaseModel):
    asset_class: AssetClass          # Cash | Bonds | Equities | Structured Products | Others
    position_type: PositionType      # cash_account | bond_fx | equity | etf | fund | commodity...
    currency: str                    # CHF, USD, EUR
    isin: Optional[str]
    name: str
    cost_price: Optional[float]
    quote: Optional[float]
    value_chf: float
    weight_pct: float
    ticker: Optional[str]            # Si coté: ROG.SW, AAPL, TTE.PA, SPY
    is_listed: bool
    # Bond: maturity_date, coupon_rate, ytm, modified_duration
```

### 3.4 ISIN → Ticker (positions cotées actuellement identifiées)

```python
ISIN_TICKER_MAP = {
    "CH0012032048": ("ROG.SW", True),   # Roche
    "FR0000120271": ("TTE.PA", True),   # TotalEnergies
    "US0378331005": ("AAPL", True),     # Apple
    "US78462F1030": ("SPY", True),      # SPDR S&P 500
    # Tout le reste → (None, False)     # Fonds, obligations, PE
}
```

### 3.5 Ce qu'on garde / ce qu'on jette

| Garder (migrer vers MCP) | Jeter (remplacé par MCP) |
|--------------------------|--------------------------|
| `models/portfolio.py` — modèles Pydantic | `main.py` — FastAPI app |
| `parsers/` — PDF extraction | `routers/` — endpoints REST |
| `services/market_service.py` — yfinance | `services/session_store.py` — in-memory |
| `services/qa_service.py` — logique Q&A | `scripts/` — demo/test client |
| ISIN→Ticker mapping | Dockerfile FastAPI |

### 3.6 Limites actuelles à corriger

1. **Parser hardcodé** : `valuation_pdf.py` a les positions en dur. Doit devenir dynamique via extraction LLM (voir section 4bis).
2. **Session in-memory** : perdu au redémarrage.
3. **Q&A pattern-matching** : pas de LLM, limité.
4. **Pas d'agents** : les outils d'analyse existent mais ne sont pas orchestrés comme Finance-Guru.
5. **Pas de tests**.
6. **Mono-client** : pas de notion de client/portefeuille multiple.

---

## 4. CE QU'ON PREND DE FINANCE-GURU

> **IMPORTANT** : Le repo Finance-Guru a été cloné dans le projet sous `./finance-guru-ref/`.
> Tu as accès direct à tout le code source. **Lis les fichiers avant de coder** — ne réinvente pas ce qui existe déjà.
>
> ```
> finance-guru-ref/              ← REPO CLONÉ — LECTURE SEULE, NE PAS MODIFIER
> ├── src/                       ← Outils d'analyse Python (à reprendre/adapter)
> │   ├── analysis/              ← risk_metrics_cli.py, correlation_cli.py, options_pricer_cli.py, itc_risk_cli.py
> │   ├── strategies/            ← optimizer.py, backtester.py
> │   ├── utils/                 ← momentum_cli.py, volatility_cli.py, validators.py
> │   └── models/                ← Pydantic models (RiskMetrics, MomentumData, etc.)
> ├── fin-guru/                  ← Système d'agents (prompts, configs, knowledge base)
> │   ├── agents/                ← Définitions des 8 agents (system prompts, rôles, outils)
> │   ├── tasks/                 ← Workflow configurations
> │   └── data/                  ← Knowledge base, user-profile template, system-context
> ├── .claude/                   ← Hooks Claude Code (référence architecture)
> │   ├── hooks/                 ← load-fin-core-config.ts, skill-activation-prompt.sh
> │   └── skills/                ← fin-core/SKILL.md (routing rules, compliance)
> ├── docs/                      ← api.md (CLI reference), hooks.md, contributing.md
> ├── tests/                     ← Tests existants
> ├── CLAUDE.md                  ← Context dev, agent-tool matrix
> └── AGENTS.md                  ← Détails agents
> ```
>
> **Workflow** : Pour chaque module à implémenter :
> 1. **Lis** le fichier source dans `finance-guru-ref/src/` ou `finance-guru-ref/fin-guru/agents/`
> 2. **Adapte** : CLI → MCP tool, argparse → Pydantic, stdout → dict return
> 3. **Intègre** dans notre structure `app/`
>
> Exemples de fichiers clés à lire :
> - `finance-guru-ref/src/analysis/risk_metrics_cli.py` → pour `app/analysis/risk_calculator.py`
> - `finance-guru-ref/src/analysis/correlation_cli.py` → pour `app/analysis/correlation.py`
> - `finance-guru-ref/src/analysis/options_pricer_cli.py` → pour `app/analysis/options_pricer.py`
> - `finance-guru-ref/src/strategies/optimizer.py` → pour `app/analysis/portfolio_optimizer.py`
> - `finance-guru-ref/src/strategies/backtester.py` → pour `app/analysis/backtester.py`
> - `finance-guru-ref/src/utils/momentum_cli.py` → pour `app/analysis/momentum.py`
> - `finance-guru-ref/src/utils/volatility_cli.py` → pour `app/analysis/volatility.py`
> - `finance-guru-ref/fin-guru/agents/*` → pour les system prompts dans `app/llm/prompts.py`
> - `finance-guru-ref/fin-guru/data/system-context.md` → pour le contexte orchestrateur
> - `finance-guru-ref/CLAUDE.md` → pour la matrice agent↔outil

### 4.1 Architecture 3 couches à conserver

Finance-Guru utilise un pattern très propre qu'on garde :

```
Pydantic Models → Calculator Classes → API Endpoints (au lieu de CLI)
     ↓                    ↓                    ↓
 Type Safety         Business Logic        Agent Access
```

**Original (Finance-Guru)** : CLI `argparse` → stdout
**Nous** : MCP tools → dict return → JSON via MCP protocol

### 4.2 Les 8 agents — convertis en MCP tools

Chaque agent Finance-Guru devient un **service Python** avec un **endpoint API dédié**.

| Agent | Rôle | Source Finance-Guru | Notre implémentation |
|-------|------|---------------------|---------------------|
| **Orchestrator** (Cassandra Holt) | Route les requêtes vers le bon agent | `fin-guru/agents/finance-orchestrator` | `app/agents/orchestrator.py` — LLM qui analyse la question et dispatch |
| **Market Researcher** | Intelligence marché, news, opportunités | `fin-guru/agents/market-researcher` | `app/agents/market_researcher.py` — yfinance + LLM analysis |
| **Quant Analyst** | Risk metrics, modèles quantitatifs | `fin-guru/agents/quant-analyst` + `src/analysis/risk_metrics_cli.py` | `app/agents/quant_analyst.py` — reprend `market_service.py` + options pricer |
| **Strategy Advisor** | Allocation, rebalancing, optimisation | `fin-guru/agents/strategy-advisor` + `src/strategies/optimizer.py` | `app/agents/strategy_advisor.py` — portfolio optimizer + backtester |
| **Compliance Officer** | Limites de concentration, risk budget | `fin-guru/agents/compliance-officer` | `app/agents/compliance_officer.py` — règles configurable par client |
| **Margin Specialist** | Analyse levier/marge | `fin-guru/agents/margin-specialist` | `app/agents/margin_specialist.py` |
| **Dividend Specialist** | Optimisation yield | `fin-guru/agents/dividend-specialist` | `app/agents/dividend_specialist.py` |
| **Tax Optimizer** | Structuration fiscale | `fin-guru/agents/tax-optimizer` | `app/agents/tax_optimizer.py` — **stub v1** (placeholder) |

### 4.3 Outils d'analyse à reprendre de `src/`

```
Finance-Guru src/              →  Notre app/analysis/
├── analysis/
│   ├── risk_metrics_cli.py    →  risk_calculator.py     (VaR, Sharpe, Sortino, Beta, Alpha, MaxDD)
│   ├── correlation_cli.py     →  correlation.py         (matrice, diversification score)
│   ├── itc_risk_cli.py        →  (skip v1 — pas d'ITC API)
│   └── options_pricer_cli.py  →  options_pricer.py      (Black-Scholes, Greeks, IV)
├── strategies/
│   ├── optimizer.py           →  portfolio_optimizer.py  (Max Sharpe, Risk Parity, Min Variance)
│   └── backtester.py          →  backtester.py          (backtest strategies)
├── utils/
│   ├── momentum_cli.py        →  momentum.py            (RSI, MACD, Golden Cross, SMA)
│   ├── volatility_cli.py      →  volatility.py          (Bollinger Bands, ATR, vol cones)
│   └── validators.py          →  validators.py          (input validation)
└── models/
    └── *.py                   →  Intégrer dans app/models/
```

### 4.4 Ce qu'on NE prend PAS

- Claude Code hooks (SessionStart, PostToolUse, Stop) → remplacé par l'API
- `.claude/` config directory → pas pertinent en mode API
- `fin-guru/data/user-profile.yaml` → remplacé par le modèle Client en DB
- `fin-guru/data/system-context.md` → intégré dans les system prompts des agents
- Fidelity CSV import → remplacé par notre PDF parser
- `setup.sh` / symlinks → remplacé par `pip install` + Docker
- MCP servers (exa, bright-data, sequential-thinking) → **REQUIS** — configurés côté client, voir section 13.7

---

## 4bis. STRATÉGIE D'EXTRACTION PDF — HYBRID LLM + PDFPLUMBER

> **Problème** : Chaque banque/gestionnaire a un format PDF différent. Écrire des regex par format = maintenable pour 1 banque, cauchemar pour 10.
> **Solution** : Extraction hybride — pdfplumber pour les tables brutes, Claude Vision pour la structuration intelligente.

### 4bis.1 Architecture d'extraction en 3 étapes

```
PDF Upload
    │
    ▼
┌──────────────────────────────────────────────────┐
│  ÉTAPE 1 — Extraction brute (pdfplumber)          │
│  pdfplumber.open(pdf) → extract_tables()          │
│  + extract_text() pour le contexte hors-tableau   │
│  Résultat : tables[][] + texte brut               │
│  Fallback : Camelot (si pdfplumber rate les        │
│  tables sans bordures)                             │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│  ÉTAPE 2 — Structuration LLM (Claude Vision)      │
│  Envoie chaque page PDF comme IMAGE à Claude       │
│  + prompt avec le schema Pydantic attendu          │
│  Claude retourne du JSON structuré                 │
│  Résultat : PortfolioData validé par Pydantic     │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│  ÉTAPE 3 — Validation croisée                      │
│  Compare les résultats pdfplumber vs Claude        │
│  Vérifie : total = somme des positions ?           │
│  P&L cohérent ? Devises valides ?                  │
│  Résultat : PortfolioData final → SQLite           │
└──────────────────────────────────────────────────┘
```

### 4bis.2 Pourquoi Claude Vision plutôt que regex

| Aspect | Regex / pdfplumber seul | Claude Vision |
|--------|-------------------------|---------------|
| Nouveau format PDF | Réécrire le parser | Fonctionne directement |
| Tableaux sans bordures | Échoue souvent | Comprend visuellement |
| Texte multi-langue (FR/EN/DE) | Patterns par langue | Comprend nativement |
| Données imbriquées | Très fragile | Comprend le contexte |
| Coût | Gratuit | ~$0.01-0.05 par page |
| Vitesse | Instantané | 2-5 sec par page |
| Fiabilité | 70-80% (nouveaux formats) | 95%+ |

**Trade-off** : On utilise pdfplumber d'abord (gratuit, rapide) et Claude Vision en complément/validation. Pour les formats connus (WealthPoint), pdfplumber suffit. Pour les nouveaux formats, Claude Vision prend le relais.

### 4bis.3 Prompt d'extraction Claude Vision

```python
EXTRACTION_SYSTEM_PROMPT = """
Tu es un expert en extraction de données financières à partir de relevés de portefeuille.
Extrais TOUTES les positions et données financières de ce document PDF.

Retourne UNIQUEMENT du JSON valide correspondant à ce schema :

{
  "valuation_date": "YYYY-MM-DD",
  "reference_currency": "CHF",
  "total_value": 0.00,
  "total_pnl": 0.00,
  "total_pnl_pct": 0.00,
  
  "allocation": {
    "cash": {"pct": 0.00, "value": 0.00},
    "bonds": {"pct": 0.00, "value": 0.00},
    "equities": {"pct": 0.00, "value": 0.00},
    "structured_products": {"pct": 0.00, "value": 0.00},
    "other": {"pct": 0.00, "value": 0.00}
  },
  
  "positions": [
    {
      "name": "str",
      "isin": "str or null",
      "asset_class": "cash|bond|equity|structured|fund|other",
      "currency": "CHF|USD|EUR|GBP",
      "quantity": 0.00,
      "purchase_price": 0.00,
      "current_price": 0.00,
      "value_chf": 0.00,
      "pnl": 0.00,
      "pnl_pct": 0.00,
      "weight_pct": 0.00,
      "maturity_date": "YYYY-MM-DD or null",
      "coupon_rate": 0.00,
      "ticker": "str or null"
    }
  ],
  
  "currency_exposure": [
    {"currency": "CHF", "pct": 0.00, "value": 0.00}
  ]
}

Règles :
- Extrais TOUTES les positions, même celles sans ISIN
- Les montants sont dans la devise du document sauf si une colonne "CHF" est explicite
- Si un champ n'est pas trouvé, mets null (pas d'invention)
- Pour les obligations : extrais maturity_date et coupon_rate si disponibles
- Pour les actions : déduis le ticker si possible (ISIN CH0012032048 → ROG.SW)
- Vérifie que la somme des positions ≈ total_value (tolérance 1%)
"""
```

### 4bis.4 Implémentation dans le code

```python
# app/parsers/llm_extractor.py

import base64
from app.llm import get_llm_provider
from app.models.portfolio import PortfolioData

class LLMPDFExtractor:
    """
    Extrait les données structurées d'un PDF via Claude Vision API.
    Envoie chaque page comme image, Claude retourne du JSON structuré.
    """
    
    async def extract(self, pdf_bytes: bytes, filename: str) -> PortfolioData:
        # 1. Convertir PDF pages → images (pdf2image ou pymupdf)
        pages_b64 = self._pdf_to_images_base64(pdf_bytes)
        
        # 2. Envoyer à Claude Vision avec le schema
        llm = get_llm_provider()
        response = await llm.extract_from_images(
            images_b64=pages_b64,
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            response_format="json"
        )
        
        # 3. Valider avec Pydantic
        portfolio = PortfolioData.model_validate_json(response)
        
        # 4. Post-traitement : ISIN → ticker mapping, devises
        portfolio = self._enrich_tickers(portfolio)
        
        return portfolio


# app/parsers/__init__.py — Router

class PDFParserRouter:
    """
    Stratégie d'extraction hybride :
    1. pdfplumber pour extraction rapide (formats connus)
    2. Claude Vision pour validation ou formats inconnus
    3. Validation croisée
    """
    
    async def parse(self, pdf_bytes: bytes, filename: str) -> PortfolioData:
        # Essayer pdfplumber d'abord (rapide, gratuit)
        pdfplumber_result = self.pdfplumber_extract(pdf_bytes)
        
        if pdfplumber_result.is_confident():  
            # Format connu, extraction complète → OK
            return pdfplumber_result
        
        # Format inconnu ou extraction partielle → Claude Vision
        llm_result = await self.llm_extract(pdf_bytes, filename)
        
        # Validation croisée si les deux ont des résultats
        if pdfplumber_result.positions:
            return self._cross_validate(pdfplumber_result, llm_result)
        
        return llm_result
```

### 4bis.5 Multi-format : une config par banque (v2+)

```python
# app/parsers/bank_configs.py

BANK_CONFIGS = {
    "wealthpoint": {
        "detect_keywords": ["WealthPoint", "Rothschild", "Edmond de Rothschild"],
        "parser": "pdfplumber",       # Format connu → pdfplumber suffit
        "table_settings": {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
        },
        "position_table_header": ["Description", "ISIN", "Quantité", "Cours"],
    },
    "ubs": {
        "detect_keywords": ["UBS", "UBS Switzerland AG"],
        "parser": "llm_vision",       # Format complexe → Claude Vision
        "extra_prompt": "UBS statements have positions split across multiple pages. "
                        "Concatenate all position tables before extracting.",
    },
    "julius_baer": {
        "detect_keywords": ["Julius Baer", "Julius Bär"],
        "parser": "llm_vision",
        "extra_prompt": "Julius Baer uses German headers (Bezeichnung, Valor, Kurs).",
    },
    "generic": {
        "detect_keywords": [],
        "parser": "llm_vision",       # Format inconnu → toujours LLM
    },
}
```

### 4bis.6 Repos open-source de référence

| Repo | Ce qu'on en tire |
|------|-----------------|
| [Schwab-PDF-Scraper](https://github.com/ethanpbrooks/Schwab-PDF-Scraper) | Pattern : PDF → positions → allocation → risk metrics (Sharpe, StdDev). Très proche de notre use case. |
| [Sparrow](https://github.com/katanaml/sparrow) | Architecture : schema JSON pré-défini + Vision LLM pour extraction. Exemple avec table d'obligations. |
| [Bank-Statement-Extractor](https://github.com/epsilonstar-02/Bank-Statement-Extractor) | Pattern hybride : pdfplumber + Camelot + Gemini AI, avec fallback rule-based. |
| [pdf-accounts](https://github.com/drkane/pdf-accounts) | Extraction minimaliste pdfplumber : pattern `<text> <number> <number>` pour états financiers. |
| [Ghostfolio](https://github.com/ghostfolio/ghostfolio) | Pas de PDF parsing, mais toute la logique de suivi portfolio + calcul de performance (ROAI). |

### 4bis.7 Multi-PDF historique (analyse sur données utilisateur)

Pour calculer VaR, Sharpe, MaxDD sur les positions **non-cotées** (obligations, structurés, fonds PE), on a besoin d'une série temporelle. Deux sources possibles :

**Source 1 — Positions cotées** : le PDF donne le poids + prix d'achat. `yfinance` donne l'historique complet. On peut tout calculer.

**Source 2 — Positions non-cotées avec multi-PDF** :
```
upload_portfolio("valuation_sept_2025.pdf")  → snapshot T-3
upload_portfolio("valuation_oct_2025.pdf")   → snapshot T-2  
upload_portfolio("valuation_nov_2025.pdf")   → snapshot T-1
upload_portfolio("valuation_dec_2025.pdf")   → snapshot T0

→ 4 points par position non-cotée → série temporelle
→ Calcul de VaR, volatilité, drawdown sur les données réelles du client
```

**Implémentation** : La table `portfolios` en SQLite stocke déjà chaque snapshot par client. Le tool `analyze_risk` détecte automatiquement si plusieurs snapshots existent pour le même client et construit la série.

```python
# app/analysis/risk_calculator.py

async def calculate_risk(session_id: str, ticker: str = None) -> dict:
    portfolio = load_portfolio(session_id)
    
    if ticker and is_listed(ticker):
        # Position cotée → yfinance
        history = yf.download(ticker, period="1y")
        return compute_metrics(history)
    
    # Position non-cotée → chercher les snapshots historiques
    client_id = portfolio.client_id
    snapshots = get_client_snapshots(client_id)  # Tous les PDFs du client
    
    if len(snapshots) >= 3:
        # Assez de points → construire série depuis les PDFs
        series = build_series_from_snapshots(snapshots, position_name)
        return compute_metrics(series)
    
    # Pas assez de data → fallback proxy benchmark
    return {
        "warning": "Insufficient historical data for full risk analysis",
        "available_metrics": {
            "pnl_since_purchase": portfolio.get_position_pnl(position_name),
            "weight": portfolio.get_position_weight(position_name),
        },
        "suggestion": "Upload more historical statements to enable full risk metrics"
    }
```

---

## 5. ARCHITECTURE CIBLE

```
wealthpoint-platform/
├── finance-guru-ref/               # CLONÉ — repo Finance-Guru LECTURE SEULE (référence)
│   ├── src/                        #   → Outils d'analyse à reprendre
│   ├── fin-guru/                   #   → Agents, prompts, knowledge base
│   ├── .claude/                    #   → Hooks, skills (référence)
│   ├── docs/                       #   → Documentation API tools
│   └── CLAUDE.md                   #   → Agent-tool matrix
│
├── mcp_server/                     # SERVEUR MCP — seule surface d'exposition
│   ├── __init__.py
│   ├── server.py                   # FastMCP server principal
│   ├── tools.py                    # MCP Tools: upload_pdf, ask, analyze_risk, etc.
│   ├── resources.py                # MCP Resources: portfolio://{id}, positions://{id}
│   └── prompts.py                  # MCP Prompts: portfolio-summary, risk-report, etc.
│
├── app/                            # MOTEUR INTERNE — modules Python (pas de serveur HTTP)
│   ├── config.py                   # Settings (API keys, DB path, LLM config)
│   ├── database.py                 # SQLite setup (SQLAlchemy/SQLModel)
│   │
│   ├── models/                     # Pydantic models
│   │   ├── portfolio.py            # (existe) PortfolioData, Position, etc.
│   │   ├── client.py               # NEW: Client, ClientPortfolio (multi-client)
│   │   └── analysis.py             # NEW: RiskMetrics, MomentumData, OptionsGreeks...
│   │
│   ├── parsers/                    # PDF ingestion (voir section 4bis)
│   │   ├── __init__.py             # PDFParserRouter : detect bank → route strategy
│   │   ├── pdfplumber_extractor.py # Extraction tables/texte via pdfplumber + Camelot fallback
│   │   ├── llm_extractor.py        # NEW: Claude Vision API → JSON structuré
│   │   ├── bank_configs.py         # NEW: Config par banque (WealthPoint, UBS, Julius Baer, generic)
│   │   ├── cross_validator.py      # NEW: Validation croisée pdfplumber vs LLM
│   │   └── base_parser.py          # Abstract base pour futurs formats
│   │
│   ├── analysis/                   # Outils de calcul (ex Finance-Guru src/)
│   │   ├── risk_calculator.py      # VaR, Sharpe, Sortino, Beta, Alpha, MaxDD, CVaR
│   │   ├── momentum.py             # RSI, MACD, SMA, Golden Cross, Bollinger
│   │   ├── volatility.py           # ATR, vol cones, Bollinger Bands
│   │   ├── correlation.py          # Matrice, diversification score
│   │   ├── options_pricer.py       # Black-Scholes, Greeks
│   │   ├── portfolio_optimizer.py  # Max Sharpe, Risk Parity, Min Variance
│   │   └── backtester.py           # Backtest avec benchmark
│   │
│   ├── llm/                        # Abstraction LLM
│   │   ├── __init__.py             # LLMProvider factory
│   │   ├── claude.py               # Anthropic Claude client
│   │   ├── ollama.py               # Ollama local client
│   │   └── prompts.py              # System prompts (repris de finance-guru-ref/fin-guru/agents/)
│   │
│   └── services/                   # Services métier
│       ├── market_service.py       # (existe) yfinance bridge
│       ├── qa_service.py           # Q&A avec LLM (pour le tool ask_portfolio)
│       └── portfolio_service.py    # CRUD portfolio + client en SQLite
│
├── tests/
│   ├── test_parsers.py
│   ├── test_analysis.py
│   ├── test_mcp_tools.py           # Tests des MCP tools (mocks)
│   └── fixtures/
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 6. MCP TOOLS & RESOURCES

Tout passe par le MCP server. Pas de FastAPI, pas de REST API séparée.

### 6.1 MCP Tools (ce que le LLM peut FAIRE)

```
upload_portfolio(pdf_base64, filename, client_id)→ Parse PDF, sauve en SQLite, retourne session_id
ask_portfolio(session_id, question)              → Q&A intelligent (session_id = contexte du PDF)
get_market_data(session_id)                      → Données marché live pour toutes les positions
analyze_risk(session_id, ticker)             → VaR, Sharpe, Sortino, Beta, Alpha
analyze_momentum(session_id, ticker)         → RSI, MACD, SMA, signaux
analyze_correlation(session_id)              → Matrice + diversification insights
price_options(session_id, ticker, strike...) → Black-Scholes, Greeks
optimize_portfolio(session_id, method)       → Allocation optimale
backtest_strategy(session_id, strategy)      → Backtest vs benchmark
check_compliance(session_id)                 → Violations et warnings
analyze_dividends(session_id)                → Yield, historique, optimisation
generate_full_report(session_id)             → Rapport complet (tous les tools)
```

### 6.2 MCP Resources (ce que le LLM peut LIRE)

```
portfolio://{session_id}                     → Portfolio complet
portfolio://{session_id}/positions           → Toutes les positions
portfolio://{session_id}/listed              → Positions cotées uniquement
portfolio://{session_id}/allocation          → Allocation par classe d'actifs
portfolio://{session_id}/exposure            → Devises, régions, secteurs
portfolio://{session_id}/pnl                 → P&L overview + détail
clients://list                               → Liste des clients
```

### 6.3 MCP Prompts (templates pré-définis)

```
portfolio-summary(session_id)                → Résumé complet avec métriques clés
risk-report(session_id)                      → Analyse de risque approfondie
rebalance-plan(session_id, target_profile)   → Plan de rebalancement
morning-briefing(session_id)                 → Briefing matinal
```

### 6.4 Frontend React — PDF Upload + Contexte persistant

Le frontend se connecte au MCP server via **Streamable HTTP** (port 3001). Le flow est :

```
1. User drop/sélectionne un PDF dans le chat
2. Frontend envoie le fichier → MCP tool upload_portfolio(pdf_bytes, client_id)
3. Le tool parse le PDF, sauve en SQLite, retourne session_id + résumé
4. Le session_id est stocké côté frontend (React state)
5. Tous les prompts suivants passent ce session_id automatiquement
6. Le portfolio reste en contexte tant que la session est active

User: [drop valuation.pdf]
→ upload_portfolio() → session_id="abc123"
→ "Portfolio chargé ! 13 positions, CHF 2'988.44"

User: "Quelle est l'allocation ?"
→ ask_portfolio(session_id="abc123", question="...")  ← session_id auto-attaché
→ pie chart allocation

User: "Et le risque de Roche ?"
→ ask_portfolio(session_id="abc123", question="...")  ← même session
→ KPI cards + interprétation
```

**Important** : le tool `upload_portfolio` doit accepter le PDF en **base64** (pas un file path) puisque le frontend ne peut pas envoyer un chemin local. Le MCP server décode, sauve temporairement, parse, puis stocke le résultat structuré en SQLite.

```python
@mcp.tool()
async def upload_portfolio(pdf_base64: str, filename: str = "valuation.pdf", 
                           client_id: str = "default") -> dict:
    """
    Upload and parse a portfolio valuation PDF.
    The PDF must be sent as a base64-encoded string.
    Returns session_id to use in all subsequent tool calls.
    
    Supports multiple bank formats (WealthPoint/Rothschild, UBS, Julius Baer, etc.)
    Uses hybrid extraction: pdfplumber (fast) + Claude Vision (intelligent).
    """
    pdf_bytes = base64.b64decode(pdf_base64)
    # PDFParserRouter.parse() → hybrid extraction → PortfolioData
    # → Save to SQLite → Return session_id
    ...
```

---

## 7. DESIGN DES AGENTS (PATTERN MCP)

### 7.1 Changement de paradigme : de "agents internes" à "MCP tools"

Dans Finance-Guru, les agents sont des system prompts que Claude charge tour à tour dans une seule conversation Claude Code. Il n'y a pas de vrai multi-agent — c'est un seul LLM qui change de persona.

**Notre approche MCP est différente et plus puissante** : chaque "agent" devient un **groupe de MCP tools** que le LLM client (Claude Desktop, etc.) peut appeler librement. C'est le LLM client qui orchestre — il décide quels tools appeler en fonction du prompt utilisateur.

```
Finance-Guru (ancien) :
  User → Claude Code → charge system prompt "Quant" → lance CLI → résultat

WealthPoint (MCP) :
  User → Claude Desktop → voit les tools disponibles → appelle analyze_risk()
                        → appelle analyze_correlation() → synthétise la réponse
```

### 7.2 Mapping agents → MCP tools

| Agent Finance-Guru | MCP Tools WealthPoint |
|---------------------|-----------------|
| Orchestrator (Cassandra) | **Le LLM client fait l'orchestration** — plus besoin d'agent interne |
| Market Researcher | `get_market_data`, `ask_portfolio` (questions marché) |
| Quant Analyst | `analyze_risk`, `analyze_momentum`, `analyze_correlation`, `price_options` |
| Strategy Advisor | `optimize_portfolio`, `backtest_strategy` |
| Compliance Officer | `check_compliance` |
| Margin Specialist | `analyze_margin` (tool dédié) |
| Dividend Specialist | `analyze_dividends` |
| Tax Optimizer | `analyze_tax` (stub v1) |

### 7.3 Les tools restent des fonctions Python simples

Chaque tool MCP est un wrapper léger qui appelle le moteur d'analyse interne :

```python
# mcp_server/tools.py

@mcp.tool()
async def analyze_risk(session_id: str, ticker: str, 
                        benchmark: str = "SPY", days: int = 90) -> dict:
    """Compute risk metrics: VaR, Sharpe, Sortino, Beta, Alpha, MaxDD."""
    # 1. Valider que le ticker est dans le portefeuille
    portfolio = get_portfolio(session_id)
    position = find_position(portfolio, ticker)
    
    # 2. Appeler le calculateur interne (pas de LLM ici — pur calcul)
    from app.analysis.risk_calculator import RiskCalculator
    calc = RiskCalculator()
    metrics = calc.compute(ticker, benchmark, days)
    
    # 3. Retourner les données structurées — le LLM client interprète
    return {
        "ticker": ticker,
        "position_name": position.name,
        "weight_pct": position.weight_pct,
        "metrics": metrics,
    }
```

### 7.4 Le Q&A intelligent reste pour le frontend React

Pour le chat React (qui n'a pas de LLM intégré), on garde l'endpoint `ask_portfolio` qui utilise notre LLM interne (Claude/Ollama) pour interpréter la question et appeler les bons outils :

```python
@mcp.tool()
async def ask_portfolio(session_id: str, question: str) -> dict:
    """
    Ask any question about a portfolio. Routes to the right analysis tools
    and returns a natural language answer with structured data.
    """
    # 1. LLM interne classifie la question et décide des actions
    # 2. Exécute les calculs nécessaires
    # 3. LLM interne synthétise en réponse avec display_type pour le frontend
    ...
```

---

## 8. ABSTRACTION LLM

```python
class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, system: str, user: str, response_format=None) -> str: ...

class ClaudeProvider(LLMProvider):
    """Anthropic Claude via API."""
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def complete(self, system, user, response_format=None) -> str:
        response = await self.client.messages.create(
            model=self.model, max_tokens=4096,
            system=system, messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text

class OllamaProvider(LLMProvider):
    """Ollama local fallback."""
    def __init__(self, model: str = "llama3.1", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    async def complete(self, system, user, response_format=None) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/api/chat", json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
            })
            return resp.json()["message"]["content"]

# Factory
def create_llm(config: Settings) -> LLMProvider:
    if config.anthropic_api_key:
        return ClaudeProvider(config.anthropic_api_key)
    return OllamaProvider(config.ollama_model, config.ollama_url)
```

---

## 9. SCHÉMA DB (SQLite v1)

```sql
CREATE TABLE clients (
    id TEXT PRIMARY KEY,         -- UUID
    name TEXT NOT NULL,
    email TEXT,
    risk_profile TEXT,           -- conservative | moderate | aggressive
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE portfolios (
    id TEXT PRIMARY KEY,         -- session_id (UUID) — clé pour tous les tool calls
    client_id TEXT REFERENCES clients(id),
    valuation_date TEXT,
    total_value_chf REAL,
    raw_text TEXT,               -- Texte brut du PDF
    data_json TEXT,              -- PortfolioData sérialisé (JSON complet)
    pdf_filename TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Le session_id (= portfolios.id) est la clé de contexte.
-- Upload PDF → crée un row → retourne session_id.
-- Tous les tools suivants reçoivent ce session_id → chargent data_json.
-- Pas de TTL : le portfolio reste en DB tant qu'il n'est pas supprimé.

CREATE TABLE analysis_cache (
    id TEXT PRIMARY KEY,
    portfolio_id TEXT REFERENCES portfolios(id),
    analysis_type TEXT,          -- risk | momentum | correlation | compliance
    ticker TEXT,
    parameters TEXT,             -- JSON des params
    result_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP         -- Cache marché: 5min. Cache PDF: jamais.
);
```

---

## 10. PLAN DE PHASES

### Phase 1 — Fondations (commence ici)

1. **MCP Server squelette** : `mcp_server/server.py` avec FastMCP. Un premier tool `upload_portfolio` qui appelle le parser.
2. **Parser PDF hybride** (section 4bis) :
   - `pdfplumber_extractor.py` : extraction dynamique via `extract_tables()` + regex. Plus de positions hardcodées.
   - `llm_extractor.py` : envoie les pages PDF comme images à Claude Vision → retourne JSON structuré via le schema Pydantic.
   - `PDFParserRouter` : pdfplumber d'abord (rapide, gratuit), Claude Vision si format inconnu ou extraction partielle, validation croisée.
3. **SQLite + modèle Client** : `app/database.py` avec SQLAlchemy/SQLModel. Tables clients + portfolios (multi-snapshot pour historique).
4. **Abstraction LLM** : Créer `app/llm/` avec Claude + Ollama providers. L'extraction PDF et le Q&A utilisent le même provider.
5. **Tool `ask_portfolio`** : Q&A avec fallback LLM + display_type pour le frontend.
6. **Tests** : pytest pour parser (pdfplumber + LLM mock), Q&A, MCP tools.

### Phase 2 — Outils d'analyse (moteur interne)

> Lis les fichiers source dans `finance-guru-ref/src/` AVANT de coder chaque module.

6. **Risk Calculator** : Reprendre de `finance-guru-ref/src/analysis/risk_metrics_cli.py` → `app/analysis/risk_calculator.py` (VaR, Sharpe, Sortino, Beta, Alpha, MaxDD, CVaR).
7. **Momentum** : Reprendre de `finance-guru-ref/src/utils/momentum_cli.py` → `app/analysis/momentum.py` (RSI, MACD, SMA, Golden Cross).
8. **Correlation** : Reprendre de `finance-guru-ref/src/analysis/correlation_cli.py` → `app/analysis/correlation.py`.
9. **Options Pricer** : Reprendre de `finance-guru-ref/src/analysis/options_pricer_cli.py` → `app/analysis/options_pricer.py` (Black-Scholes, Greeks).
10. **Portfolio Optimizer + Backtester** : Reprendre de `finance-guru-ref/src/strategies/` → `app/analysis/portfolio_optimizer.py` + `backtester.py`.

### Phase 3 — MCP Server complet

11. **MCP Resources** : Exposer portfolio data comme resources MCP (portfolio://{id}, positions, allocation, exposure).
12. **MCP Prompts** : Templates portfolio-summary, risk-report, rebalance-plan, morning-briefing.
13. **Tools d'analyse** : Brancher les calculateurs Phase 2 comme MCP tools (analyze_risk, analyze_momentum, analyze_correlation).
14. **Transport Streamable HTTP** : Pour que le frontend React puisse se connecter (port 3001).
15. **Test avec Claude Desktop** : Configurer claude_desktop_config.json avec les 4 serveurs (wealthpoint + exa + bright-data + sequential-thinking) et valider end-to-end.

### Phase 4 — Agents complets (via MCP tools)

> **Avant de coder chaque agent** : lis d'abord sa définition dans `finance-guru-ref/fin-guru/agents/`
> et les outils associés dans `finance-guru-ref/src/`. Adapte, ne réécris pas from scratch.

16. **Compliance Officer** : Tool `check_compliance` — limites de concentration, risk budget configurable par client.
17. **Options Pricer** : Tool `price_options` — Black-Scholes + Greeks depuis Finance-Guru.
18. **Strategy Advisor** : Tools `optimize_portfolio` + `backtest_strategy` — reprendre `finance-guru-ref/src/strategies/`.
19. **Margin + Dividend specialists** : Tools dédiés.
20. **Full report** : Tool `generate_full_report` — orchestre tous les tools et produit un rapport consolidé.
21. **Analyse non-cotés** : Pour les obligations → YTM, duration, convexité depuis les données PDF. Pour les fonds → NAV tracking depuis les données PDF.

### Phase 5 — Production & Frontend

22. **Frontend React Chat** : Voir section 14. Se connecte au MCP server via Streamable HTTP. Rendu conditionnel (texte, tableaux, graphiques).
23. **Multi-format PDF** : Ajouter les configs UBS, Julius Baer, Credit Suisse dans `bank_configs.py` (le LLM extractor gère déjà les formats inconnus depuis Phase 1).
24. **Multi-PDF historique** : UI pour uploader plusieurs relevés → construction automatique de séries temporelles → risk metrics sur positions non-cotées (section 4bis.7).
25. **Auth JWT** : Sécurisation multi-client.
25. **Tax Optimizer** : Fiscalité suisse (impôt anticipé, ICTax).
26. **Export** : Excel/CSV via MCP tools.

---

## 11. RÈGLES DE CODE

- **TOUJOURS lire le fichier source dans `finance-guru-ref/` AVANT de coder** un module équivalent
- Python 3.12+, type hints partout, docstrings Google-style
- Async pour tout ce qui est I/O (LLM calls, yfinance, DB)
- Pydantic v2 pour validation entrée/sortie
- Montants en CHF, format suisse (apostrophe: 2'988.44)
- Q&A bilingue FR/EN
- **Pas de FastAPI** — tout passe par le MCP server
- Chaque MCP tool doit être autonome et bien documenté (le LLM lit la docstring pour décider quand l'utiliser)
- Les MCP tools retournent des **données structurées** (JSON), PAS du texte libre — c'est le LLM client qui rédige la réponse
- Les analyses sur positions non-cotées utilisent les données du PDF (pas yfinance)
- Tout calculator doit être testable sans réseau (mocks yfinance)
- **MCP tools = wrappers légers** qui appellent `app/analysis/` et `app/services/` — pas de logique métier dans `mcp_server/`

---

## 12. CONFIG (.env)

```env
# LLM
ANTHROPIC_API_KEY=sk-ant-...
OLLAMA_MODEL=llama3.1
OLLAMA_URL=http://localhost:11434

# Database
DATABASE_URL=sqlite:///./wealthpoint.db

# API
API_KEY=your-api-key-here       # Simple auth v1
PORT=8000

# MCP Server
MCP_TRANSPORT=stdio             # stdio | streamable-http
MCP_HTTP_PORT=3001              # Port pour Streamable HTTP (frontend React)

# MCP Servers externes (configurés côté client, mais clés nécessaires)
EXA_API_KEY=your-exa-api-key                # Exa — market research, web search
BRIGHT_DATA_API_KEY=your-brightdata-token  # Bright Data — web scraping, live data
# Sequential Thinking — pas de clé API requise

# Market Data
YFINANCE_CACHE_TTL=300          # Cache 5 minutes
```

### .gitignore (ajouter)

```gitignore
finance-guru-ref/               # Repo cloné — référence uniquement, pas commité
wealthpoint.db
*.pyc
__pycache__/
.env
```

---

## 13. SERVEUR MCP — COUCHE D'EXPOSITION

Le serveur MCP est la **façade** du système. Il expose les capacités de WealthPoint sous forme de **Tools**, **Resources** et **Prompts** MCP. N'importe quel client compatible (Claude Desktop, Claude Code, Cursor, React app, etc.) peut s'y connecter.

### 13.1 Stack MCP

```python
# On utilise le SDK officiel Python MCP (v1.x stable)
# pip install "mcp[cli]"
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("wealthpoint-analysis")
```

**Dépendances clés** :
```
# requirements.txt (principales)
mcp[cli]>=1.0            # MCP SDK Python
anthropic>=0.40           # Claude API (chat + vision)
pdfplumber>=0.11          # PDF table extraction
camelot-py[base]>=0.11    # Fallback table extraction
pymupdf>=1.24             # PDF → images (pour Claude Vision)
pydantic>=2.0             # Validation models
sqlmodel>=0.0.14          # SQLite ORM
yfinance>=0.2             # Données marché
pandas>=2.0
numpy>=1.26
scipy>=1.12
```

### 13.2 MCP Tools — ce que le LLM peut FAIRE

Chaque tool correspond à une action. Le LLM client décide quel(s) tool(s) appeler en fonction du prompt utilisateur.

```python
# mcp_server/tools.py
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("wealthpoint-analysis")

# ── Upload & Parse ───────────────────────────────────────────
@mcp.tool()
async def upload_portfolio(pdf_base64: str, filename: str = "valuation.pdf",
                           client_id: str = "default") -> dict:
    """
    Parse a portfolio valuation PDF and extract structured financial data.
    The PDF must be base64-encoded (the frontend encodes it before sending).
    Returns session_id — use this ID in ALL subsequent tool calls to reference
    this portfolio. The portfolio data is persisted in SQLite.
    """
    ...

# ── Q&A Intelligent (orchestre les agents) ───────────────────
@mcp.tool()
async def ask_portfolio(session_id: str, question: str) -> dict:
    """
    Ask any question about a portfolio in natural language (French or English).
    The orchestrator automatically routes to the right specialist agent(s).
    Returns text answer + structured data (charts, tables, KPIs).
    
    Examples:
    - "Quelle est l'allocation du portefeuille ?"
    - "Top performers YTD"
    - "Analyse le risque de Roche"
    - "Should I rebalance towards more bonds?"
    """
    ...

# ── Quant Analyst Tools ──────────────────────────────────────
@mcp.tool()
async def analyze_risk(session_id: str, ticker: str, benchmark: str = "SPY", days: int = 90) -> dict:
    """
    Compute risk metrics for a listed position: VaR, Sharpe, Sortino, Beta, Alpha, Max Drawdown.
    Only works for listed positions (stocks, ETFs with tickers).
    """
    ...

@mcp.tool()
async def analyze_momentum(session_id: str, ticker: str, days: int = 90) -> dict:
    """
    Compute momentum indicators: RSI (14), MACD, SMA 20/50, Golden Cross detection.
    Returns signal interpretation (overbought/oversold/neutral, bullish/bearish).
    """
    ...

@mcp.tool()
async def analyze_correlation(session_id: str, days: int = 90) -> dict:
    """
    Compute correlation matrix between all listed positions.
    Returns matrix + diversification insights (which pairs are too correlated).
    """
    ...

@mcp.tool()
async def price_options(session_id: str, ticker: str, strike: float, 
                         expiry_days: int, option_type: str = "call") -> dict:
    """
    Black-Scholes options pricing with Greeks (Delta, Gamma, Theta, Vega, Rho).
    Use for listed positions only.
    """
    ...

# ── Strategy Advisor Tools ───────────────────────────────────
@mcp.tool()
async def optimize_portfolio(session_id: str, method: str = "max_sharpe") -> dict:
    """
    Optimize portfolio allocation for listed positions.
    Methods: max_sharpe, min_variance, risk_parity, equal_weight.
    Returns current vs recommended weights + expected improvement.
    """
    ...

@mcp.tool()
async def backtest_strategy(session_id: str, strategy: str, days: int = 365) -> dict:
    """
    Backtest a portfolio strategy against benchmark.
    Returns cumulative returns, drawdown, and comparison metrics.
    """
    ...

# ── Compliance Officer Tools ─────────────────────────────────
@mcp.tool()
async def check_compliance(session_id: str) -> dict:
    """
    Check portfolio compliance: concentration limits, sector exposure,
    currency risk, single position max weight.
    Returns violations and warnings.
    """
    ...

# ── Market Researcher Tools ──────────────────────────────────
@mcp.tool()
async def get_market_data(session_id: str) -> dict:
    """
    Get live market data for all listed positions: current price,
    1d/5d/1m changes, PE ratio, dividend yield, beta.
    """
    ...

# ── Dividend Specialist Tools ────────────────────────────────
@mcp.tool()
async def analyze_dividends(session_id: str) -> dict:
    """
    Analyze dividend yield, payout history, and income optimization
    for all equity and fund positions.
    """
    ...

# ── Full Report ──────────────────────────────────────────────
@mcp.tool()
async def generate_full_report(session_id: str) -> dict:
    """
    Generate a comprehensive portfolio report by running ALL agents:
    Market analysis, risk metrics, momentum, compliance check,
    strategy recommendations, dividend analysis.
    Use when the user asks for a complete portfolio review.
    """
    ...
```

### 13.3 MCP Resources — ce que le LLM peut LIRE

Les resources exposent les données structurées du portefeuille. Le client LLM les charge dans son contexte.

```python
# mcp_server/resources.py

@mcp.resource("portfolio://{session_id}")
async def get_portfolio(session_id: str) -> str:
    """Complete structured portfolio data as JSON."""
    ...

@mcp.resource("portfolio://{session_id}/positions")
async def get_positions(session_id: str) -> str:
    """All positions with ISIN, value, weight, P&L."""
    ...

@mcp.resource("portfolio://{session_id}/listed")
async def get_listed(session_id: str) -> str:
    """Listed positions with tickers (Finance-Guru compatible)."""
    ...

@mcp.resource("portfolio://{session_id}/allocation")
async def get_allocation(session_id: str) -> str:
    """Asset allocation breakdown."""
    ...

@mcp.resource("portfolio://{session_id}/exposure")
async def get_exposure(session_id: str) -> str:
    """Currency, regional, and sector exposure."""
    ...

@mcp.resource("portfolio://{session_id}/pnl")
async def get_pnl(session_id: str) -> str:
    """P&L overview and detailed breakdown."""
    ...

@mcp.resource("clients://list")
async def list_clients() -> str:
    """List all clients and their portfolios."""
    ...
```

### 13.4 MCP Prompts — templates de conversation pré-définis

Les prompts sont des templates que le client LLM peut proposer à l'utilisateur.

```python
# mcp_server/prompts.py

@mcp.prompt()
def portfolio_summary(session_id: str) -> str:
    """Generate a comprehensive portfolio summary with key metrics."""
    return f"""Analyse le portefeuille {session_id} et donne-moi:
    1. Valeur totale et performance
    2. Allocation par classe d'actifs
    3. Top 3 et Flop 3 performers
    4. Principaux risques identifiés
    5. Recommandation en une phrase"""

@mcp.prompt()
def risk_report(session_id: str) -> str:
    """Deep risk analysis of the portfolio."""
    return f"""Fais une analyse de risque complète du portefeuille {session_id}:
    1. Risk metrics (VaR, Sharpe, Beta) pour chaque position cotée
    2. Matrice de corrélation et diversification
    3. Stress test sur les scénarios historiques
    4. Exposition devises et concentration
    5. Recommandations pour réduire le risque"""

@mcp.prompt()
def rebalance_plan(session_id: str, target_profile: str = "moderate") -> str:
    """Generate a rebalancing plan."""
    return f"""Propose un plan de rebalancement pour le portefeuille {session_id}
    vers un profil {target_profile}:
    1. Allocation actuelle vs cible
    2. Positions à renforcer / alléger
    3. Impact estimé sur le rendement et le risque
    4. Ordres suggérés"""

@mcp.prompt()
def morning_briefing(session_id: str) -> str:
    """Daily morning briefing on portfolio positions."""
    return f"""Briefing matinal pour le portefeuille {session_id}:
    1. Mouvements overnight sur les positions cotées
    2. News impactant les positions
    3. Alertes techniques (RSI, MACD)
    4. Actions suggérées pour aujourd'hui"""
```

### 13.5 Transport & Lancement

```python
# mcp_server/server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "wealthpoint-analysis",
    description="AI-powered portfolio analysis for family offices. "
                "Upload valuation PDFs, ask questions, get risk/momentum analysis, "
                "compliance checks, and strategy recommendations.",
)

# Import et enregistre tous les tools, resources, prompts
from mcp_server.tools import *      # noqa
from mcp_server.resources import *  # noqa
from mcp_server.prompts import *    # noqa

if __name__ == "__main__":
    mcp.run()  # stdio par défaut (Claude Desktop, Claude Code)
```

```bash
# Lancement stdio (Claude Desktop, Claude Code)
python -m mcp_server.server

# Lancement Streamable HTTP (React frontend, autres clients)
python -m mcp_server.server --transport streamable-http --port 3001

# Dev avec l'inspector MCP
mcp dev mcp_server/server.py
```

### 13.6 MCP Servers externes requis

WealthPoint fonctionne en **constellation de MCP servers** — notre server est le cœur, mais il s'appuie sur 3 MCP servers externes pour le Market Researcher agent :

| MCP Server | Package | Rôle dans WealthPoint | API Key requise |
|------------|---------|-----------------|-----------------|
| **Exa** | `exa-mcp-server` | Market research, intelligence gathering, recherche web sémantique (news financières, analyses, company research) | `EXA_API_KEY` |
| **Bright Data** | `@brightdata/mcp` | Web scraping, extraction de données alternatives, données live (prix temps réel, filings SEC, rapports annuels) | `BRIGHT_DATA_API_KEY` |
| **Sequential Thinking** | `@modelcontextprotocol/server-sequential-thinking` | Raisonnement financier complexe en étapes (analyse multi-critères, scoring, workflows d'analyse séquentiels) | Aucune |

#### Config Claude Desktop (tous les serveurs)

```json
{
  "mcpServers": {
    "wealthpoint-analysis": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/wealthpoint-platform",
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "DATABASE_URL": "sqlite:///./wealthpoint.db"
      }
    },
    "exa": {
      "command": "npx",
      "args": ["-y", "exa-mcp-server", "--tools=web_search,company_search,academic_search,url_content"],
      "env": {
        "EXA_API_KEY": "your-exa-api-key"
      }
    },
    "bright-data": {
      "command": "npx",
      "args": ["@brightdata/mcp"],
      "env": {
        "API_TOKEN": "your-brightdata-token"
      }
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}
```

#### Synergie entre les serveurs

Quand un utilisateur demande une analyse complexe, le LLM client (Claude) peut combiner les tools de TOUS les serveurs en une seule réponse :

```
User: "Roche a beaucoup monté, est-ce le bon moment pour prendre des profits ?"

Claude orchestre:
  1. [wealthpoint]       analyze_risk("ROG.SW")         → VaR, Sharpe, Beta
  2. [wealthpoint]       analyze_momentum("ROG.SW")     → RSI overbought, MACD bearish divergence
  3. [exa]         web_search("Roche Q4 earnings outlook 2025")  → News financières récentes
  4. [exa]         company_search("Roche Holding")  → Données fondamentales
  5. [bright-data] scrape_as_text("https://finance.yahoo.com/quote/ROG.SW")  → Prix live
  6. [sequential]  sequentialthinking(...)          → Raisonnement structuré multi-critères
  7. [wealthpoint]       check_compliance(session_id)     → Impact sur la concentration du portefeuille
  
Claude synthétise → Réponse complète avec recommandation argumentée
```

#### Impact sur l'architecture

Ces serveurs externes sont **indépendants** de notre code — ils se configurent côté client (Claude Desktop, Cursor, etc.). Mais nos MCP tools WealthPoint doivent être conçus pour que leurs résultats se combinent bien avec les données provenant d'Exa et Bright Data.

En pratique :
- Les tools WealthPoint retournent des **données structurées** (JSON avec des clés standardisées)
- Les descriptions des tools WealthPoint mentionnent explicitement quand utiliser Exa/Bright Data en complément
- Le tool `ask_portfolio` peut suggérer au LLM de consulter Exa pour des news récentes

### 13.7 Flow complet : Prompt → Multi-MCP → Réponse

```
Utilisateur: "Analyse le risque de mon portefeuille et dis-moi si je dois rebalancer"

MCP Client (Claude Desktop / React Chat):
  │
  ├── Claude lit les resources: portfolio://{id}, portfolio://{id}/listed
  │   → Charge le contexte du portefeuille
  │
  ├── Claude décide d'appeler les tools:
  │   1. analyze_risk(session_id, "ROG.SW")     → Quant Analyst
  │   2. analyze_risk(session_id, "AAPL")       → Quant Analyst
  │   3. analyze_risk(session_id, "SPY")        → Quant Analyst
  │   4. analyze_correlation(session_id)         → Quant Analyst
  │   5. check_compliance(session_id)            → Compliance Officer
  │   6. optimize_portfolio(session_id)          → Strategy Advisor
  │
  ├── Chaque tool appelle les modules Python internes
  │   → Calculs Python (risk metrics, correlation, optimizer)
  │   → LLM si interprétation nécessaire
  │
  └── Claude synthétise tous les résultats en réponse naturelle
      avec data structurée (charts, tables, KPIs)
```

**Point clé** : c'est le **LLM client** (Claude) qui orchestre — il décide quels tools appeler en fonction du prompt. On n'a plus besoin d'un orchestrateur interne complexe. Le LLM EST l'orchestrateur. Nos "agents" deviennent des **groupes de tools MCP** spécialisés.

---

## 14. OBJECTIF FINAL — CHAT INTERFACE REACT

Le produit final est un **chat conversationnel** React qui communique avec le MCP server via Streamable HTTP. L'utilisateur discute avec WealthPoint comme avec un conseiller financier. L'interface est intelligente : elle affiche du **texte** quand la réponse est textuelle, et des **visualisations** (tableaux, graphiques, pie charts, etc.) quand la réponse contient de la data.

### 14.1 Principe : Response Types

Le tool `ask_portfolio` retourne un champ `display_type` pour indiquer au frontend **comment** afficher le résultat :

```python
class DisplayType(str, Enum):
    TEXT = "text"                # Réponse textuelle simple
    TABLE = "table"             # Tableau de données (positions, transactions, etc.)
    PIE_CHART = "pie_chart"     # Allocation, exposition (devises, régions, secteurs)
    LINE_CHART = "line_chart"   # Performance dans le temps, évolution NAV
    BAR_CHART = "bar_chart"     # Tops/Flops, comparaisons, contributions
    AREA_CHART = "area_chart"   # P&L cumulé, drawdown
    MIXED = "mixed"             # Texte + une ou plusieurs visualisations
    KPI_CARDS = "kpi_cards"     # Métriques clés (total value, perf, sharpe, etc.)
    HEATMAP = "heatmap"         # Matrice de corrélation

class ChatMessage(BaseModel):
    role: str                   # "user" | "assistant"
    content: str                # Texte de la réponse
    display_type: DisplayType   # Comment afficher
    charts: list[ChartData] = []  # Données pour les visualisations
    tables: list[TableData] = []  # Données pour les tableaux
    kpis: list[KPICard] = []     # Métriques clés

class ChartData(BaseModel):
    chart_type: str             # "pie" | "line" | "bar" | "area" | "heatmap"
    title: str
    labels: list[str]
    datasets: list[DataSet]
    options: dict = {}          # Config spécifique (couleurs, axes, etc.)

class DataSet(BaseModel):
    label: str
    data: list[float]
    color: Optional[str] = None

class TableData(BaseModel):
    title: str
    columns: list[ColumnDef]
    rows: list[dict]
    sortable: bool = True

class ColumnDef(BaseModel):
    key: str
    label: str
    type: str = "text"          # "text" | "number" | "percent" | "currency" | "date"
    align: str = "left"

class KPICard(BaseModel):
    label: str
    value: str
    change: Optional[str] = None        # "+3.37%" 
    change_type: Optional[str] = None   # "positive" | "negative" | "neutral"
    icon: Optional[str] = None          # "trending-up" | "wallet" | "shield"
```

### 14.2 Mapping Question → Visualisation

L'orchestrateur (ou le Q&A service) doit décider du `display_type` en fonction du contenu :

| Question / Réponse | display_type | Visualisation |
|---------------------|-------------|---------------|
| "Résumé du portefeuille" | `MIXED` | KPI cards (valeur, perf, nb positions) + pie chart allocation |
| "Quelle est la valeur totale ?" | `KPI_CARDS` | Card avec CHF 2'988.44 |
| "Allocation du portefeuille" | `PIE_CHART` | Pie: Cash 1.35%, Bonds 17.66%, Equities 38%... |
| "Exposition par devise" | `PIE_CHART` | Pie: CHF 35%, USD 63%, EUR 2% |
| "Exposition régionale" | `PIE_CHART` | Pie: Switzerland, Euro Zone, USA, Other |
| "Top performers" | `BAR_CHART` | Bar horizontal: Roche +20.35%, TotalEnergies +13%... |
| "Worst performers" | `BAR_CHART` | Bar horizontal (rouge): Vanguard EM -1.31%... |
| "Performance du portefeuille" | `LINE_CHART` | Line: évolution cum. perf Oct → Nov |
| "Détails Roche" | `MIXED` | KPI cards (prix, perf, poids) + texte analyse |
| "Liste des positions" | `TABLE` | Tableau: Name, ISIN, Ccy, Value, Weight%, Perf YTD |
| "Transactions" | `TABLE` | Tableau: Date, Instrument, Type, Amount, Price |
| "Obligations" | `TABLE` | Tableau: Name, Coupon, YTM, Duration, Maturity |
| "Risk metrics AAPL" | `MIXED` | KPI cards (Sharpe, Beta, VaR) + texte interprétation |
| "Momentum AAPL" | `MIXED` | KPI cards (RSI, MACD) + bar chart signal |
| "Corrélation positions" | `HEATMAP` | Heatmap matrice corrélation |
| "Optimise mon allocation" | `MIXED` | Pie chart (current vs recommended) + tableau ajustements + texte |
| "Stress test / scénarios" | `BAR_CHART` | Bar: impact par crise historique |
| "Should I add more equities?" | `TEXT` | Réponse textuelle de l'agent (avec data en support) |
| "Backtest strategy" | `LINE_CHART` | Line: portfolio vs benchmark dans le temps |

### 14.3 Tool ask_portfolio — Response Format

```
MCP Tool Call: ask_portfolio(session_id="abc123", question="Montre-moi l'allocation du portefeuille")

Response (JSON retourné par le tool): {
    "content": "Voici l'allocation de votre portefeuille au 27/11/2025 :",
    "display_type": "pie_chart",
    "charts": [{
        "chart_type": "pie",
        "title": "Allocation par classe d'actifs",
        "labels": ["Cash", "Bonds", "Equities", "Structured Products", "Others"],
        "datasets": [{
            "label": "Allocation",
            "data": [1.35, 17.66, 38.00, 6.36, 36.63]
        }]
    }],
    "tables": [],
    "kpis": [{
        "label": "Valeur totale",
        "value": "CHF 2'988.44",
        "change": "+3.37%",
        "change_type": "positive",
        "icon": "wallet"
    }]
}
```

### 14.4 Frontend React (Phase 5)

```
frontend/
├── src/
│   ├── components/
│   │   ├── Chat/
│   │   │   ├── ChatContainer.tsx       # Container principal — gère le session_id
│   │   │   ├── ChatInput.tsx           # Input message + bouton upload PDF
│   │   │   ├── ChatMessage.tsx         # Rendu conditionnel selon display_type
│   │   │   └── MessageRenderer.tsx     # Switch: text | table | chart | kpi
│   │   ├── Charts/
│   │   │   ├── PieChart.tsx            # recharts PieChart
│   │   │   ├── LineChart.tsx           # recharts LineChart
│   │   │   ├── BarChart.tsx            # recharts BarChart
│   │   │   ├── AreaChart.tsx           # recharts AreaChart
│   │   │   └── Heatmap.tsx             # Matrice corrélation
│   │   ├── DataTable/
│   │   │   └── DataTable.tsx           # Tableau sortable (positions, transactions)
│   │   ├── KPICards/
│   │   │   └── KPICard.tsx             # Card métrique (valeur + tendance)
│   │   └── Upload/
│   │       └── PDFUpload.tsx           # Drag & drop PDF → encode base64 → upload_portfolio
│   ├── hooks/
│   │   ├── useChat.ts                  # Gère messages[] + session_id + appels MCP
│   │   └── useSession.ts              # Persist session_id, auto-attach aux tool calls
│   ├── services/
│   │   └── mcp-client.ts              # Client MCP (Streamable HTTP vers port 3001)
│   └── App.tsx
├── package.json                        # React, recharts, tailwindcss, @modelcontextprotocol/sdk
└── tsconfig.json
```

**Session management côté frontend** :

```typescript
// hooks/useChat.ts (simplifié)
const useChat = () => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const uploadPDF = async (file: File) => {
    const base64 = await fileToBase64(file);
    const result = await mcpClient.callTool("upload_portfolio", {
      pdf_base64: base64,
      filename: file.name,
    });
    setSessionId(result.session_id);  // Stocké pour tous les prochains prompts
    addMessage({ role: "assistant", ...result });
  };

  const sendMessage = async (question: string) => {
    if (!sessionId) return;  // Pas de PDF uploadé → désactivé
    const result = await mcpClient.callTool("ask_portfolio", {
      session_id: sessionId,  // ← Auto-attaché
      question,
    });
    addMessage({ role: "assistant", ...result });
  };

  return { messages, sessionId, uploadPDF, sendMessage };
};
```

### 14.5 Flow utilisateur

```
┌─────────────────────────────────────────────────────────────┐
│  WealthPoint Chat                                     [📎 PDF ↑] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  👤 [glisse valuation.pdf]                                  │
│                                                             │
│  🤖 Portfolio chargé ! 13 positions, CHF 2'988.44          │
│     Session: abc123 (gardée en mémoire)                     │
│     ┌──────────┐ ┌──────────┐ ┌──────────┐                 │
│     │ 💰       │ │ 📈       │ │ 📊       │                 │
│     │ 2'988.44 │ │ +3.37%   │ │ 13 pos.  │                 │
│     │ Total    │ │ Perf YTD │ │ (4 cotées)│                 │
│     └──────────┘ └──────────┘ └──────────┘                 │
│                                                             │
│  👤 Montre-moi l'allocation      ← session_id auto-attaché │
│                                                             │
│  🤖 Voici l'allocation :                                   │
│     ┌─────────────────────┐                                 │
│     │    🥧 Pie Chart     │                                 │
│     │  Equities 38%       │                                 │
│     │  Others 36.6%       │                                 │
│     │  Bonds 17.7%        │                                 │
│     │  Struct. 6.4%       │                                 │
│     │  Cash 1.4%          │                                 │
│     └─────────────────────┘                                 │
│                                                             │
│  👤 Top performers ?             ← même session, même PDF   │
│                                                             │
│  🤖 Top 5 YTD :                                            │
│     ┌─────────────────────────────────────┐                 │
│     │ ████████████████████░ Roche  +20.4% │                 │
│     │ ████████████░░░░░░░░ Total.  +13.0% │                 │
│     │ ███████░░░░░░░░░░░░░ Apple    +7.7% │                 │
│     │ ██████░░░░░░░░░░░░░░ Gold     +7.1% │                 │
│     │ ██░░░░░░░░░░░░░░░░░░ Climb    +3.0% │                 │
│     └─────────────────────────────────────┘                 │
│                                                             │
│  👤 [glisse autre_client.pdf]    ← nouveau PDF = nouveau   │
│                                     session_id              │
│  🤖 Nouveau portfolio chargé ! 8 positions, CHF 1'245.00   │
│     Les prochaines questions porteront sur ce portefeuille. │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  💬 Posez votre question...             [📎] [Envoyer]      │
└─────────────────────────────────────────────────────────────┘
```

### 14.6 Règles de rendu frontend

1. **Toute réponse a du texte** (`content`) — le chat est toujours conversationnel
2. **Les visualisations sont additives** — elles accompagnent le texte, ne le remplacent pas
3. **Le backend décide du format** — le frontend ne fait que rendre ce qu'on lui envoie
4. **Responsive** — les charts s'adaptent à la largeur du chat
5. **Interactif** — les tableaux sont triables, les charts ont des tooltips
6. **Thème** — palette verte/dorée cohérente avec les PDFs WealthPoint (couleurs extraites du PDF sample)

---

**Commence par la Phase 1. Crée le MCP server squelette, puis le parser PDF dynamique, puis la DB SQLite, puis l'abstraction LLM. Montre-moi le code fichier par fichier.**
