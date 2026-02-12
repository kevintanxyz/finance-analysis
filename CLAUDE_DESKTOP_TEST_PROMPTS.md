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

## 🆕 Phase 4 — Agent Tools (7 nouveaux outils)

### Test 1: check_compliance — Compliance Officer

**Prompt basique** :
```
Vérifie la compliance de mon portefeuille avec les limites standard
```

**Prompt avec limites personnalisées** :
```
Vérifie la compliance de mon portefeuille avec :
- Maximum 15% par position individuelle
- Maximum 60% par classe d'actifs
- Minimum 10 positions pour la diversification
- Cash entre 5% et 20%
```

**Résultat attendu** :
- Status de compliance (compliant/non-compliant)
- Violations détaillées par sévérité (critical, high, medium, low)
- Montants CHF à ajuster pour chaque violation
- Recommandations prioritaires pour corriger les violations
- KPIs : nombre de violations, concentration max, cash allocation

---

### Test 2: analyze_dividends — Dividend Specialist

**Prompt** :
```
Analyse le potentiel de revenus de dividendes de mon portefeuille
```

**Prompt alternatif** :
```
Quelles sont mes 5 meilleures sources de revenus de dividendes ?
Combien est-ce que je vais recevoir en dividendes cette année ?
```

**Résultat attendu** :
- Portfolio dividend yield (moyenne pondérée)
- Revenu annuel projeté en CHF
- Top 5 contributeurs aux dividendes
- Concentration des dividendes (% du total)
- Positions éligibles vs positions payant des dividendes
- Recommandations pour optimiser les revenus
- KPIs : yield global, revenu annuel, nombre de positions payantes

---

### Test 3: analyze_margin — Margin Specialist

**Prompt basique** :
```
Analyse mon utilisation de marge et mes coûts d'intérêts
```

**Prompt avec taux personnalisé** :
```
Analyse ma marge avec un taux d'intérêt de 6.5%
Combien je paie en intérêts par mois ?
```

**Résultat attendu** :
- Ratio de leverage (1.0 = pas de marge, >1.0 = position à effet de levier)
- Dette de marge estimée en CHF
- Coûts d'intérêts annuels et mensuels
- Valeur nette vs valeur brute du portefeuille
- Warnings si leverage > 1.5x (risque élevé)
- Recommandations pour gestion de la marge
- KPIs : leverage ratio, coûts annuels, valeur nette

**Note** : Implémentation simplifiée basée sur la position cash. L'analyse complète nécessiterait les données broker (maintenance requirements, margin call thresholds).

---

### Test 4: generate_full_report — Full Report Generator

**Prompt** :
```
Génère un rapport complet de mon portefeuille avec toutes les analyses
```

**Prompt alternatif** :
```
Donne-moi un health check institutionnel complet de mon portfolio
```

**Résultat attendu** :
- Orchestration de 8 sections :
  1. Portfolio Allocation (par classe d'actifs)
  2. Compliance Check (violations et conformité)
  3. Market Data (prix live de toutes les positions cotées)
  4. Dividend Analysis (revenus et yield)
  5. Margin Analysis (leverage et coûts)
  6. Risk Analysis (top 3 positions par value)
  7. Momentum Analysis (top 3 positions)
  8. Correlation Matrix (toutes les positions cotées)
- Executive Summary avec KPIs clés :
  - Status de compliance
  - Dividend yield global
  - Leverage ratio
  - Diversification score
- Gestion d'erreurs : sections partielles si certaines analyses échouent

**Durée estimée** : 30-60 secondes (appels séquentiels à 8 outils)

---

### Test 5: analyze_portfolio_profile — Onboarding Specialist

**Prompt** :
```
Analyse mon profil d'investisseur à partir de mon portefeuille
Quel est mon niveau de tolérance au risque ?
```

**Prompt alternatif** :
```
Est-ce que mon allocation correspond à un profil conservateur,
modéré ou agressif ?
```

**Résultat attendu** :
- Classification de tolérance au risque (Conservative/Moderate/Aggressive)
- Risk score de 0-100 basé sur l'allocation d'actifs
- Objectifs d'investissement inférés (Income/Growth/Preservation)
- Niveau d'expérience (Beginner/Intermediate/Experienced)
- Analyse de diversification :
  - Nombre de positions
  - Nombre de classes d'actifs
  - Nombre de devises
  - Présence d'alternatives/crypto
- Questions de confirmation pour validation du profil
- Recommandations d'alignement si désalignement détecté
- KPIs : risk score, diversification level, experience level

**Adaptation** : L'agent Finance Guru original utilisait un questionnaire. L'outil MCP analyse l'allocation du portfolio PDF uploadé.

---

### Test 6: analyze_security — Market Researcher

**Prompt basique** :
```
Fais une recherche complète sur Apple (AAPL)
avec analyse fondamentale et technique
```

**Prompt fondamentale seulement** :
```
Analyse les fondamentaux de Microsoft (MSFT)
sans les indicateurs techniques
```

**Prompt technique seulement** :
```
Donne-moi l'analyse technique de NVIDIA (NVDA)
RSI, moyennes mobiles, Bollinger Bands
```

**Résultat attendu** :

**Profil de l'entreprise** :
- Nom, secteur, industrie, pays
- Description du business
- Nombre d'employés, market cap
- Site web

**Prix actuel** :
- Prix actuel et variation du jour
- Ranges : jour (low/high), 52 semaines (low/high)
- Volume vs volume moyen

**Métriques fondamentales** :
- Valorisation : P/E, P/B, PEG, Price-to-Sales
- Profitabilité : marges (profit, operating), ROE, ROA
- Croissance : revenue growth, earnings growth
- Santé financière : cash, dette, debt-to-equity, ratios de liquidité
- Dividendes : yield, payout ratio, dividend rate annuel

**Indicateurs techniques** :
- Moyennes mobiles : SMA 50, SMA 200, % vs prix actuel
- Momentum : RSI 14 (overbought/oversold/neutral)
- Volatilité : Bollinger Bands (upper/lower), Beta

**Recommandations analystes** :
- Prix cible moyen, high, low
- Consensus (buy/hold/sell)
- Nombre d'analystes
- Potentiel de hausse (% upside vs prix cible)

**Facteurs de risque** :
- High leverage (debt-to-equity > 2.0)
- Négative earnings (profit margin < 0)
- High valuation (P/E > 50)
- High volatility (Beta > 1.5)

**Use case** : Rechercher de nouvelles opportunités ou valider des positions existantes avant ajustement d'allocation.

---

### Test 7: recommend_rebalancing — Strategy Advisor

**Prompt basique** :
```
Recommande un rebalancing de mon portefeuille
vers une allocation 60% actions, 30% obligations, 10% cash
```

**Prompt avec allocation auto-inférée** :
```
Est-ce que je devrais rebalancer mon portefeuille ?
Quelle est l'allocation cible recommandée pour mon profil ?
```

**Prompt avec seuil personnalisé** :
```
Vérifie si je dois rebalancer avec un seuil de 3%
(déclencher si drift > 3% de la cible)
```

**Résultat attendu** :

**Allocation drift** :
- Target allocation (user-specified ou inferred from profile)
- Current allocation (equity, bond, cash, other)
- Drift par classe d'actifs (en %)

**Rebalancing required** :
- Boolean : true si drift > threshold (default 5%)
- Threshold utilisé pour le déclenchement

**Recommandations d'actions** :
- Asset class concernée
- Action : Buy/Sell/Increase/Deploy
- Montant en CHF à ajuster
- Priorité : High/Medium/Low (selon l'ampleur du drift)
- Current % → Target %

**Plan d'implémentation** :
1. Review Tax Implications (consulter conseiller fiscal)
2. Execute High Priority Rebalancing (focus sur drifts critiques)
3. Execute Trades (spread sur 1-2 jours, limit orders)
4. Monitor and Document (tracking des coûts, schedule next review)

**KPIs** :
- Rebalancing required (yes/no)
- Nombre de classes d'actifs à ajuster
- Montant total à rebalancer (CHF)
- Priorité max (High/Medium/Low)

**Use case** : Maintenir l'allocation cible, rebalancing tax-efficient, drift monitoring.

---

## 🎯 Workflow de Test Phase 4 — Agents Complets

### Test Rapide (5 min)
```
1. Vérifie la compliance de mon portefeuille
2. Analyse mes revenus de dividendes
3. Analyse mon profil d'investisseur
4. Recommande un rebalancing vers 60/30/10
```

### Test Complet (15 min)
```
1. Upload un portfolio PDF
2. Génère un rapport complet (generate_full_report)
3. Vérifie la compliance avec limites strictes
4. Analyse les dividendes et identifie les top contributeurs
5. Vérifie l'utilisation de marge et les coûts d'intérêts
6. Analyse mon profil d'investisseur inféré
7. Recherche en profondeur sur une position spécifique (ex: AAPL)
8. Recommande un rebalancing avec allocation cible personnalisée
```

### Test Institutionnel (30 min) — Full Portfolio Review
```
1. Upload portfolio PDF
2. Generate full report (8 sections orchestrées)
3. Pour chaque violation de compliance :
   - Recherche détaillée sur les positions concernées
   - Analyse de risque approfondie
   - Recommandation de rebalancing pour corriger
4. Pour les positions à haut dividend yield :
   - Vérifier la soutenabilité (payout ratio)
   - Analyser la croissance des dividendes
5. Analyse du profil investisseur et validation :
   - Est-ce que l'allocation reflète bien le risk score ?
   - Recommandations d'alignement
6. Plan stratégique de rebalancing avec priorités
```

---

## 📊 Tableau Récapitulatif — 16 Outils Actifs

| # | Tool | Type | Purpose | Prompt Test |
|---|------|------|---------|-------------|
| 1 | `upload_portfolio` | Core | Upload PDF | "Upload mon portfolio PDF" |
| 2 | `ask_portfolio` | Core | Q&A intelligent | "Synthétise mon portefeuille" |
| 3 | `get_market_data` | Phase 2 | Prix live | "Données marché pour toutes positions" |
| 4 | `get_portfolio_allocation` | Phase 3 | Allocation | "Quelle est mon allocation ?" |
| 5 | `analyze_risk` | Phase 2 | Risk metrics | "Analyse risque de AAPL" |
| 6 | `analyze_momentum` | Phase 2 | Momentum | "Indicateurs momentum NVDA" |
| 7 | `analyze_correlation` | Phase 2 | Correlation | "Corrélation AAPL, NVDA, SPY" |
| 8 | `price_options` | Phase 2 | Options pricing | "Prix call AAPL strike 180" |
| 9 | `optimize_portfolio` | Phase 2 | Optimization | "Optimise avec Max Sharpe" |
| 10 | `check_compliance` | Phase 4 | Compliance | "Vérifie la compliance" |
| 11 | `analyze_dividends` | Phase 4 | Dividends | "Analyse mes dividendes" |
| 12 | `analyze_margin` | Phase 4 | Margin | "Analyse mon utilisation marge" |
| 13 | `generate_full_report` | Phase 4 | Report | "Rapport complet portefeuille" |
| 14 | `analyze_portfolio_profile` | Phase 4 | Profile | "Analyse mon profil investisseur" |
| 15 | `analyze_security` | Phase 4 | Research | "Recherche AAPL complète" |
| 16 | `recommend_rebalancing` | Phase 4 | Rebalancing | "Recommande rebalancing 60/30/10" |

**Désactivés temporairement** (bugs à corriger) :
- ❌ `get_portfolio_performance` (Bug #4, #5)
- ❌ `analyze_portfolio_risk` (Bug #1, #2, #3)

---

## 🎓 Exemples Avancés Phase 4

### Combo : Compliance + Rebalancing
```
1. Vérifie la compliance avec limites strictes (max 15% par position)
2. Pour chaque violation détectée, recommande le rebalancing nécessaire
3. Calcule les montants CHF à vendre pour corriger
```

### Combo : Profile + Dividends + Strategy
```
1. Analyse mon profil investisseur
2. Si profil = "Income Generation" :
   - Analyse dividendes en détail
   - Identifie positions à faible yield
   - Recommande rebalancing vers high dividend stocks
3. Génère un plan d'optimisation des revenus
```

### Combo : Full Report + Deep Dive
```
1. Génère le rapport complet
2. Identifie les red flags (compliance violations, high concentration)
3. Pour chaque red flag :
   - Recherche détaillée sur la position (analyze_security)
   - Analyse de risque approfondie
   - Recommandation stratégique
```

### Combo : Research + Compliance + Rebalancing
```
1. Recherche fondamentale sur AAPL (analyze_security)
2. Vérifie si AAPL dépasse les limites de concentration
3. Si oui, recommande rebalancing pour réduire l'exposition
4. Suggère des alternatives dans le même secteur (diversification)
```

---

**Note finale** : Les 7 agents Phase 4 transforment le serveur MCP en plateforme d'analyse institutionnelle complète, couvrant compliance, revenus, leverage, profiling, research, et stratégie. Tous les agents Finance Guru ont été adaptés avec succès ! 🚀

