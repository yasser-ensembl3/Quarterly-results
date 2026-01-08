#!/usr/bin/env python3
"""Convert extracted JSON insights to readable Markdown files."""

import json
from pathlib import Path

INSIGHTS_DIR = Path(__file__).parent.parent / "data" / "insights"


def financial_to_markdown(data: dict, company: str) -> str:
    """Convert financial JSON to readable markdown."""
    lines = []

    # Header
    info = data.get("company_info", {})
    lines.append(f"# {info.get('name', company)} - Financial Analysis")
    lines.append(f"**Quarter:** {info.get('quarter', 'Q3')} {info.get('year', 2025)}")
    lines.append(f"**Currency:** {info.get('currency', 'USD')}")
    lines.append(f"**Sector:** {info.get('company_type', 'N/A')}")
    lines.append("")

    # Income Statement
    income = data.get("income_statement", {})
    if income:
        lines.append("## Income Statement")
        lines.append("")
        lines.append("| Metric | Value | YoY Change |")
        lines.append("|--------|-------|------------|")

        for key, val in income.items():
            if isinstance(val, dict) and val.get("value") is not None:
                value = f"${val['value']:,.1f}M" if isinstance(val.get('value'), (int, float)) else str(val.get('value'))
                yoy = f"{val.get('yoy_pct', 'N/A')}%" if val.get('yoy_pct') else "N/A"
                lines.append(f"| {key.replace('_', ' ').title()} | {value} | {yoy} |")
            elif isinstance(val, (int, float)):
                lines.append(f"| {key.replace('_', ' ').title()} | ${val:,.1f}M | N/A |")
        lines.append("")

    # Balance Sheet
    balance = data.get("balance_sheet", {})
    if balance and any(v for v in balance.values() if v is not None):
        lines.append("## Balance Sheet")
        lines.append("")
        lines.append("| Item | Value (M) |")
        lines.append("|------|-----------|")
        for key, val in balance.items():
            if val is not None:
                lines.append(f"| {key.replace('_', ' ').title()} | ${val:,.1f} |")
        lines.append("")

    # Cash Flow
    cashflow = data.get("cash_flow", {})
    if cashflow and any(v for v in cashflow.values() if v is not None):
        lines.append("## Cash Flow")
        lines.append("")
        lines.append("| Item | Value (M) |")
        lines.append("|------|-----------|")
        for key, val in cashflow.items():
            if val is not None:
                lines.append(f"| {key.replace('_', ' ').title()} | ${val:,.1f} |")
        lines.append("")

    # Revenue Breakdown
    breakdown = data.get("revenue_breakdown", {})
    if breakdown:
        lines.append("## Revenue Breakdown")
        lines.append("")

        for category in ["by_segment", "by_geography", "by_product"]:
            items = breakdown.get(category, [])
            if items:
                lines.append(f"### {category.replace('_', ' ').title()}")
                lines.append("")
                lines.append("| Name | Revenue (M) | % of Total | YoY % |")
                lines.append("|------|-------------|------------|-------|")
                for item in items:
                    name = item.get("name") or item.get("region") or item.get("product", "N/A")
                    rev = item.get("revenue", "N/A")
                    pct = item.get("pct_of_total", "N/A")
                    yoy = item.get("yoy_pct", "N/A")
                    lines.append(f"| {name} | {rev} | {pct}% | {yoy}% |")
                lines.append("")

    # Sector Specific
    sector = data.get("sector_specific", {})
    if sector and any(v for v in sector.values() if v is not None):
        lines.append("## Sector-Specific Metrics")
        lines.append("")
        for key, val in sector.items():
            if val is not None:
                lines.append(f"- **{key.replace('_', ' ').title()}:** {val}")
        lines.append("")

    # Operational Metrics
    ops = data.get("operational_metrics", {})
    if ops:
        lines.append("## Operational Metrics")
        lines.append("")
        for key, val in ops.items():
            if key == "other_kpis" and val:
                for kpi in val:
                    lines.append(f"- **{kpi.get('name', 'N/A')}:** {kpi.get('value', 'N/A')} {kpi.get('unit', '')}")
            elif isinstance(val, dict):
                for subkey, subval in val.items():
                    if subval is not None:
                        lines.append(f"- **{key.title()} - {subkey.title()}:** {subval}")
        lines.append("")

    # Guidance
    guidance = data.get("guidance", {})
    if guidance:
        lines.append("## Guidance")
        lines.append("")
        for period, vals in guidance.items():
            if vals and isinstance(vals, dict):
                lines.append(f"### {period.replace('_', ' ').title()}")
                for key, val in vals.items():
                    if val is not None and key != "other":
                        lines.append(f"- **{key.replace('_', ' ').title()}:** {val}")
                lines.append("")

    # Metadata
    meta = data.get("extraction_metadata", {})
    if meta:
        lines.append("---")
        lines.append(f"*Confidence: {meta.get('confidence_score', 'N/A')} | Completeness: {meta.get('data_completeness', 'N/A')}*")

    return "\n".join(lines)


def strategic_to_markdown(data: dict, company: str) -> str:
    """Convert strategic JSON to readable markdown."""
    lines = []

    # Header
    info = data.get("company_info", {})
    lines.append(f"# {info.get('name', company)} - Strategic Analysis")
    lines.append(f"**Quarter:** {info.get('quarter', 'Q3')} {info.get('year', 2025)}")
    lines.append("")

    # Executive Summary
    summary = data.get("executive_summary", {})
    if summary:
        lines.append("## Executive Summary")
        lines.append("")
        if summary.get("one_liner"):
            lines.append(f"**TL;DR:** {summary['one_liner']}")
            lines.append("")
        if summary.get("management_tone"):
            lines.append(f"**Management Tone:** {summary['management_tone'].title()}")
            lines.append("")
        if summary.get("key_narrative"):
            lines.append(f"{summary['key_narrative']}")
            lines.append("")

    # Key Takeaways
    takeaways = data.get("key_takeaways", [])
    if takeaways:
        lines.append("## Key Takeaways")
        lines.append("")
        for i, t in enumerate(takeaways, 1):
            lines.append(f"{i}. {t}")
        lines.append("")

    # Strategic Initiatives
    initiatives = data.get("strategic_initiatives", [])
    if initiatives:
        lines.append("## Strategic Initiatives")
        lines.append("")
        for init in initiatives:
            lines.append(f"### {init.get('initiative', 'N/A')}")
            lines.append(f"- **Status:** {init.get('status', 'N/A')}")
            if init.get('progress'):
                lines.append(f"- **Progress:** {init['progress']}")
            if init.get('expected_impact'):
                lines.append(f"- **Expected Impact:** {init['expected_impact']}")
            lines.append("")

    # Product & Innovation
    product = data.get("product_and_innovation", {})
    if product:
        lines.append("## Product & Innovation")
        lines.append("")

        launches = product.get("new_launches", [])
        if launches:
            lines.append("### New Launches")
            for p in launches:
                lines.append(f"- **{p.get('product', 'N/A')}:** {p.get('description', '')}")
            lines.append("")

        if product.get("r_and_d_focus"):
            lines.append(f"### R&D Focus")
            lines.append(product["r_and_d_focus"])
            lines.append("")

    # Competitive Landscape
    competitive = data.get("competitive_landscape", {})
    if competitive:
        lines.append("## Competitive Position")
        lines.append("")
        if competitive.get("market_position"):
            lines.append(f"**Market Position:** {competitive['market_position']}")
            lines.append("")

        advantages = competitive.get("competitive_advantages", [])
        if advantages:
            lines.append("### Competitive Advantages")
            for a in advantages:
                lines.append(f"- {a}")
            lines.append("")

        trends = competitive.get("industry_trends", [])
        if trends:
            lines.append("### Industry Trends")
            for t in trends:
                if isinstance(t, dict):
                    lines.append(f"- **{t.get('trend', 'N/A')}:** {t.get('company_positioning', '')}")
                else:
                    lines.append(f"- {t}")
            lines.append("")

    # Risks & Challenges
    risks = data.get("risks_and_challenges", [])
    if risks:
        lines.append("## Risks & Challenges")
        lines.append("")
        for r in risks:
            severity = r.get('severity', 'medium').upper()
            lines.append(f"### [{severity}] {r.get('risk', 'N/A')}")
            lines.append(f"- **Category:** {r.get('category', 'N/A')}")
            if r.get('management_response'):
                lines.append(f"- **Management Response:** {r['management_response']}")
            lines.append("")

    # Partnerships & M&A
    ma = data.get("partnerships_and_ma", {})
    if ma:
        acquisitions = ma.get("acquisitions", [])
        partnerships = ma.get("partnerships", [])

        if acquisitions or partnerships:
            lines.append("## Partnerships & M&A")
            lines.append("")

            if acquisitions:
                lines.append("### Acquisitions")
                for a in acquisitions:
                    lines.append(f"- **{a.get('target', 'N/A')}:** {a.get('rationale', '')}")
                lines.append("")

            if partnerships:
                lines.append("### Partnerships")
                for p in partnerships:
                    lines.append(f"- **{p.get('partner', 'N/A')}:** {p.get('significance', '')}")
                lines.append("")

    # Notable Quotes
    quotes = data.get("notable_quotes", [])
    if quotes:
        lines.append("## Notable Quotes")
        lines.append("")
        for q in quotes:
            lines.append(f"> \"{q.get('quote', '')}\"")
            lines.append(f"> — {q.get('speaker', 'N/A')}")
            lines.append("")

    # Investor Highlights
    investor = data.get("investor_highlights", {})
    if investor:
        lines.append("## Investor Highlights")
        lines.append("")

        bull = investor.get("bull_case", [])
        if bull:
            lines.append("### Bull Case")
            for b in bull:
                lines.append(f"- {b}")
            lines.append("")

        bear = investor.get("bear_case", [])
        if bear:
            lines.append("### Bear Case")
            for b in bear:
                lines.append(f"- {b}")
            lines.append("")

        catalysts = investor.get("catalysts", [])
        if catalysts:
            lines.append("### Upcoming Catalysts")
            for c in catalysts:
                if isinstance(c, dict):
                    lines.append(f"- **{c.get('catalyst', 'N/A')}** ({c.get('timeline', 'TBD')}): {c.get('potential_impact', '')}")
                else:
                    lines.append(f"- {c}")
            lines.append("")

    # Metadata
    meta = data.get("extraction_metadata", {})
    if meta:
        lines.append("---")
        lines.append(f"*Confidence: {meta.get('confidence_score', 'N/A')} | Document Type: {meta.get('document_type', 'N/A')}*")

    return "\n".join(lines)


def convert_all_insights():
    """Convert all JSON insights to Markdown."""
    companies = [d for d in INSIGHTS_DIR.iterdir() if d.is_dir()]

    print(f"Found {len(companies)} companies in {INSIGHTS_DIR}")

    for company_dir in companies:
        company = company_dir.name
        print(f"\n[{company}]")

        # Financial
        financial_json = company_dir / f"{company.lower()}_financial.json"
        if financial_json.exists():
            data = json.loads(financial_json.read_text(encoding="utf-8"))
            md_content = financial_to_markdown(data, company)
            md_path = company_dir / f"{company.lower()}_financial.md"
            md_path.write_text(md_content, encoding="utf-8")
            print(f"  -> {md_path.name}")

        # Strategic
        strategic_json = company_dir / f"{company.lower()}_strategic.json"
        if strategic_json.exists():
            data = json.loads(strategic_json.read_text(encoding="utf-8"))
            md_content = strategic_to_markdown(data, company)
            md_path = company_dir / f"{company.lower()}_strategic.md"
            md_path.write_text(md_content, encoding="utf-8")
            print(f"  -> {md_path.name}")


if __name__ == "__main__":
    convert_all_insights()
