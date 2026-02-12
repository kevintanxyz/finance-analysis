# Claude Desktop — Test Prompts pour WealthPoint MCP Server

Voici une série de prompts pour tester chaque outil MCP du serveur WealthPoint.

---

## 🚀 Étape 1 : Vérifier que les outils sont chargés

```
Liste tous les outils MCP disponibles
```

**Résultat attendu** : Tu devrais voir 11 outils :
- upload_portfolio
- ask_portfolio
- get_market_data
- analyze_risk
- analyze_momentum
- analyze_correlation
- price_options
- optimize_portfolio
- get_portfolio_allocation ⭐ NEW
- get_portfolio_performance ⭐ NEW
- analyze_portfolio_risk ⭐ NEW

---

## 📄 Étape 2 : Upload d'un portfolio

**⚠️ IMPORTANT** : Pour les **PDFs volumineux** (>500KB), utilise le **chemin de fichier** au lieu du base64 pour éviter de dépasser les limites de contexte.

### Option A : Upload via chemin de fichier (Recommandé)
```
Upload mon portfolio PDF en utilisant le chemin de fichier :
/Users/kevintan/Documents/portfolios/valuation_nov2025.pdf
```

**Pourquoi c'est mieux** : Pas de limite de taille, plus rapide, pas d'encodage base64

### Option B : Upload via glisser-déposer (Petits PDFs uniquement)
```
[Glisse ton PDF de valorisation dans le chat]

Parse ce PDF et analyse le portefeuille
```

**Note** : Claude Desktop va encoder le PDF en base64. Si le PDF est trop gros (>500KB), le prompt peut dépasser la limite. Dans ce cas, utilise l'option A.

### Option C : Test sans PDF (portfolio mock)
```
Créé un portfolio de test avec 3 positions cotées (AAPL, NVDA, SPY)
et sauvegarde-le avec upload_portfolio en utilisant des données mock.
```

---

## 📊 Étape 3 : Test get_market_data

Une fois que tu as un `session_id` (retourné par l'upload) :

```
Récupère les données de marché en temps réel pour toutes
les positions cotées du portefeuille
```

**Ce que tu vas obtenir** :
- KPI cards : valeur totale des positions listées, changement du jour, nombre de positions
- Tableau avec : ticker, nom, prix actuel, variations 1D/5D/1M, P/E, dividend yield, beta
- Insights automatiques : top gainers/losers, warnings sur P/E élevés

---

## 📈 Étape 4 : Test analyze_risk

```
Analyse le risque de Apple (AAPL) sur les 90 derniers jours
avec SPY comme benchmark
```

**Métriques attendues** :
- VaR (Value at Risk)
- Sharpe Ratio
- Sortino Ratio
- Beta
- Alpha
- Max Drawdown
- Volatility

---

## 🎯 Étape 5 : Test analyze_momentum

```
Analyse les indicateurs momentum pour NVDA sur 90 jours
```

**Indicateurs attendus** :
- RSI (14)
- MACD + Signal + Histogram
- Stochastic %K et %D
- Williams %R
- ROC
- Confluence score (bullish/bearish/neutral)

---

## 🔗 Étape 6 : Test analyze_correlation

```
Calcule la matrice de corrélation entre AAPL, NVDA, et SPY
sur les 90 derniers jours
```

**Résultat attendu** :
- Matrice de corrélation (3x3)
- Score de diversification
- Insights sur les paires (hedge detection, concentration risk)
- Graphique heatmap (si supporté par le frontend)

---

## 📉 Étape 7 : Test price_options

```
Calcule le prix d'une option call sur Apple avec :
- Strike : 180$
- Expiration : 30 jours
- Utilise la volatilité historique automatique
```

**Résultat attendu** :
- Prix de l'option (Black-Scholes)
- Delta, Gamma, Theta, Vega, Rho
- Moneyness (ITM/ATM/OTM)
- Valeur intrinsèque vs temps
- Interprétation pour covered call ou protective put

---

## 🎲 Étape 8 : Test optimize_portfolio

```
Optimise l'allocation du portefeuille avec la méthode
Max Sharpe sur AAPL, NVDA, et SPY (252 jours d'historique)
```

**Résultat attendu** :
- Poids actuels vs recommandés
- Sharpe ratio actuel vs optimisé
- Volatilité attendue
- Rendement attendu
- Liste des ajustements à faire

---

## 🔄 Étape 9 : Test ask_portfolio (Q&A intelligent)

Une fois que tu as uploadé un portfolio :

```
Quelle est l'allocation de mon portefeuille ?
```

```
Quelles sont les 3 meilleures performances ?
```

```
Analyse le risque global du portefeuille
```

```
Devrais-je rebalancer vers plus d'obligations ?
```

**Ce que fait ask_portfolio** :
- Comprend la question en langage naturel (FR/EN)
- Route vers le bon outil d'analyse
- Retourne une réponse avec le bon `display_type` (table, chart, KPI cards, etc.)

---

## 🎯 Workflow Complet de Test

### Test Rapide (5 min)
```
1. Liste les outils disponibles
2. Récupère les données marché pour AAPL
3. Analyse le risque de NVDA
4. Calcule la corrélation entre AAPL, NVDA, SPY
```

### Test Complet (15 min)
```
1. Upload un PDF de valorisation (ou créé un mock)
2. get_market_data pour toutes les positions
3. analyze_risk sur chaque position cotée
4. analyze_momentum sur la position la plus volatile
5. analyze_correlation pour tout le portefeuille coté
6. price_options sur une position (si applicable)
7. optimize_portfolio avec méthode Max Sharpe
8. ask_portfolio : "Synthétise l'état de mon portefeuille"
```

---

## ⚙️ Configuration Claude Desktop

Vérifie que ton `claude_desktop_config.json` contient :

```json
{
  "mcpServers": {
    "wealthpoint-analysis": {
      "command": "uv",
      "args": ["run", "python", "-m", "mcp_server.server"],
      "cwd": "/Users/kevintan/Documents/Projects/wealthpoint-projects/finance-analysis",
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "DATABASE_URL": "sqlite:///./wealthpoint.db"
      }
    }
  }
}
```

---

## 🐛 Debugging

Si un outil ne fonctionne pas :

1. **Vérifie les logs** :
```bash
tail -f ~/Library/Logs/Claude/mcp-server-wealthpoint-analysis.log
```

2. **Test en ligne de commande** :
```bash
uv run python -m mcp_server.server
# Le serveur devrait afficher : "Registered: 8 tools, 1 resources, 6 prompts"
```

3. **Test d'un outil spécifique** :
```bash
uv run python -c "
from mcp_server.tools import get_market_data
import asyncio
result = asyncio.run(get_market_data('test-session'))
print(result)
"
```

---

## 📊 Résultats Attendus

### ✅ Succès
- Chaque outil retourne un dict avec `content`, `display_type`
- `get_market_data` : `display_type="mixed"`, KPIs + table
- `analyze_risk` : `display_type="mixed"`, KPIs + interpretation
- `analyze_correlation` : `display_type="heatmap"` + pairwise insights
- `optimize_portfolio` : `display_type="mixed"`, current vs recommended weights

### ❌ Erreurs Communes
- **"Portfolio not found"** : Le session_id n'existe pas, upload un portfolio d'abord
- **"No listed positions"** : Le portfolio n'a que des positions non-cotées
- **"Ticker required"** : Tu n'as pas fourni le ticker pour analyze_risk/momentum
- **yfinance timeout** : Marchés fermés ou ticker invalide

---

## 🎓 Exemples Avancés

### Combo : Market Data + Risk Analysis
```
1. Récupère les données marché pour toutes les positions
2. Pour chaque position avec un P/E > 30, fais une analyse de risque détaillée
3. Synthétise les positions à surveiller
```

### Combo : Momentum + Correlation
```
1. Identifie les positions avec RSI > 70 (surachetées)
2. Calcule leur corrélation avec SPY
3. Recommande si je devrais prendre des profits
```

### Full Portfolio Review
```
Génère un rapport complet de mon portefeuille incluant :
- Données marché live
- Risque par position
- Matrice de corrélation
- Recommandations d'optimisation
```

---

**Note** : Ces prompts sont conçus pour Claude Desktop avec le serveur MCP WealthPoint.
Les résultats varient selon les données du marché et l'état du portfolio uploadé.

---

## 🆕 Nouveaux Outils Portfolio-Level (v1.1)

### Test get_portfolio_allocation

```
Quelle est l'allocation de mon portefeuille par classe d'actifs?
```

**Résultat attendu** :
- KPIs: Valeur totale, nombre de classes d'actifs, nombre de positions
- Tableau d'allocation : Equities X%, Bonds Y%, Cash Z%, etc.
- Graphique pie chart (si supporté par le frontend)

### Test get_portfolio_performance

```
Quelles sont les 3 meilleures performances de mon portefeuille?
```

**Résultat attendu** :
- KPIs: P&L total non réalisé, nombre de positions avec données, cost basis total
- Top 3 performers : position, gain CHF, gain %
- Worst 3 performers : position, perte CHF, perte %
- Tableau complet de toutes les positions classées par performance

### Test analyze_portfolio_risk

```
Analyse le risque global de mon portefeuille
```

**Résultat attendu** :
- KPIs: Volatilité portefeuille, VaR 95%, Beta pondéré, Concentration top 3
- Métriques de risque agrégées pour toutes les positions
- Tableau de concentration (top 10 positions)
- Scénarios de stress (normal day, VaR, correction -10%, crash -30%, max drawdown)
- Facteurs de risque identifiés (concentration, liquidité, volatilité, etc.)
- Poids listed vs unlisted positions

---

