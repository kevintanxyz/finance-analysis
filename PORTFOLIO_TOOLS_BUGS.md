# 🐛 Portfolio Tools — Bugs Identifiés

**Date**: 12 février 2026
**Version**: v1.1
**Status**: 🔴 Bugs documentés, fixes à implémenter

---

## 📋 Résumé Exécutif

Trois outils portfolio-level présentent des bugs de calcul significatifs :

| Outil | Bug Principal | Impact |
|-------|---------------|---------|
| `get_portfolio_performance` | Comparaison USD cost basis vs CHF current value | P&L inversés (-18% au lieu de +1%) |
| `analyze_portfolio_risk` | Beta/Sharpe/MaxDD pondérés = 0.00 | Métriques de risque inutilisables |
| `analyze_portfolio_risk` | Stress scenarios retournent CHF 0 | Scénarios de crise invalides |
| PDF Parser | Extraction bonds: CHF 0.84 au lieu de CHF 104.84 | Performance bonds à -99% |

**Impact global** : Les 3 outils retournent des données structurées correctement, mais les calculs numériques sont erronés.

---

## 🔴 Bug #1 : Beta/Sharpe/MaxDD Pondérés = 0.00

### Symptômes

```json
{
  "weighted_beta": 0.00,      // ❌ Attendu: 0.73
  "weighted_sharpe": 0.00,    // ❌ Attendu: 0.69
  "weighted_max_dd": 0.00     // ❌ Attendu: -21.9%
}
```

### Calculs Attendus

**Beta pondéré:**
```
Formule: β_portfolio = Σ (wᵢ × βᵢ) / Σ wᵢ  [normalisé sur positions cotées uniquement]

Données d'entrée (positions cotées = 38% du portfolio):
- ROG.SW:  w = 10.47%,  β = -0.013
- TTE.PA:  w =  1.77%,  β =  0.078
- AAPL:    w =  7.47%,  β =  1.263
- SPY:     w = 18.29%,  β =  1.000

Calcul correct:
β = (0.1047 × -0.013 + 0.0177 × 0.078 + 0.0747 × 1.263 + 0.1829 × 1.000)
  ÷ (0.1047 + 0.0177 + 0.0747 + 0.1829)

β = 0.27726 / 0.3800 = 0.73 ✅
```

**Sharpe pondéré:**
```
Sharpe = (0.1047 × 0.96 + 0.0177 × 0.78 + 0.0747 × 0.49 + 0.1829 × 0.60)
       ÷ 0.3800

Sharpe = 0.26066 / 0.3800 = 0.69 ✅
```

**Max Drawdown pondéré:**
```
MaxDD = (0.1047 × -21.83% + 0.0177 × -20.25% + 0.0747 × -30.22% + 0.1829 × -18.76%)
      ÷ 0.3800

MaxDD = -0.08332 / 0.3800 = -21.9% ✅
```

### Cause Racine

Le code actuel dans `analyze_portfolio_risk` divise par **total_portfolio_weight** (100%) au lieu de **listed_weight** (38%) :

```python
# ❌ Bug actuel (lines ~2550-2570)
weighted_beta = 0.0
for position in listed_positions:
    weight = position.value_chf / total_value  # Ex: 312.90 / 2988.44 = 10.47%
    risk_metrics = await analyze_risk(...)
    weighted_beta += weight * risk_metrics["beta"]  # 0.1047 × -0.013 = -0.00136

# weighted_beta final = 0.27726 (correct numerator)

# Mais ensuite, on ne divise PAS par listed_weight:
# Result: 0.27726 (non normalisé) → affiché comme 0.00 (probablement tronqué)
```

Le bug semble être que le code calcule `Σ (wᵢ × βᵢ)` mais ne normalise **pas** par la somme des poids cotés. Comme les poids individuels sont déjà en % du portfolio total (et non en % de la poche cotée), le résultat est dilué par les 62% de positions non cotées.

### Fix Suggéré

```python
# ✅ Fix (lines ~2550-2580 dans mcp_server/tools.py)

# 1. Calculer le poids total des positions cotées
listed_weight = sum(
    position.value_chf / total_value
    for position in listed_positions
)  # = 0.38 (38%)

# 2. Calculer les moyennes pondérées normalisées
weighted_beta = 0.0
weighted_sharpe = 0.0
weighted_max_dd = 0.0

for position in listed_positions:
    weight = position.value_chf / total_value  # Poids absolu
    risk_metrics = await analyze_risk(...)

    # Accumuler les produits pondérés
    weighted_beta += weight * risk_metrics.get("beta", 0.0)
    weighted_sharpe += weight * risk_metrics.get("sharpe_ratio", 0.0)
    weighted_max_dd += weight * risk_metrics.get("max_drawdown", 0.0)

# 3. Normaliser par le poids coté total
if listed_weight > 0:
    weighted_beta /= listed_weight      # 0.27726 / 0.38 = 0.73
    weighted_sharpe /= listed_weight    # 0.26066 / 0.38 = 0.69
    weighted_max_dd /= listed_weight    # -0.08332 / 0.38 = -21.9%
```

**Alternative** : Si on veut un beta "du portfolio entier", alors on peut garder le calcul actuel (0.27726 non normalisé) et documenter que c'est le beta **effectif** du portfolio incluant les 62% de cash/bonds/unlisted (qui ont beta ≈ 0).

---

## 🔴 Bug #2 : Stress Scenarios Retournent CHF 0

### Symptômes

```json
{
  "stress_scenarios": [
    {"scenario": "Market Correction (-10%)", "impact_chf": 0, "impact_pct": 0.0},  // ❌
    {"scenario": "Market Crash (-30%)",      "impact_chf": 0, "impact_pct": 0.0}   // ❌
  ]
}
```

### Calculs Attendus

**Correction -10%:**
```
Impact = Valeur_cotée × β_portfolio × choc_marché
       = CHF 1'135.56 × 0.73 × (-10%)
       = CHF -82.90 ✅

Ou si on veut l'impact sur le portfolio total:
       = CHF 2'988.44 × (0.73 × 0.38) × (-10%)
       = CHF 2'988.44 × 0.2774 × (-10%)
       = CHF -82.90
```

**Crash -30%:**
```
Impact = CHF 1'135.56 × 0.73 × (-30%)
       = CHF -248.71 ✅
```

### Cause Racine

Les stress scenarios utilisent le `weighted_beta` calculé précédemment, qui vaut 0.00 à cause du Bug #1 :

```python
# ❌ Code actuel (lines ~2650)
scenarios = [
    {
        "scenario": "Market Correction (-10%)",
        "impact_pct": -0.10 * weighted_beta * listed_weight,  # -0.10 × 0.00 × 0.38 = 0
        "impact_chf": total_value * (-0.10 * weighted_beta * listed_weight),  # = 0
    },
]
```

### Fix Suggéré

```python
# ✅ Fix: utiliser le beta normalisé correct (0.73)

# Après avoir fixé weighted_beta (Bug #1):
correction_impact_pct = -0.10 * weighted_beta * listed_weight
correction_impact_chf = total_value * correction_impact_pct

# Avec weighted_beta = 0.73, listed_weight = 0.38:
# correction_impact_pct = -0.10 × 0.73 × 0.38 = -2.77%
# correction_impact_chf = 2988.44 × -0.0277 = CHF -82.90 ✅
```

**Note** : Le calcul actuel `beta × listed_weight` est correct conceptuellement (il capture le fait que seuls 38% du portfolio sont exposés au marché actions). Le problème vient uniquement du beta = 0.00.

---

## 🔴 Bug #3 : Volatilité Portfolio (7.1% vs 6.5%)

### Symptômes

```json
{
  "portfolio_volatility": "6.5%"  // MCP
}
```

Calcul manuel attendu : **7.1%**

### Calculs Attendus

**Formule complète:**
```
σ_portfolio = √( Σᵢ Σⱼ wᵢ wⱼ σᵢ σⱼ ρᵢⱼ )
```

**Simplification (corrélations croisées faibles entre coté/non coté):**
```
σ_portfolio ≈ √( Σᵢ (wᵢ × σᵢ)² + 2 Σᵢ<ⱼ wᵢ wⱼ σᵢ σⱼ ρᵢⱼ )
```

**Données d'entrée:**

Positions cotées (38% du portfolio):
- ROG.SW:  w = 10.47%,  σ = 24.67%
- TTE.PA:  w =  1.77%,  σ = 21.04%
- AAPL:    w =  7.47%,  σ = 31.71%
- SPY:     w = 18.29%,  σ = 19.15%

Positions non cotées (62% du portfolio, volatilités estimées):
- Prima Capital:     w = 18.71%,  σ = 15.0%  (hedge fund)
- Pictet CHF Bonds:  w = 17.61%,  σ =  4.0%  (fonds oblig.)
- Pictet Gold:       w = 10.28%,  σ = 18.0%  (or physique)
- Vanguard EM:       w =  7.64%,  σ = 22.0%  (marchés émergents)
- USS DNA 9 (×2):    w =  6.33%,  σ =  8.0%  (produits structurés)
- Cash:              w =  1.35%,  σ =  0.0%
- Autres:            w =  0.09%,  σ = ~8%

**Calcul simplifié (terme diagonal uniquement):**
```python
variance = 0
for position in all_positions:
    variance += (weight * volatility) ** 2

# Terme diagonal coté:
variance += (0.1047 × 0.2467)² + (0.0177 × 0.2104)² + (0.0747 × 0.3171)² + (0.1829 × 0.1915)²
         = 0.000667 + 0.000014 + 0.000561 + 0.001226
         = 0.002468

# Terme diagonal non coté:
variance += (0.1871 × 0.15)² + (0.1761 × 0.04)² + (0.1028 × 0.18)² + (0.0764 × 0.22)²
         = 0.000788 + 0.000050 + 0.000342 + 0.000283
         = 0.001463

# Corrélations croisées significatives (AAPL-SPY, corr ≈ 0.55):
variance += 2 × 0.0747 × 0.1829 × 0.3171 × 0.1915 × 0.55
         = 0.001145

# Total:
variance_total = 0.002468 + 0.001463 + 0.001145 = 0.005076
σ_portfolio = √0.005076 = 7.1% ✅
```

### Cause Racine (Hypothèse)

Le MCP calcule probablement la volatilité avec une ou plusieurs simplifications :

1. **Ignore les positions non cotées** → sous-estime la volatilité
2. **N'estime pas de volatilité pour unlisted** → traite comme cash (σ = 0)
3. **Applique un facteur de diversification trop agressif** (0.7 au lieu de 0.85)

```python
# ❌ Code actuel probable:
portfolio_vol = weighted_vol * listed_weight * 0.7
              = 22.5% × 0.38 × 0.7
              = 6.0%  (proche de 6.5%)
```

### Fix Suggéré

```python
# ✅ Option 1: Inclure des estimations pour les positions non cotées

unlisted_vol_estimates = {
    "Prima Capital Fund": 0.15,      # Hedge fund
    "Pictet CHF Bonds": 0.04,        # Bond fund
    "Pictet Physical Gold": 0.18,    # Commodity
    "Vanguard EM": 0.22,             # Emerging markets
    "USS DNA 9": 0.08,               # Structured product
    "Cash": 0.00,
}

# Calculer la variance totale incluant unlisted:
variance = 0.0
for position in all_positions:
    if position.is_listed:
        vol = risk_metrics[position.ticker]["volatility"]
    else:
        vol = unlisted_vol_estimates.get(position.name, 0.10)  # Default 10%

    weight = position.value_chf / total_value
    variance += (weight * vol) ** 2

# Ajouter corrélations pour positions cotées (optionnel)
# ...

portfolio_vol = sqrt(variance) * diversification_factor
```

**Note** : L'écart 6.5% vs 7.1% n'est pas énorme et peut être acceptable. La vraie question est : **faut-il estimer la volatilité des unlisted ou les traiter comme du cash ?**

---

## 🔴 Bug #4 : Obligations à -99% (PDF Parsing)

### Symptômes

```json
{
  "worst_performers": [
    {
      "name": "4.85% Nestle Holdings Inc 2033/03/14",
      "unrealized_pnl_chf": -103.16,
      "pnl_pct": -99.19
    },
    {
      "name": "4.125% United States of America 2044/08/15",
      "unrealized_pnl_chf": -95.24,
      "pnl_pct": -99.21
    }
  ]
}
```

### Données Extraites (Erreur)

| Position | Cost Basis | Current Value | P&L | Problème |
|----------|------------|---------------|-----|----------|
| Nestle Bond | CHF 104.00 | **CHF 0.84** | -99.19% | ❌ Valeur = accrued interest au lieu de market value |
| US Treasury | CHF 96.00 | **CHF 0.76** | -99.21% | ❌ Idem |

### Valeurs Attendues (Données PDF Réelles)

```
Nestle Holdings 4.85% 2033/03/14:
- Nominal:           USD 100
- Prix (quote):      103.27%  (prix de marché en % du nominal)
- Valeur propre:     USD 103.27  (= 100 × 103.27%)
- Intérêts courus:   USD 0.84
- Valeur totale:     USD 104.11  (= 103.27 + 0.84)
- Taux de change:    0.8042 USD/CHF
- Valeur CHF:        CHF 83.73  (= 104.11 × 0.8042)

Cost basis:          CHF 104.00
P&L réel:            CHF 83.73 - 104.00 = -CHF 20.27 (-19.5%) ✅
```

### Cause Racine

Le parser PDF extrait **accrued_interest** (CHF 0.84) au lieu de **total_value** (CHF 83.73).

**Où ça se passe :**

1. **`app/parsers/llm_extractor.py`** (Claude Vision) :
   ```python
   # Ligne ~317
   value_chf=pos_dict.get("value") or pos_dict.get("value_chf", 0.0),
   ```

   Le JSON retourné par Claude Vision contient probablement :
   ```json
   {
     "name": "4.85% Nestle Holdings",
     "value": 0.84,  // ❌ C'est l'accrued interest, pas la market value!
     "accrued_interest": 0.84
   }
   ```

2. **Prompt d'extraction** (`EXTRACTION_SYSTEM_PROMPT`) :
   ```python
   # Ligne ~24-86 dans llm_extractor.py
   **Critical Rules:**
   ...
   3. **value**: Position value in reference_currency (NOT always CHF!)
   ```

   Le prompt ne spécifie **pas explicitement** pour les obligations :
   - "Pour les bonds, extraire la valeur totale (clean value + accrued interest), PAS juste les intérêts courus"

### Fix Suggéré

**Option A : Améliorer le prompt Claude Vision**

```python
# Ajouter dans EXTRACTION_SYSTEM_PROMPT (ligne ~70-80):

**CRITICAL — Bonds Extraction:**
10. For bonds, extract the TOTAL market value, not just accrued interest:
    - Bonds typically show: Clean Value + Accrued Interest = Total Value
    - Extract "Total Value" (e.g., CHF 104.11), NOT "Accrued Interest" (e.g., CHF 0.84)
    - If only "Clean Value" and "Accrued Interest" are shown, SUM them for "value"
    - Pattern to look for: "Valeur totale", "Total Value", "Market Value (incl. accrued)"
```

**Option B : Post-processing après extraction**

```python
# Dans _dict_to_portfolio_data (ligne ~290-340):

for pos_dict in data.get("positions", []):
    asset_class_str = pos_dict.get("asset_class", "other").lower()

    # Fix bond values si aberrantes
    if asset_class_str in ["bond", "bonds"]:
        value = pos_dict.get("value", 0.0)
        accrued = pos_dict.get("accrued_interest", 0.0)
        cost = pos_dict.get("purchase_price", 0.0)

        # Détection d'erreur: si value < 5% du cost, c'est probablement accrued interest
        if cost > 0 and value < (cost * 0.05):
            logger.warning(
                f"Bond '{pos_dict['name']}' has suspicious value {value} vs cost {cost}. "
                f"This may be accrued interest instead of total value. "
                f"Recommend re-extraction or manual verification."
            )
            # Option: essayer d'inférer total value = clean value + accrued
            # Mais on n'a pas clean value ici...
```

**Option C : Validation lors de l'upload**

```python
# Dans upload_portfolio (ligne ~200-250 dans tools.py):

# Après extract_positions_with_validation:
for position in validated_positions:
    if position.asset_class == AssetClass.BONDS:
        if position.cost_price and position.value_chf:
            pnl_pct = (position.value_chf - position.cost_price) / position.cost_price * 100

            # Flag si P&L < -80% (improbable pour une obligation)
            if pnl_pct < -80:
                validation_summary["warnings"].append(
                    f"Bond '{position.name}' shows extreme loss ({pnl_pct:.1f}%). "
                    f"Current value {position.value_chf} may be accrued interest instead of market value. "
                    f"Please verify extraction."
                )
```

---

## 🔴 Bug #5 : P&L Inversés (Devise Cost Basis vs CHF Current Value)

### Symptômes

```json
// ask_portfolio (LLM halluciné):
{
  "AAPL": {"cost": "USD 260", "current": "USD 277.55", "pnl": "+6.75%"},
  "SPY": {"cost": "USD 670", "current": "USD 679.68", "pnl": "+1.45%"}
}

// get_portfolio_performance (structuré):
{
  "AAPL": {"cost": 260.00, "current": 223.21, "pnl": "-14.15%"},  // ❌
  "SPY": {"cost": 670.00, "current": 546.60, "pnl": "-18.42%"}    // ❌
}
```

### Comparaison Détaillée

| Position | ask_portfolio (USD) | get_portfolio_performance (CHF) | Écart |
|----------|---------------------|----------------------------------|-------|
| **SPY** | | | |
| Cost basis | USD 670.00 | CHF 670.00 | ⚠️ Même nombre, devise différente |
| Valeur actuelle | USD 679.68 | CHF 546.60 | ❌ 679.68 USD ≠ 546.60 CHF |
| P&L | +1.45% 📈 | -18.42% 📉 | **P&L inversé** |
| | | | |
| **AAPL** | | | |
| Cost basis | USD 260.00 | CHF 260.00 | ⚠️ Même nombre |
| Valeur actuelle | USD 277.55 | CHF 223.21 | ❌ Devises différentes |
| P&L | +6.75% 📈 | -14.15% 📉 | **P&L inversé** |
| | | | |
| **Prima Capital** | | | |
| Cost basis | USD 708.49 | CHF 708.49 | ⚠️ Même nombre |
| Valeur actuelle | USD 695.22 | CHF 559.10 | ❌ Devises différentes |
| P&L | -1.87% | -21.09% | **Écart amplifié** |

### Analyse des Scénarios

**Scénario A : Cost basis en USD dans le PDF**

Si le PDF contient :
```
SPY : Coût USD 670.00 → Valeur actuelle USD 679.68 (prix marché)
      Converti en CHF au taux 0.8042 → CHF 546.60
```

Alors le vrai P&L en CHF devrait être :
```
Cost basis CHF = 670 × (taux historique à l'achat)  // Ex: 0.88 → CHF 589.60
P&L = 546.60 - 589.60 = -CHF 43.00 (-7.3%)
```

Le code actuel fait :
```python
# ❌ Bug:
cost_basis = position.cost_price * quantity  # 670 × 1 = 670 CHF (FAUX, c'est USD!)
unrealized_pnl = position.value_chf - cost_basis  # 546.60 - 670 = -123.40 CHF
pnl_pct = unrealized_pnl / cost_basis * 100  # -18.42%
```

**Scénario B : Cost basis déjà en CHF dans le PDF**

Si le PDF contient déjà la conversion :
```
SPY : Coût CHF 670.00 (investi lors d'un taux USD/CHF favorable)
      Valeur actuelle CHF 546.60
```

Alors le calcul actuel est **correct** : -18.42% de perte réelle due à la baisse de l'USD.

### Cause Racine

Il faut vérifier dans le **modèle `Position`** s'il y a :
1. Un champ `cost_price_currency` qui stocke la devise du cost price
2. Un taux de change historique pour convertir

**Vérification dans la base SQLite :**

```sql
SELECT
    name,
    currency,           -- Devise de la position (USD, CHF, EUR)
    cost_price,         -- Prix d'achat (260, 670, etc.)
    value_chf,          -- Valeur actuelle en CHF
    fx_rate             -- Taux de change actuel
FROM positions
WHERE session_id = 'xxx'
AND name LIKE '%SPY%';
```

Si `cost_price` est stocké **sans devise associée**, alors on ne peut pas savoir s'il est en USD ou en CHF.

### Fix Suggéré

**Option 1 : Stocker la devise du cost basis**

Modifier le modèle `Position` :

```python
# app/models/portfolio.py

class Position(SQLModel, table=True):
    ...
    cost_price: Optional[float] = None
    cost_price_currency: Optional[str] = None  # 🆕 Ajouter ce champ
    fx_rate: Optional[float] = None
    fx_rate_at_purchase: Optional[float] = None  # 🆕 Taux de change à l'achat
```

Puis dans `get_portfolio_performance` :

```python
# Calculer cost basis en CHF
if position.cost_price_currency and position.cost_price_currency != "CHF":
    # Convertir le cost en CHF avec le taux historique
    if position.fx_rate_at_purchase:
        cost_basis_chf = position.cost_price * position.fx_rate_at_purchase
    else:
        # Fallback: utiliser le taux actuel (approximation)
        cost_basis_chf = position.cost_price * (position.fx_rate or 1.0)
else:
    cost_basis_chf = position.cost_price

unrealized_pnl = position.value_chf - cost_basis_chf
```

**Option 2 : Documenter l'ambiguïté**

Si on ne peut pas récupérer la devise du cost basis depuis le PDF, documenter que :

> **Important** : Le cost basis est comparé directement à la valeur CHF actuelle. Si le cost basis était en devise étrangère (USD, EUR), le P&L calculé inclut l'effet de change. Pour un P&L en devise locale, utiliser `analyze_risk` sur le ticker individuel.

---

## 🧪 Tests de Validation

Pour chaque bug, voici comment vérifier le fix :

### Bug #1 : Beta/Sharpe/MaxDD

**Test :**
```python
result = await analyze_portfolio_risk(session_id="xxx", days=90)

assert result["weighted_beta"] > 0.5  # Au moins 0.5 (portfolio avec SPY/AAPL)
assert result["weighted_sharpe"] > 0.5  # Au moins 0.5
assert result["weighted_max_dd"] < -15  # Au moins -15%
```

### Bug #2 : Stress Scenarios

**Test :**
```python
result = await analyze_portfolio_risk(session_id="xxx")

correction_scenario = next(s for s in result["stress_scenarios"] if "Correction" in s["scenario"])
assert abs(correction_scenario["impact_chf"]) > 50  # Au moins CHF 50 d'impact
assert correction_scenario["impact_pct"] < -2.0  # Au moins -2%
```

### Bug #3 : Volatilité

**Test :**
```python
result = await analyze_portfolio_risk(session_id="xxx")

assert result["portfolio_volatility_pct"] > 5.0  # Au moins 5%
assert result["portfolio_volatility_pct"] < 15.0  # Moins de 15% (diversifié)
```

### Bug #4 : Obligations

**Test :**
```python
result = await get_portfolio_performance(session_id="xxx")

# Trouver les obligations
bonds = [p for p in result["performance_list"] if "Nestle" in p["name"] or "Treasury" in p["name"]]

for bond in bonds:
    # Les obligations ne devraient jamais perdre 99%
    assert bond["pnl_pct"] > -50  # Max -50% de perte (très conservateur)
    assert bond["unrealized_pnl_chf"] > -500  # Max CHF 500 de perte
```

### Bug #5 : P&L Devise

**Test manuel :**
```
1. Uploader un PDF de test avec des positions en USD
2. Vérifier dans la base SQLite:
   - Quelle devise est stockée pour cost_price ?
   - Y a-t-il un champ cost_price_currency ?
3. Comparer le P&L calculé avec le P&L attendu
```

---

## 📊 Priorités de Fix

| Bug | Sévérité | Effort | Priorité | Raison |
|-----|----------|--------|----------|---------|
| #4 Obligations -99% | 🔴 **CRITIQUE** | 🟢 Faible | **P0** | Rend les données inutilisables, fausse toutes les analyses |
| #1 Beta/Sharpe = 0 | 🔴 **HAUTE** | 🟡 Moyen | **P1** | Bloque les stress scenarios (Bug #2) |
| #2 Stress = 0 | 🔴 **HAUTE** | 🟢 Faible | **P1** | Dépend du fix de Bug #1 |
| #5 P&L Devise | 🟡 **MOYENNE** | 🔴 Élevé | **P2** | Nécessite changement de schéma DB + reparsing |
| #3 Volatilité | 🟢 **BASSE** | 🟡 Moyen | **P3** | Écart acceptable (6.5% vs 7.1%), peut vivre avec |

---

## 📝 Conclusion

Les 3 outils portfolio-level sont **structurellement corrects** (retournent JSON valide, KPIs bien formatés, tables bien organisées) mais contiennent **5 bugs numériques** qui rendent certaines métriques inutilisables.

**Fixes recommandés :**
1. ✅ **P0** : Améliorer le prompt Claude Vision pour les obligations (1 ligne de code)
2. ✅ **P1** : Normaliser beta/sharpe/maxdd par `listed_weight` (5 lignes de code)
3. ✅ **P2** : Ajouter `cost_price_currency` au schéma (changement de DB)
4. 🤔 **P3** : Décider si on veut estimer les volatilités unlisted ou non (décision produit)

**Décision produit importante :** Pour le Bug #5 (P&L devise), il faut décider :
- **Option A** : Considérer que le cost basis est toujours en CHF (simplifie, mais peut être faux)
- **Option B** : Ajouter la devise du cost basis au schéma (plus précis, mais nécessite reparsing de tous les PDFs)

---

**Status** : 🔴 Bugs documentés, à fixer

**Next Steps** :
1. Valider les hypothèses de cause racine avec le code réel
2. Implémenter les fixes P0 et P1 (bugs critiques)
3. Décider de l'approche pour Bug #5 (devise cost basis)
