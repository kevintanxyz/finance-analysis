"""
Test Claude Vision PDF extraction with a real PDF.

Usage:
    uv run python test_pdf_extraction.py path/to/valuation.pdf
"""
import sys
import asyncio
from pathlib import Path

from app.llm import create_llm
from app.parsers.enhanced_parser import parse_portfolio_pdf
from app.parsers.valuation_pdf import ISIN_TICKER_MAP


async def test_extraction(pdf_path: str):
    """Test PDF extraction with Claude Vision router."""

    print(f"\n{'='*60}")
    print(f"🖼️  Testing Claude Vision PDF Extraction")
    print(f"{'='*60}\n")

    # Check PDF exists
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"❌ Error: File not found: {pdf_path}")
        return

    print(f"📄 PDF: {pdf_file.name}")
    print(f"📦 Size: {pdf_file.stat().st_size / 1024:.1f} KB")
    print()

    # Create LLM provider
    print("🤖 Initializing Claude Vision provider...")
    try:
        llm = create_llm()
        print(f"   ✅ Provider: {llm.__class__.__name__}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("\n💡 Tip: Set ANTHROPIC_API_KEY in .env")
        return

    print()

    # Parse PDF with Claude Vision
    print("🖼️  Extracting with Claude Vision router...")
    print("   (This will take 6-8 seconds...)\n")

    try:
        positions, summary = await parse_portfolio_pdf(
            pdf_path,
            ISIN_TICKER_MAP,
            total_value_chf=0.0,  # Will be calculated
            llm=llm,
            enable_llm_validation=False,  # Claude Vision only
            verbose=True  # Show progress
        )

        print(f"\n{'='*60}")
        print(f"✅ Extraction Complete!")
        print(f"{'='*60}\n")

        # Display results
        print(f"🏦 Bank Detected: {summary.get('bank_detected', 'unknown')}")
        print(f"📋 Strategy Used: {summary.get('strategy_used', 'llm_vision')}")
        print(f"🎯 Confidence: {summary.get('confidence_score', 0):.2%}")
        print(f"📊 Positions: {len(positions)}")

        if positions:
            total_value = sum(p.value_chf for p in positions)
            print(f"💰 Total Value: CHF {total_value:,.2f}")
            print()

            # Show first 5 positions
            print("📋 First 5 Positions:")
            print("-" * 60)
            for i, pos in enumerate(positions[:5], 1):
                print(f"{i}. {pos.name}")
                print(f"   ISIN: {pos.isin or 'N/A'}")
                print(f"   Value: CHF {pos.value_chf:,.2f} ({pos.weight_pct:.2f}%)")
                print(f"   Asset Class: {pos.asset_class.value if pos.asset_class else 'N/A'}")
                print()

        # Warnings
        if summary.get('warnings'):
            print("⚠️  Warnings:")
            for warning in summary['warnings'][:5]:
                print(f"   - {warning}")
            if len(summary['warnings']) > 5:
                print(f"   ... and {len(summary['warnings']) - 5} more")
            print()

        # Success metrics
        print("✅ Test Successful!")
        print(f"   Extraction: {'✅ Valid' if summary.get('is_valid', True) else '⚠️  Has issues'}")
        print(f"   Positions: {len(positions)} extracted")

    except Exception as e:
        print(f"\n❌ Extraction Failed!")
        print(f"   Error: {type(e).__name__}: {e}")
        import traceback
        print("\n📋 Full traceback:")
        traceback.print_exc()
        print("\n💡 Tips:")
        print("   - Check that PDF is a valid valuation statement")
        print("   - Verify ANTHROPIC_API_KEY is set correctly")
        print("   - Try with a different PDF format")


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run python test_pdf_extraction.py <pdf_path>")
        print("\nExample:")
        print("  uv run python test_pdf_extraction.py tests/fixtures/sample_valuation.pdf")
        print("  uv run python test_pdf_extraction.py ~/Downloads/portfolio.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    asyncio.run(test_extraction(pdf_path))


if __name__ == "__main__":
    main()
