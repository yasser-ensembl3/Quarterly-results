#!/usr/bin/env python3
"""Extract financial and strategic insights from markdown files using Claude."""

import json
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.financial_extractor import FinancialExtractor
from agents.strategic_extractor import StrategicExtractor

# Directories
MARKDOWN_DIR = Path(__file__).parent.parent / "data" / "markdown" / "Q3"
INSIGHTS_DIR = Path(__file__).parent.parent / "data" / "insights"


def get_companies() -> list[str]:
    """Get list of company folders in markdown directory."""
    return [d.name for d in MARKDOWN_DIR.iterdir() if d.is_dir()]


def get_markdown_files(company: str) -> list[Path]:
    """Get all markdown files for a company."""
    company_dir = MARKDOWN_DIR / company
    return list(company_dir.glob("*.md"))


def combine_markdown_files(files: list[Path]) -> str:
    """Combine multiple markdown files into one document."""
    combined = []
    for f in files:
        content = f.read_text(encoding="utf-8")
        combined.append(f"# Source: {f.name}\n\n{content}")
    return "\n\n---\n\n".join(combined)


def extract_for_company(
    company: str,
    financial_extractor: FinancialExtractor,
    strategic_extractor: StrategicExtractor,
    skip_existing: bool = True
) -> dict:
    """Extract insights for a single company."""
    output_dir = INSIGHTS_DIR / company
    output_dir.mkdir(parents=True, exist_ok=True)

    financial_path = output_dir / f"{company.lower()}_financial.json"
    strategic_path = output_dir / f"{company.lower()}_strategic.json"

    results = {"company": company, "financial": None, "strategic": None, "errors": []}

    # Check if already extracted
    if skip_existing and financial_path.exists() and strategic_path.exists():
        print(f"  [SKIP] {company} - already extracted")
        return results

    # Get markdown files
    md_files = get_markdown_files(company)
    if not md_files:
        results["errors"].append("No markdown files found")
        return results

    print(f"\n{'='*60}")
    print(f"[{company}] Processing {len(md_files)} markdown files...")

    # Combine markdown content
    combined_content = combine_markdown_files(md_files)
    print(f"  Combined content: {len(combined_content):,} characters")

    # Financial extraction
    if not skip_existing or not financial_path.exists():
        print(f"  [Financial] Extracting...")
        try:
            financial_data = financial_extractor.extract(combined_content, company)
            if "error" not in financial_data:
                financial_path.write_text(
                    json.dumps(financial_data, indent=2, ensure_ascii=False),
                    encoding="utf-8"
                )
                results["financial"] = financial_data
                print(f"  [Financial] SUCCESS -> {financial_path.name}")
            else:
                results["errors"].append(f"Financial: {financial_data.get('error')}")
                print(f"  [Financial] ERROR: {financial_data.get('error')}")
        except Exception as e:
            results["errors"].append(f"Financial: {e}")
            print(f"  [Financial] EXCEPTION: {e}")
    else:
        print(f"  [Financial] Already exists, skipping")

    # Strategic extraction
    if not skip_existing or not strategic_path.exists():
        print(f"  [Strategic] Extracting...")
        try:
            strategic_data = strategic_extractor.extract(combined_content, company)
            if "error" not in strategic_data:
                strategic_path.write_text(
                    json.dumps(strategic_data, indent=2, ensure_ascii=False),
                    encoding="utf-8"
                )
                results["strategic"] = strategic_data
                print(f"  [Strategic] SUCCESS -> {strategic_path.name}")
            else:
                results["errors"].append(f"Strategic: {strategic_data.get('error')}")
                print(f"  [Strategic] ERROR: {strategic_data.get('error')}")
        except Exception as e:
            results["errors"].append(f"Strategic: {e}")
            print(f"  [Strategic] EXCEPTION: {e}")
    else:
        print(f"  [Strategic] Already exists, skipping")

    return results


def main(skip_existing: bool = True):
    """Main function to extract insights for all companies."""
    companies = get_companies()
    print(f"Found {len(companies)} companies in {MARKDOWN_DIR}")
    print(f"Companies: {', '.join(companies)}")

    # Initialize extractors
    print("\nInitializing extractors...")
    financial_extractor = FinancialExtractor()
    strategic_extractor = StrategicExtractor()

    # Process each company
    all_results = []
    successes = 0
    failures = []

    for i, company in enumerate(companies, 1):
        print(f"\n[{i}/{len(companies)}] Processing {company}...")
        result = extract_for_company(
            company,
            financial_extractor,
            strategic_extractor,
            skip_existing=skip_existing
        )
        all_results.append(result)

        if not result["errors"]:
            successes += 1
        else:
            failures.append((company, result["errors"]))

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total companies: {len(companies)}")
    print(f"Successes: {successes}")
    print(f"Failures: {len(failures)}")

    if failures:
        print("\nFailed companies:")
        for company, errors in failures:
            print(f"  - {company}: {errors}")


if __name__ == "__main__":
    # Set skip_existing=False to re-extract everything
    skip_existing = "--force" not in sys.argv
    main(skip_existing=skip_existing)
