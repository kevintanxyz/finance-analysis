# Guide de Test - Claude Vision PDF Extraction

**Date**: February 11, 2026

---

## ✅ Prérequis

```bash
✅ Python 3.10 + uv
✅ ANTHROPIC_API_KEY configuré dans .env
✅ Tous les composants testés (uv run python test_components.py)
```

---

## 🧪 Test 1: Vérifier les Composants (sans PDF)

```bash
uv run python test_components.py
```

**Résultat attendu**:
```
✅ Bank detection system: OK
✅ LLM provider: OK (ClaudeProvider)
✅ PDF router: OK
✅ ISIN mapping: OK
🎯 All components ready!
```

---

## 🖼️ Test 2: Extraction avec un PDF Réel

### Obtenir un PDF de test

Vous avez besoin d'un relevé de portefeuille (n'importe quel format):
- **WealthPoint/Rothschild** ✅
- **UBS** ✅
- **Julius Baer** ✅
- **Credit Suisse** ✅
- **Autre banque** ✅ (fallback générique)

### Lancer l'extraction

```bash
# Avec votre PDF
uv run python test_pdf_extraction.py ~/path/to/portfolio.pdf

# Exemples
uv run python test_pdf_extraction.py ~/Downloads/valuation_nov_2025.pdf
uv run python test_pdf_extraction.py tests/fixtures/sample_valuation.pdf
```

### Résultat attendu

```
🖼️  Testing Claude Vision PDF Extraction
============================================================

📄 PDF: valuation_nov_2025.pdf
📦 Size: 245.3 KB

🤖 Initializing Claude Vision provider...
   ✅ Provider: ClaudeProvider

🖼️  Extracting with Claude Vision router...
   (This will take 6-8 seconds...)

📄 Step 1: Extracting with Claude Vision router...

🖼️  Converting PDF pages to images...
   → 3 pages converted
🤖 Sending to Claude Vision for extraction...
   → Received structured data from LLM
✅ Extracted 15 positions

============================================================
✅ Extraction Complete!
============================================================

🏦 Bank Detected: ubs
📋 Strategy Used: llm_vision
🎯 Confidence: 92.00%
📊 Positions: 15
💰 Total Value: CHF 1'250'000.00

📋 First 5 Positions:
------------------------------------------------------------
1. UBS (Lux) Bond SICAV USD High Yield
   ISIN: LU0136412771
   Value: CHF 125'000.00 (10.00%)
   Asset Class: bonds

2. Apple Inc.
   ISIN: US0378331005
   Value: CHF 95'000.00 (7.60%)
   Asset Class: equities

[...]
```

---

## 🌍 Support Multi-Devise

**Important**: Le système extrait la **devise du statement** automatiquement.

### Exemple: Portfolio USD

```json
{
  "reference_currency": "USD",  // Extrait du document
  "total_value": 1500000.00,    // En USD
  "positions": [
    {
      "name": "Apple Inc.",
      "currency": "USD",          // Devise de la position
      "value": 150000.00,         // Valeur en reference_currency (USD)
      "weight_pct": 10.0
    }
  ]
}
```

### Exemple: Portfolio Multi-Devise (CHF)

```json
{
  "reference_currency": "CHF",  // Portfolio en CHF
  "total_value": 1000000.00,
  "positions": [
    {
      "name": "Apple Inc.",
      "currency": "USD",          // Position en USD
      "value": 50000.00,          // Converti en CHF
      "weight_pct": 5.0
    },
    {
      "name": "TotalEnergies",
      "currency": "EUR",          // Position en EUR
      "value": 30000.00,          // Converti en CHF
      "weight_pct": 3.0
    }
  ],
  "currency_exposure": [
    {"currency": "CHF", "pct": 40.0, "value": 400000.00},
    {"currency": "USD", "pct": 35.0, "value": 350000.00},
    {"currency": "EUR", "pct": 25.0, "value": 250000.00}
  ]
}
```

**Claude Vision extrait automatiquement**:
1. ✅ La devise de référence du portfolio (CHF, USD, EUR, etc.)
2. ✅ La devise de chaque position
3. ✅ Les valeurs converties dans la devise de référence
4. ✅ L'exposition par devise

---

## 📊 Test 3: Vérifier les Résultats

### Validation automatique

Le système valide automatiquement:
- ✅ Somme des positions ≈ total portfolio (±1%)
- ✅ Poids des positions ≈ 100%
- ✅ Format ISIN (12 caractères)
- ✅ Valeurs positives
- ✅ Devises valides

### Exemple de warnings

```
⚠️  Warnings:
   - Total value mismatch: calculated 1,245,000 vs reported 1,250,000 (0.4% diff)
   - Position weights sum to 98.5% (should be ~100%)
   - High concentration: Apple Inc. (25.0%)
```

---

## 🔍 Test 4: Banques Spécifiques

### UBS

```bash
uv run python test_pdf_extraction.py ubs_statement.pdf
```

**Attendu**:
- Bank: `ubs`
- Strategy: `llm_vision`
- Extra handling: Multi-page positions

### Julius Baer (Allemand)

```bash
uv run python test_pdf_extraction.py julius_baer_statement.pdf
```

**Attendu**:
- Bank: `julius_baer`
- Strategy: `llm_vision`
- Headers allemands: Bezeichnung, Valor, Kurs, Bewertung

### Format Inconnu

```bash
uv run python test_pdf_extraction.py other_bank.pdf
```

**Attendu**:
- Bank: `generic`
- Strategy: `llm_vision`
- Fonctionne quand même ! ✅

---

## 🐛 Troubleshooting

### Erreur: "LLM returned invalid JSON"

**Cause**: Claude Vision a retourné du texte au lieu de JSON

**Solution**:
1. Vérifier que le PDF contient bien des données financières
2. Essayer avec un PDF plus simple (moins de pages)
3. Check les logs pour voir ce que Claude a retourné

### Erreur: "No positions extracted"

**Cause**: Claude Vision n'a pas trouvé de tableau de positions

**Solutions**:
1. Vérifier que le PDF contient un tableau de positions
2. Essayer d'uploader seulement la page avec les positions
3. Regarder le prompt d'extraction (peut nécessiter ajustement)

### Warning: "Value sum mismatch"

**Cause**: La somme des positions ne correspond pas au total

**Solutions**:
- C'est souvent normal (cash non comptabilisé, arrondis)
- Si l'écart est > 5%, vérifier l'extraction
- Activer LLM validation: `enable_llm_validation=True`

### PDF Scannés (OCR)

Pour les PDFs de mauvaise qualité:

```python
# Dans test_pdf_extraction.py, ligne 45:
positions, summary = await parse_portfolio_pdf(
    pdf_path,
    ISIN_TICKER_MAP,
    total_value_chf=0.0,
    llm=llm,
    enable_llm_validation=True,  # ← Active la correction OCR
    verbose=True
)
```

---

## 📈 Performance Attendue

| Métrique | Valeur |
|----------|--------|
| **Temps** | 6-8 secondes (3 pages) |
| **Coût** | ~$0.05 par PDF |
| **Accuracy** | ~95% (validation auto) |
| **Formats supportés** | Tous ✅ |

---

## 🎯 Next Steps

Une fois le test réussi:

1. **Intégrer dans MCP**:
   - Le tool `upload_portfolio` utilise déjà Claude Vision
   - Configure Claude Desktop (voir START_SERVER.md)
   - Test end-to-end avec Claude Desktop

2. **Tester plusieurs formats**:
   - WealthPoint, UBS, Julius Baer, etc.
   - Vérifier la détection automatique

3. **Phase 2**: Implémenter les analysis tools
   - Risk metrics, momentum, correlation
   - Voir NEXT_STEPS.md

---

**Documentation complète**: [docs/CLAUDE_VISION.md](docs/CLAUDE_VISION.md)
