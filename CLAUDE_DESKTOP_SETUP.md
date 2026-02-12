# 🖥️ Claude Desktop Setup - WealthPoint Analysis Intelligence

Guide pour tester le serveur MCP avec Claude Desktop.

## 📋 Prérequis

1. **Claude Desktop** installé
   - Download: https://claude.ai/download
   - Version: Latest (2024+)

2. **Python Environment** configuré
   ```bash
   cd /Users/kevintan/Documents/Projects/wealthpoint-projects/finance-analysis
   uv sync  # Installer toutes les dépendances
   ```

3. **API Key Anthropic** (optionnel pour LLM features)
   - Get from: https://console.anthropic.com/

---

## 🚀 Installation

### Étape 1 : Localiser le fichier de configuration

Sur macOS, le fichier de configuration Claude Desktop est ici :
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

Si le fichier n'existe pas, créez-le.

### Étape 2 : Ajouter WealthPoint MCP Server

Copiez le contenu de `claude_desktop_config.json` dans votre configuration :

```json
{
  "mcpServers": {
    "wealthpoint-analysis": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/kevintan/Documents/Projects/wealthpoint-projects/finance-analysis",
        "run",
        "python",
        "-m",
        "mcp_server.server"
      ],
      "env": {
        "PYTHONPATH": "/Users/kevintan/Documents/Projects/wealthpoint-projects/finance-analysis"
      }
    }
  }
}
```

**⚠️ Important** : Remplacez le chemin `/Users/kevintan/...` par le chemin absolu de VOTRE projet.

### Étape 3 : Redémarrer Claude Desktop

1. Quitter complètement Claude Desktop (Cmd+Q)
2. Relancer Claude Desktop
3. Le serveur MCP devrait se connecter automatiquement

---

## 🧪 Tests à Effectuer

### 1. Vérifier la Connexion MCP

Dans Claude Desktop, demandez :
```
Quels sont les MCP tools disponibles ?
```

Vous devriez voir **8 tools** :
- ✅ upload_portfolio
- ✅ ask_portfolio
- ✅ get_market_data
- ✅ analyze_risk
- ✅ analyze_momentum
- ✅ analyze_correlation
- ✅ price_options
- ✅ optimize_portfolio

### 2. Test Risk Analysis

```
Analyze the risk for AAPL stock over the last 252 days.
```

**Expected Output** :
- VaR, CVaR, Sharpe, Sortino metrics
- KPI cards avec interprétation
- Actionnable recommendations

### 3. Test Momentum Indicators

```
Show me momentum indicators for NVDA stock.
```

**Expected Output** :
- RSI, MACD, Stochastic, Williams %R, ROC
- Confluence analysis (bullish/bearish signals)
- Trading recommendations

### 4. Test Correlation Analysis

```
Analyze correlation between AAPL, NVDA, TSLA, and SPY.
```

**Expected Output** :
- Correlation matrix
- Diversification score
- Concentration warnings

### 5. Test Options Pricing

```
Price a 30-day ATM call option on AAPL.
```

**Expected Output** :
- Black-Scholes theoretical price
- All Greeks (Delta, Gamma, Theta, Vega, Rho)
- Moneyness classification
- Trading insights

### 6. Test Portfolio Optimization (NEW! 🎉)

```
Optimize a portfolio with AAPL, NVDA, TSLA, and SPY using maximum Sharpe ratio.
```

**Expected Output** :
- Optimal allocation weights
- Expected return, volatility, Sharpe ratio
- Diversification ratio
- Implementation checklist

**Test variations** :
```
# Conservative strategy
Optimize AAPL, NVDA, TSLA, SPY using minimum variance method.

# Balanced strategy
Optimize AAPL, NVDA, TSLA, SPY using risk parity method.

# With position limits
Optimize AAPL, NVDA, TSLA, SPY with max 30% per position.

# With target return
Optimize AAPL, NVDA, TSLA using mean-variance method with 15% target return.

# With investor views
Optimize AAPL, NVDA, TSLA using Black-Litterman with views: AAPL 15%, NVDA 20%.
```

### 7. Test MCP Resources

```
Show me the portfolio resource for session abc123.
```

**Expected Resources** :
- portfolio://abc123
- portfolio://abc123/positions
- portfolio://abc123/allocation
- portfolio://abc123/exposure
- And more...

### 8. Test MCP Prompts

```
Use the portfolio-summary prompt for my portfolio.
```

**Expected Prompts** :
- portfolio-summary
- risk-report
- rebalance-plan
- morning-briefing

---

## 🐛 Troubleshooting

### Erreur : "MCP server not connecting"

**Solution 1** : Vérifier les logs
```bash
# Dans un terminal, lancer manuellement :
cd /Users/kevintan/Documents/Projects/wealthpoint-projects/finance-analysis
uv run python -m mcp_server.server
```

**Solution 2** : Vérifier que uv est dans le PATH
```bash
which uv
# Devrait afficher : /Users/kevintan/.local/bin/uv ou similaire
```

**Solution 3** : Utiliser python directement
```json
{
  "mcpServers": {
    "wealthpoint-analysis": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/Users/kevintan/Documents/Projects/wealthpoint-projects/finance-analysis",
      "env": {
        "PYTHONPATH": "/Users/kevintan/Documents/Projects/wealthpoint-projects/finance-analysis"
      }
    }
  }
}
```

### Erreur : "Module not found"

```bash
# Installer les dépendances
cd /Users/kevintan/Documents/Projects/wealthpoint-projects/finance-analysis
uv sync
```

### Erreur : "yfinance not found"

Les outils d'analyse utilisent yfinance pour les données de marché :
```bash
uv add yfinance
```

---

## ✅ Validation Checklist

Cochez quand testé :

- [ ] Server se connecte à Claude Desktop
- [ ] 8 tools détectés
- [ ] Test analyze_risk avec AAPL
- [ ] Test analyze_momentum avec NVDA
- [ ] Test analyze_correlation avec AAPL/NVDA/TSLA/SPY
- [ ] Test price_options avec call ATM
- [ ] Test optimize_portfolio max_sharpe
- [ ] Test optimize_portfolio min_variance
- [ ] Test optimize_portfolio risk_parity
- [ ] Test optimize_portfolio avec position limits
- [ ] Test MCP resources
- [ ] Test MCP prompts

---

## 📊 Expected Performance

- **Connection** : < 2 seconds
- **analyze_risk** : 3-5 seconds (fetching data)
- **analyze_momentum** : 3-5 seconds
- **analyze_correlation** : 4-6 seconds (multi-asset)
- **price_options** : 1-2 seconds
- **optimize_portfolio** : 5-10 seconds (scipy optimization)

**Note** : First request per tool is slower (no cache). Subsequent requests use 5-minute cache.

---

## 🎉 Success Criteria

Phase 3.5 est **COMPLETE** ✅ quand :

1. ✅ Server se connecte sans erreur
2. ✅ Tous les 8 tools fonctionnent
3. ✅ Real market data est récupérée
4. ✅ Caching fonctionne (2ème requête plus rapide)
5. ✅ Resources et Prompts accessibles
6. ✅ No crashes ou errors

---

## 📝 Notes

- **Cache TTL** : 5 minutes pour toutes les analyses de marché
- **Rate Limits** : yfinance gratuit a des limits, pas d'API key nécessaire
- **Data Source** : Yahoo Finance via yfinance
- **Python Version** : 3.9+ (testé avec 3.10.16)

Pour Phase 3.4 (HTTP transport), voir `HTTP_TRANSPORT_SETUP.md` (à venir).
