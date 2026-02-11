#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# Portfolio API — Example Usage
# ─────────────────────────────────────────────────────────────────────
set -e

API="http://localhost:8000/api/v1"

echo "══════════════════════════════════════════════════════"
echo "  Portfolio Analysis API — Demo"
echo "══════════════════════════════════════════════════════"

# 1. Upload PDF
echo -e "\n📤 Uploading valuation PDF..."
RESPONSE=$(curl -s -X POST "$API/upload" \
  -F "file=@sample.pdf")
echo "$RESPONSE" | python3 -m json.tool

SESSION_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")
echo "Session ID: $SESSION_ID"

# 2. Get full portfolio
echo -e "\n📊 Getting portfolio data..."
curl -s "$API/portfolio/$SESSION_ID" | python3 -m json.tool | head -50

# 3. Ask questions
echo -e "\n❓ Asking: Quelle est la valeur totale?"
curl -s -X POST "$API/ask/$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"question": "Quelle est la valeur totale du portefeuille?"}' \
  | python3 -m json.tool

echo -e "\n❓ Asking: Quels sont les top performers?"
curl -s -X POST "$API/ask/$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"question": "top performers"}' \
  | python3 -m json.tool

echo -e "\n❓ Asking: Allocation?"
curl -s -X POST "$API/ask/$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"question": "allocation du portefeuille"}' \
  | python3 -m json.tool

echo -e "\n❓ Asking: Roche?"
curl -s -X POST "$API/ask/$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"question": "détails Roche"}' \
  | python3 -m json.tool

# 4. Listed positions (Finance-Guru bridge)
echo -e "\n🏦 Listed positions (Finance-Guru compatible)..."
curl -s "$API/listed/$SESSION_ID" | python3 -m json.tool

# 5. Market data (requires internet)
echo -e "\n📈 Live market data..."
curl -s "$API/market/$SESSION_ID" | python3 -m json.tool

# 6. Risk metrics for Apple
echo -e "\n⚠️  Risk metrics for AAPL..."
curl -s "$API/risk/$SESSION_ID/AAPL?benchmark=SPY&days=90" | python3 -m json.tool

# 7. Momentum for Roche
echo -e "\n📉 Momentum for ROG.SW..."
curl -s "$API/momentum/$SESSION_ID/ROG.SW?days=90" | python3 -m json.tool

# 8. Correlation matrix
echo -e "\n🔗 Correlation between listed positions..."
curl -s "$API/correlation/$SESSION_ID?days=90" | python3 -m json.tool

echo -e "\n✅ Done!"
