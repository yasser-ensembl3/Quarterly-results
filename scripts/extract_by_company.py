"""
Extract financial and strategic insights per company.

Workflow:
1. Convert PDFs to Markdown using LlamaParse
2. Upload markdown files to Google Drive
3. Combine all markdown files for a company
4. Run financial and strategic extractors
5. Output: JSON + formatted Markdown for each extraction
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.pdf_to_markdown import pdf_to_markdown
from src.agents.financial_extractor import FinancialExtractor
from src.agents.strategic_extractor import StrategicExtractor
from src.gdrive.sync import DriveSync
from src.config import get_settings


def json_to_financial_markdown(data: dict, company_name: str) -> str:
    """Convert financial JSON to readable markdown."""
    lines = [
        f"# {company_name} - Financial Insights",
        f"",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        f"",
    ]

    # Company Info
    info = data.get("company_info", {})
    if info:
        lines.extend([
            "## Company Information",
            f"- **Company**: {info.get('name', 'N/A')}",
            f"- **Ticker**: {info.get('ticker', 'N/A')}",
            f"- **Quarter**: {info.get('quarter', 'N/A')} {info.get('year', 'N/A')}",
            f"- **Type**: {info.get('company_type', 'N/A')}",
            "",
        ])

    # Income Statement
    income = data.get("income_statement", {})
    if income:
        lines.extend(["## Income Statement", ""])

        if income.get("revenue"):
            rev = income["revenue"]
            yoy = f" ({rev.get('yoy_pct', 'N/A'):+.1f}% YoY)" if rev.get('yoy_pct') else ""
            lines.append(f"| Metric | Value | YoY Change |")
            lines.append(f"|--------|-------|------------|")
            lines.append(f"| Revenue | ${rev.get('value', 'N/A'):,.0f}M | {rev.get('yoy_pct', 'N/A')}% |")

        for metric in ["gross_profit", "operating_income", "net_income"]:
            m = income.get(metric, {})
            if m and m.get("value"):
                margin = f" ({m.get('margin_pct', 'N/A'):.1f}% margin)" if m.get('margin_pct') else ""
                lines.append(f"| {metric.replace('_', ' ').title()} | ${m.get('value', 0):,.0f}M | {m.get('margin_pct', 'N/A')}% margin |")

        eps = income.get("eps", {})
        if eps:
            lines.append(f"| EPS (Diluted) | ${eps.get('diluted', 'N/A')} | {eps.get('yoy_pct', 'N/A')}% |")
        lines.append("")

    # Balance Sheet
    balance = data.get("balance_sheet", {})
    if balance:
        lines.extend(["## Balance Sheet", ""])
        lines.append("| Item | Value (M) |")
        lines.append("|------|-----------|")
        for key in ["total_cash", "cash_and_equivalents", "total_debt", "net_cash_position", "shareholders_equity"]:
            if balance.get(key):
                lines.append(f"| {key.replace('_', ' ').title()} | ${balance[key]:,.0f} |")
        lines.append("")

    # Cash Flow
    cf = data.get("cash_flow", {})
    if cf:
        lines.extend(["## Cash Flow", ""])
        lines.append("| Item | Value (M) |")
        lines.append("|------|-----------|")
        for key in ["operating_cash_flow", "free_cash_flow", "capex"]:
            if cf.get(key):
                lines.append(f"| {key.replace('_', ' ').title()} | ${cf[key]:,.0f} |")
        lines.append("")

    # Revenue Breakdown
    breakdown = data.get("revenue_breakdown", {})
    if breakdown:
        lines.extend(["## Revenue Breakdown", ""])

        if breakdown.get("by_segment"):
            lines.extend(["### By Segment", ""])
            lines.append("| Segment | Revenue (M) | % of Total | YoY |")
            lines.append("|---------|-------------|------------|-----|")
            for seg in breakdown["by_segment"]:
                lines.append(f"| {seg.get('name', 'N/A')} | ${seg.get('revenue', 0):,.0f} | {seg.get('pct_of_total', 'N/A')}% | {seg.get('yoy_pct', 'N/A')}% |")
            lines.append("")

        if breakdown.get("by_geography"):
            lines.extend(["### By Geography", ""])
            lines.append("| Region | Revenue (M) | % of Total |")
            lines.append("|--------|-------------|------------|")
            for geo in breakdown["by_geography"]:
                lines.append(f"| {geo.get('region', 'N/A')} | ${geo.get('revenue', 0):,.0f} | {geo.get('pct_of_total', 'N/A')}% |")
            lines.append("")

    # Sector Specific
    sector = data.get("sector_specific", {})
    if sector:
        lines.extend(["## Sector-Specific Metrics", ""])
        for key, value in sector.items():
            if value is not None:
                lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        lines.append("")

    # Guidance
    guidance = data.get("guidance", {})
    if guidance:
        lines.extend(["## Guidance", ""])

        nq = guidance.get("next_quarter", {})
        if nq and (nq.get("revenue_low") or nq.get("revenue_high")):
            lines.append(f"### Next Quarter")
            lines.append(f"- Revenue: ${nq.get('revenue_low', 'N/A'):,.0f}M - ${nq.get('revenue_high', 'N/A'):,.0f}M")
            if nq.get("eps_low"):
                lines.append(f"- EPS: ${nq.get('eps_low')} - ${nq.get('eps_high')}")
            lines.append("")

        fy = guidance.get("full_year", {})
        if fy and (fy.get("revenue_low") or fy.get("revenue_high")):
            lines.append(f"### Full Year")
            lines.append(f"- Revenue: ${fy.get('revenue_low', 'N/A'):,.0f}M - ${fy.get('revenue_high', 'N/A'):,.0f}M")
            lines.append("")

    # Metadata
    meta = data.get("extraction_metadata", {})
    if meta:
        lines.extend([
            "---",
            f"*Confidence: {meta.get('confidence_score', 'N/A')} | Completeness: {meta.get('data_completeness', 'N/A')}*",
        ])

    return "\n".join(lines)


def json_to_strategic_markdown(data: dict, company_name: str) -> str:
    """Convert strategic JSON to readable markdown."""
    lines = [
        f"# {company_name} - Strategic Insights",
        f"",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        f"",
    ]

    # Executive Summary
    summary = data.get("executive_summary", {})
    if summary:
        lines.extend(["## Executive Summary", ""])
        if summary.get("one_liner"):
            lines.append(f"> {summary['one_liner']}")
            lines.append("")
        if summary.get("management_tone"):
            lines.append(f"**Management Tone**: {summary['management_tone']}")
        if summary.get("key_narrative"):
            lines.append(f"\n{summary['key_narrative']}")
        lines.append("")

    # Strategic Initiatives
    initiatives = data.get("strategic_initiatives", [])
    if initiatives:
        lines.extend(["## Strategic Initiatives", ""])
        for init in initiatives:
            lines.append(f"### {init.get('initiative', 'Initiative')}")
            lines.append(f"- **Status**: {init.get('status', 'N/A')}")
            if init.get("progress"):
                lines.append(f"- **Progress**: {init['progress']}")
            if init.get("expected_impact"):
                lines.append(f"- **Expected Impact**: {init['expected_impact']}")
            lines.append("")

    # Products & Innovation
    products = data.get("product_and_innovation", {})
    if products:
        lines.extend(["## Products & Innovation", ""])

        launches = products.get("new_launches", [])
        if launches:
            lines.append("### New Launches")
            for launch in launches:
                lines.append(f"- **{launch.get('product', 'Product')}**: {launch.get('description', '')}")
            lines.append("")

        if products.get("r_and_d_focus"):
            lines.append(f"### R&D Focus")
            lines.append(products["r_and_d_focus"])
            lines.append("")

    # Competitive Landscape
    competitive = data.get("competitive_landscape", {})
    if competitive:
        lines.extend(["## Competitive Position", ""])

        if competitive.get("market_position"):
            lines.append(f"**Market Position**: {competitive['market_position']}")
            lines.append("")

        advantages = competitive.get("competitive_advantages", [])
        if advantages:
            lines.append("### Competitive Advantages")
            for adv in advantages:
                lines.append(f"- {adv}")
            lines.append("")

        trends = competitive.get("industry_trends", [])
        if trends:
            lines.append("### Industry Trends")
            for trend in trends:
                if isinstance(trend, dict):
                    lines.append(f"- **{trend.get('trend', '')}**: {trend.get('company_positioning', '')}")
                else:
                    lines.append(f"- {trend}")
            lines.append("")

    # Partnerships & M&A
    pma = data.get("partnerships_and_ma", {})
    if pma:
        acquisitions = pma.get("acquisitions", [])
        partnerships = pma.get("partnerships", [])

        if acquisitions or partnerships:
            lines.extend(["## Partnerships & M&A", ""])

            if acquisitions:
                lines.append("### Acquisitions")
                for acq in acquisitions:
                    lines.append(f"- **{acq.get('target', 'Target')}**: {acq.get('rationale', '')} ({acq.get('status', '')})")
                lines.append("")

            if partnerships:
                lines.append("### Partnerships")
                for part in partnerships:
                    lines.append(f"- **{part.get('partner', 'Partner')}**: {part.get('significance', '')}")
                lines.append("")

    # Risks
    risks = data.get("risks_and_challenges", [])
    if risks:
        lines.extend(["## Risks & Challenges", ""])
        for risk in risks:
            severity = risk.get("severity", "").upper() if risk.get("severity") else ""
            lines.append(f"### [{severity}] {risk.get('risk', 'Risk')}")
            lines.append(f"- **Category**: {risk.get('category', 'N/A')}")
            if risk.get("management_response"):
                lines.append(f"- **Management Response**: {risk['management_response']}")
            lines.append("")

    # Notable Quotes
    quotes = data.get("notable_quotes", [])
    if quotes:
        lines.extend(["## Notable Quotes", ""])
        for quote in quotes:
            lines.append(f"> \"{quote.get('quote', '')}\"")
            lines.append(f"> — *{quote.get('speaker', 'Executive')}*")
            lines.append("")

    # Investor Highlights
    highlights = data.get("investor_highlights", {})
    if highlights:
        lines.extend(["## Investor Highlights", ""])

        bull = highlights.get("bull_case", [])
        if bull:
            lines.append("### Bull Case")
            for b in bull:
                lines.append(f"- {b}")
            lines.append("")

        bear = highlights.get("bear_case", [])
        if bear:
            lines.append("### Bear Case")
            for b in bear:
                lines.append(f"- {b}")
            lines.append("")

        catalysts = highlights.get("catalysts", [])
        if catalysts:
            lines.append("### Upcoming Catalysts")
            for cat in catalysts:
                if isinstance(cat, dict):
                    lines.append(f"- **{cat.get('catalyst', '')}** ({cat.get('timeline', '')}): {cat.get('potential_impact', '')}")
                else:
                    lines.append(f"- {cat}")
            lines.append("")

    # Key Takeaways
    takeaways = data.get("key_takeaways", [])
    if takeaways:
        lines.extend(["## Key Takeaways", ""])
        for i, t in enumerate(takeaways, 1):
            lines.append(f"{i}. {t}")
        lines.append("")

    # Metadata
    meta = data.get("extraction_metadata", {})
    if meta:
        lines.extend([
            "---",
            f"*Confidence: {meta.get('confidence_score', 'N/A')} | Richness: {meta.get('richness', 'N/A')}*",
        ])

    return "\n".join(lines)


def convert_pdfs_to_markdown(raw_dir: Path, markdown_dir: Path, force: bool = False) -> dict[str, list[Path]]:
    """
    Convert all PDFs in raw_dir to markdown files in markdown_dir.

    Args:
        raw_dir: Directory containing company folders with PDFs
        markdown_dir: Output directory for markdown files
        force: If True, reconvert even if markdown already exists

    Returns:
        Dict mapping company names to list of converted markdown paths
    """
    converted_files = {}

    # Get all company directories
    companies = sorted([d for d in raw_dir.iterdir() if d.is_dir()])

    for company_dir in companies:
        company_name = company_dir.name
        pdf_files = list(company_dir.glob("*.pdf"))

        if not pdf_files:
            continue

        print(f"\n[PDF] {company_name}: {len(pdf_files)} PDF(s) found")

        # Create markdown output directory for this company
        company_md_dir = markdown_dir / company_name
        company_md_dir.mkdir(parents=True, exist_ok=True)

        converted_files[company_name] = []

        for pdf_file in pdf_files:
            md_filename = pdf_file.stem + ".md"
            md_path = company_md_dir / md_filename

            # Skip if already converted (unless force=True)
            if md_path.exists() and not force:
                print(f"  [SKIP] {pdf_file.name} (already converted)")
                continue

            print(f"  [CONVERT] {pdf_file.name}...")
            try:
                markdown_content = pdf_to_markdown(pdf_file, use_llamaparse=True)
                md_path.write_text(markdown_content, encoding="utf-8")
                print(f"  [OK] -> {md_filename} ({len(markdown_content):,} chars)")
                converted_files[company_name].append(md_path)
            except Exception as e:
                print(f"  [ERROR] {pdf_file.name}: {e}")

    return converted_files


def upload_markdowns_to_drive(markdown_dir: Path, quarter: str) -> dict:
    """
    Upload all markdown files to corresponding Google Drive folders.

    Args:
        markdown_dir: Directory containing company markdown folders
        quarter: Quarter name (e.g., 'Q3')

    Returns:
        Dict with upload results per company
    """
    settings = get_settings()
    root_folder_id = settings.gdrive_root_folder_id

    if not root_folder_id:
        print("[WARN] GDRIVE_ROOT_FOLDER_ID not set, skipping upload")
        return {}

    try:
        drive_sync = DriveSync()
    except Exception as e:
        print(f"[WARN] Could not initialize Google Drive: {e}")
        return {}

    results = {}

    # Get all company directories
    companies = sorted([d for d in markdown_dir.iterdir() if d.is_dir()])

    for company_dir in companies:
        company_name = company_dir.name
        md_files = list(company_dir.glob("*.md"))

        if not md_files:
            continue

        print(f"\n[UPLOAD] {company_name}: {len(md_files)} markdown(s)")

        upload_result = drive_sync.upload_results_to_company_folder(
            root_folder_id=root_folder_id,
            quarter_name=quarter,
            company_name=company_name,
            files=md_files
        )

        results[company_name] = upload_result

        if upload_result.get('uploaded'):
            for item in upload_result['uploaded']:
                print(f"  [OK] {item['file']}")
        if upload_result.get('errors'):
            for err in upload_result['errors']:
                print(f"  [ERROR] {err}")

    return results


def process_company(company_dir: Path, output_dir: Path, financial_extractor, strategic_extractor):
    """Process all markdowns for a company and extract insights."""
    company_name = company_dir.name

    # Combine all markdown files
    md_files = sorted(company_dir.glob("*.md"))
    if not md_files:
        print(f"  [SKIP] No markdown files found")
        return

    combined_content = []
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        combined_content.append(f"\n\n{'='*80}\n# SOURCE: {md_file.name}\n{'='*80}\n\n{content}")

    full_content = "\n".join(combined_content)
    print(f"  Combined {len(md_files)} files ({len(full_content):,} chars)")

    # Create output directory
    company_output = output_dir / company_name
    company_output.mkdir(parents=True, exist_ok=True)

    # Financial extraction
    print(f"  [Financial] Extracting...")
    try:
        financial_data = financial_extractor.extract(full_content, source_file=company_name)

        # Save JSON
        json_path = company_output / f"{company_name.lower().replace(' ', '_')}_financial.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(financial_data, f, indent=2, ensure_ascii=False)

        # Save MD
        md_content = json_to_financial_markdown(financial_data, company_name)
        md_path = company_output / f"{company_name.lower().replace(' ', '_')}_financial.md"
        md_path.write_text(md_content, encoding="utf-8")

        print(f"  [Financial] Done")
    except Exception as e:
        print(f"  [Financial] Error: {e}")

    # Strategic extraction
    print(f"  [Strategic] Extracting...")
    try:
        strategic_data = strategic_extractor.extract(full_content, source_file=company_name)

        # Save JSON
        json_path = company_output / f"{company_name.lower().replace(' ', '_')}_strategic.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(strategic_data, f, indent=2, ensure_ascii=False)

        # Save MD
        md_content = json_to_strategic_markdown(strategic_data, company_name)
        md_path = company_output / f"{company_name.lower().replace(' ', '_')}_strategic.md"
        md_path.write_text(md_content, encoding="utf-8")

        print(f"  [Strategic] Done")
    except Exception as e:
        print(f"  [Strategic] Error: {e}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Extract financial and strategic insights from quarterly reports")
    parser.add_argument("--quarter", "-q", default="Q3", help="Quarter to process (default: Q3)")
    parser.add_argument("--force-convert", "-f", action="store_true", help="Force reconvert PDFs even if markdown exists")
    parser.add_argument("--skip-convert", action="store_true", help="Skip PDF conversion, use existing markdowns")
    parser.add_argument("--skip-upload", action="store_true", help="Skip uploading markdowns to Google Drive")
    parser.add_argument("--convert-only", action="store_true", help="Only convert PDFs (and upload), skip extraction")
    parser.add_argument("--upload-all", action="store_true", help="Upload all markdowns (not just newly converted)")
    args = parser.parse_args()

    # Setup paths
    base_dir = Path(__file__).parent.parent
    raw_dir = base_dir / "data" / "raw" / args.quarter
    markdown_dir = base_dir / "data" / "markdown" / args.quarter
    output_dir = base_dir / "data" / "insights"

    print(f"{'='*60}")
    print(f"Quarterly Report Extraction Pipeline")
    print(f"{'='*60}")
    print(f"Quarter: {args.quarter}")
    print(f"Raw PDFs: {raw_dir}")
    print(f"Markdown: {markdown_dir}")
    print(f"Output: {output_dir}")
    print(f"{'='*60}")

    # Step 1: Convert PDFs to Markdown
    converted_files = {}
    if not args.skip_convert:
        print(f"\n{'='*60}")
        print("STEP 1: PDF to Markdown Conversion (LlamaParse)")
        print(f"{'='*60}")

        if raw_dir.exists():
            converted_files = convert_pdfs_to_markdown(raw_dir, markdown_dir, force=args.force_convert)
            total_converted = sum(len(files) for files in converted_files.values())
            print(f"\nConverted {total_converted} PDF(s) to Markdown")
        else:
            print(f"[WARN] Raw directory not found: {raw_dir}")

    # Step 2: Upload to Google Drive
    if not args.skip_upload:
        print(f"\n{'='*60}")
        print("STEP 2: Upload Markdowns to Google Drive")
        print(f"{'='*60}")

        if args.upload_all or args.force_convert:
            # Upload all markdowns in the directory
            upload_markdowns_to_drive(markdown_dir, args.quarter)
        elif converted_files:
            # Only upload newly converted files
            upload_markdowns_to_drive(markdown_dir, args.quarter)
        else:
            print("[SKIP] No new markdowns to upload")

    if args.convert_only:
        print("\n[DONE] Convert-only mode, skipping extraction")
        return

    # Step 3: Extract Insights
    print(f"\n{'='*60}")
    print("STEP 3: Financial & Strategic Extraction")
    print(f"{'='*60}")

    # Initialize extractors
    print("\nInitializing extractors...")
    financial_extractor = FinancialExtractor()
    strategic_extractor = StrategicExtractor()

    # Get all company directories from markdown folder
    if not markdown_dir.exists():
        print(f"[ERROR] Markdown directory not found: {markdown_dir}")
        return

    companies = sorted([d for d in markdown_dir.iterdir() if d.is_dir()])
    print(f"Found {len(companies)} companies\n")

    for i, company_dir in enumerate(companies, 1):
        print(f"\n[{i}/{len(companies)}] {company_dir.name}")
        process_company(company_dir, output_dir, financial_extractor, strategic_extractor)

    print(f"\n{'='*60}")
    print(f"Done! Output saved to: {output_dir}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
