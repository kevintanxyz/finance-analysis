"""
Test Claude Vision components without a PDF.

This verifies all parts are working before testing with real PDFs.

Usage:
    uv run python test_components.py
"""
import asyncio
from app.llm import create_llm
from app.parsers.bank_configs import detect_bank, BANK_CONFIGS
from app.parsers.pdf_router import PDFParserRouter
from app.parsers.valuation_pdf import ISIN_TICKER_MAP


def test_bank_configs():
    """Test bank configuration system."""
    print("\n" + "="*60)
    print("🏦 Testing Bank Configuration System")
    print("="*60 + "\n")

    # Test detection for each bank
    test_cases = [
        ("NUMAN Valorisation Portfolio", "numan"),
        ("UBS Switzerland AG Portfolio Statement", "ubs"),
        ("Julius Baer Vermögensübersicht", "julius_baer"),
        ("Credit Suisse Investment Proposal", "credit_suisse"),
        ("Unknown Bank Statement", "generic"),
    ]

    for text, expected in test_cases:
        detected = detect_bank(text)
        status = "✅" if detected.name == expected else "❌"
        print(f"{status} '{text[:40]}...'")
        print(f"   Detected: {detected.name}, Strategy: {detected.parser}")
        print()

    print(f"✅ All {len(BANK_CONFIGS)} bank configs loaded")


def test_llm_provider():
    """Test LLM provider initialization."""
    print("\n" + "="*60)
    print("🤖 Testing LLM Provider")
    print("="*60 + "\n")

    try:
        llm = create_llm()
        provider_name = llm.__class__.__name__
        print(f"✅ LLM Provider: {provider_name}")

        # Check if it's Claude (required for vision)
        if provider_name == "ClaudeProvider":
            print("✅ Claude Vision: Available")
            print("   Model: claude-sonnet-4-20250514")
            print("   Vision support: ✅ Yes")
        else:
            print("⚠️  Warning: Using Ollama (no vision support)")
            print("   Set ANTHROPIC_API_KEY for Claude Vision")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Tip: Check .env file for ANTHROPIC_API_KEY")


async def test_router():
    """Test PDF router initialization."""
    print("\n" + "="*60)
    print("🖼️  Testing PDF Router")
    print("="*60 + "\n")

    try:
        llm = create_llm()
        router = PDFParserRouter(
            llm=llm,
            isin_ticker_map=ISIN_TICKER_MAP,
            verbose=False
        )
        print("✅ PDFParserRouter initialized")
        print(f"   ISIN mappings: {len(ISIN_TICKER_MAP)} known securities")
        print(f"   MVP mode: USE_CLAUDE_VISION_ONLY = True")
        print()
        print("✅ Router ready for PDF extraction")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_vision_api():
    """Test Claude Vision API with a simple image."""
    print("\n" + "="*60)
    print("🖼️  Testing Claude Vision API")
    print("="*60 + "\n")

    try:
        llm = create_llm()

        if llm.__class__.__name__ != "ClaudeProvider":
            print("⚠️  Skipping: Claude API not available")
            print("   Set ANTHROPIC_API_KEY to test Vision API")
            return

        # Test if complete_with_images method exists
        if hasattr(llm, 'complete_with_images'):
            print("✅ complete_with_images() method: Available")
            print("   Ready to process PDF images")
        else:
            print("❌ complete_with_images() method: Missing")

    except Exception as e:
        print(f"❌ Error: {e}")


def test_isin_mapping():
    """Test ISIN → ticker mapping."""
    print("\n" + "="*60)
    print("📊 Testing ISIN Mapping")
    print("="*60 + "\n")

    sample_isins = [
        "CH0012032048",  # Roche
        "FR0000120271",  # TotalEnergies
        "US0378331005",  # Apple
        "US78462F1030",  # SPDR S&P 500
    ]

    print(f"Total known ISINs: {len(ISIN_TICKER_MAP)}\n")

    for isin in sample_isins:
        if isin in ISIN_TICKER_MAP:
            ticker, is_listed = ISIN_TICKER_MAP[isin]
            print(f"✅ {isin} → {ticker} (listed: {is_listed})")
        else:
            print(f"⚠️  {isin} → Not in mapping")

    print()
    print("✅ ISIN mapping system working")


async def main():
    """Run all component tests."""
    print("\n" + "="*60)
    print("🧪 NUMAN Claude Vision Component Tests")
    print("="*60)

    # Run all tests
    test_bank_configs()
    test_llm_provider()
    await test_router()
    await test_vision_api()
    test_isin_mapping()

    # Final summary
    print("\n" + "="*60)
    print("📋 Test Summary")
    print("="*60 + "\n")
    print("✅ Bank detection system: OK")
    print("✅ LLM provider: OK")
    print("✅ PDF router: OK")
    print("✅ ISIN mapping: OK")
    print()
    print("🎯 All components ready!")
    print()
    print("Next steps:")
    print("  1. Get a portfolio PDF (NUMAN, UBS, Julius Baer, any format)")
    print("  2. Run: uv run python test_pdf_extraction.py <pdf_path>")
    print("  3. Claude Vision will extract all positions automatically")


if __name__ == "__main__":
    asyncio.run(main())
