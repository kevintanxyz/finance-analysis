"""
Test client for the Portfolio Analysis API.

Usage:
    python scripts/test_client.py path/to/valuation.pdf
"""
import sys

import httpx

API = "http://localhost:8000/api/v1"


def main(pdf_path: str):
    client = httpx.Client(timeout=30)

    # 1. Upload
    print("📤 Uploading PDF...")
    with open(pdf_path, "rb") as f:
        resp = client.post(f"{API}/upload", files={"file": (pdf_path, f, "application/pdf")})
    resp.raise_for_status()
    upload = resp.json()
    sid = upload["session_id"]
    print(f"  ✅ Session: {sid}")
    print(f"  💰 Total: CHF {upload['total_value_chf']:,.2f}")
    print(f"  📋 Positions: {upload['positions_count']} (listed: {upload['listed_count']})")
    print(f"  🏷  Tickers: {upload['listed_tickers']}")

    # 2. Questions
    questions = [
        "résumé du portefeuille",
        "allocation",
        "top performers",
        "exposition devises",
        "exposition régionale",
        "détails Roche",
        "obligations",
        "risque stress test",
        "positions cotées",
    ]

    for q in questions:
        print(f"\n❓ {q}")
        resp = client.post(f"{API}/ask/{sid}", json={"question": q})
        data = resp.json()
        print(f"  → {data['answer'][:200]}...")

    # 3. Market data for listed
    print("\n📈 Market data for listed positions:")
    resp = client.get(f"{API}/listed/{sid}")
    listed = resp.json()
    for pos in listed.get("positions", []):
        print(f"  {pos['ticker']:10s} {pos['name']:30s} CHF {pos['value_chf']:>10,.2f}")

    # 4. Risk metrics
    for ticker in upload.get("listed_tickers", []):
        print(f"\n⚠️  Risk metrics: {ticker}")
        resp = client.get(f"{API}/risk/{sid}/{ticker}")
        risk = resp.json()
        if "error" not in risk:
            print(f"  Sharpe: {risk.get('sharpe_ratio', 'N/A')}")
            print(f"  Beta:   {risk.get('beta', 'N/A')}")
            print(f"  MaxDD:  {risk.get('max_drawdown', 'N/A')}")
        else:
            print(f"  Error: {risk['error']}")

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_client.py <path_to_pdf>")
        sys.exit(1)
    main(sys.argv[1])
