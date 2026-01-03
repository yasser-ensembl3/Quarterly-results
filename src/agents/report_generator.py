"""Markdown report generator from normalized financial data."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


def generate_markdown_report(normalized_data: dict, pipeline_info: dict = None) -> str:
    """
    Generate a markdown report from normalized financial data.

    Args:
        normalized_data: Normalized data from the pipeline
        pipeline_info: Optional pipeline metadata

    Returns:
        Markdown formatted report
    """
    lines = []

    # Header
    id_info = normalized_data.get('id', {})
    company = id_info.get('company', 'Unknown Company')
    ticker = id_info.get('ticker', '')
    quarter = id_info.get('quarter', '')
    year = id_info.get('year', '')
    company_type = id_info.get('company_type', '')

    lines.append(f"# {company} ({ticker}) - {quarter} {year} Earnings Report")
    lines.append("")
    lines.append(f"**Company Type:** {company_type.title()}")
    lines.append(f"**Report Date:** {id_info.get('report_date', 'N/A')}")
    lines.append("")

    # Investment Thesis (at the top for quick summary)
    highlights = normalized_data.get('highlights', {})
    thesis = highlights.get('investment_thesis')
    if thesis:
        lines.append("## Investment Thesis")
        lines.append("")
        lines.append(f"> {thesis}")
        lines.append("")

    # Financial Highlights
    lines.append("## Financial Highlights")
    lines.append("")

    fin = normalized_data.get('financials', {})
    inc = fin.get('income_statement', {})

    lines.append("### Income Statement")
    lines.append("")
    lines.append("| Metric | Value | YoY Change |")
    lines.append("|--------|-------|------------|")

    if inc.get('revenue'):
        yoy = f"{inc.get('revenue_yoy_pct', 'N/A')}%" if inc.get('revenue_yoy_pct') else "N/A"
        lines.append(f"| Revenue | ${inc['revenue']:,.1f}M | {yoy} |")
    if inc.get('gross_profit'):
        margin = f"({inc.get('gross_margin_pct', 'N/A')}% margin)" if inc.get('gross_margin_pct') else ""
        lines.append(f"| Gross Profit | ${inc['gross_profit']:,.1f}M | {margin} |")
    if inc.get('operating_income'):
        margin = f"({inc.get('operating_margin_pct', 'N/A')}% margin)" if inc.get('operating_margin_pct') else ""
        lines.append(f"| Operating Income | ${inc['operating_income']:,.1f}M | {margin} |")
    if inc.get('net_income'):
        margin = f"({inc.get('net_margin_pct', 'N/A')}% margin)" if inc.get('net_margin_pct') else ""
        lines.append(f"| Net Income | ${inc['net_income']:,.1f}M | {margin} |")
    if inc.get('adjusted_ebitda'):
        lines.append(f"| Adjusted EBITDA | ${inc['adjusted_ebitda']:,.1f}M | |")

    lines.append("")

    # EPS
    eps = fin.get('per_share', {})
    if eps.get('eps_basic') or eps.get('eps_diluted'):
        lines.append("### Earnings Per Share")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        if eps.get('eps_basic'):
            lines.append(f"| EPS (Basic) | ${eps['eps_basic']:.2f} |")
        if eps.get('eps_diluted'):
            lines.append(f"| EPS (Diluted) | ${eps['eps_diluted']:.2f} |")
        lines.append("")

    # Balance Sheet
    bs = fin.get('balance_sheet', {})
    if bs:
        lines.append("### Balance Sheet")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        if bs.get('cash_and_equivalents'):
            lines.append(f"| Cash & Equivalents | ${bs['cash_and_equivalents']:,.1f}M |")
        if bs.get('total_debt'):
            lines.append(f"| Total Debt | ${bs['total_debt']:,.1f}M |")
        if bs.get('net_cash'):
            lines.append(f"| Net Cash | ${bs['net_cash']:,.1f}M |")
        lines.append("")

    # Revenue Segments
    segments = normalized_data.get('segments', {})
    by_business = segments.get('by_business', [])
    if by_business:
        lines.append("## Revenue Breakdown")
        lines.append("")
        lines.append("### By Business Segment")
        lines.append("")
        lines.append("| Segment | Revenue | % of Total | YoY Growth |")
        lines.append("|---------|---------|------------|------------|")
        for seg in by_business:
            name = seg.get('name', 'Unknown')
            rev = f"${seg.get('revenue', 0):,.1f}M" if seg.get('revenue') else "N/A"
            pct = f"{seg.get('pct_of_total', 0):.1f}%" if seg.get('pct_of_total') else "N/A"
            yoy = f"{seg.get('yoy_pct', 'N/A')}%" if seg.get('yoy_pct') else "N/A"
            lines.append(f"| {name} | {rev} | {pct} | {yoy} |")
        lines.append("")

    by_geo = segments.get('by_geography', [])
    if by_geo:
        lines.append("### By Geography")
        lines.append("")
        lines.append("| Region | Revenue | % of Total |")
        lines.append("|--------|---------|------------|")
        for geo in by_geo:
            region = geo.get('region', 'Unknown')
            rev = f"${geo.get('revenue', 0):,.1f}M" if geo.get('revenue') else "N/A"
            pct = f"{geo.get('pct_of_total', 0):.1f}%" if geo.get('pct_of_total') else "N/A"
            lines.append(f"| {region} | {rev} | {pct} |")
        lines.append("")

    # Sector Specific Metrics
    sector = normalized_data.get('sector_specific', {})
    if sector and any(v for v in sector.values() if v is not None):
        lines.append("## Sector-Specific Metrics")
        lines.append("")

        if company_type == 'crypto':
            lines.append("### Crypto Metrics")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            if sector.get('trading_volume'):
                lines.append(f"| Trading Volume | ${sector['trading_volume']:,.0f}M |")
            if sector.get('assets_on_platform'):
                lines.append(f"| Assets on Platform | ${sector['assets_on_platform']:,.0f}M |")
            if sector.get('monthly_transacting_users'):
                lines.append(f"| Monthly Transacting Users | {sector['monthly_transacting_users']:,.0f}M |")
            if sector.get('verified_users'):
                lines.append(f"| Verified Users | {sector['verified_users']:,.0f}M |")
            if sector.get('stablecoin_market_cap'):
                lines.append(f"| Stablecoin Market Cap (USDC) | ${sector['stablecoin_market_cap']:,.0f}M |")
            if sector.get('transaction_revenue'):
                lines.append(f"| Transaction Revenue | ${sector['transaction_revenue']:,.1f}M |")
        else:
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            for key, value in sector.items():
                if value is not None:
                    if isinstance(value, (int, float)):
                        lines.append(f"| {key.replace('_', ' ').title()} | {value:,.1f} |")
                    else:
                        lines.append(f"| {key.replace('_', ' ').title()} | {value} |")
        lines.append("")

    # Operations
    ops = normalized_data.get('operations', {})
    if ops.get('employees'):
        lines.append("## Operations")
        lines.append("")
        lines.append(f"**Employees:** {ops['employees']:,}")
        if ops.get('employee_change_qoq'):
            lines.append(f" (QoQ change: {ops['employee_change_qoq']}%)")
        lines.append("")

    # Guidance
    guidance = normalized_data.get('guidance', {})
    if guidance:
        lines.append("## Guidance & Outlook")
        lines.append("")

        q1 = guidance.get('q_plus_1', {})
        if q1.get('revenue_low') or q1.get('revenue_high'):
            lines.append("### Next Quarter")
            lines.append("")
            if q1.get('revenue_low') and q1.get('revenue_high'):
                lines.append(f"- **Revenue Guidance:** ${q1['revenue_low']:,.0f}M - ${q1['revenue_high']:,.0f}M")
            if q1.get('other'):
                for item in q1['other']:
                    if isinstance(item, dict):
                        lines.append(f"- **{item.get('metric', 'N/A')}:** {item.get('guidance', 'N/A')}")
            lines.append("")

        if guidance.get('commentary'):
            lines.append("### Management Commentary")
            lines.append("")
            lines.append(f"> {guidance['commentary']}")
            lines.append("")

    # Strategic Updates
    strategic = normalized_data.get('strategic', {})
    if strategic:
        lines.append("## Strategic Updates")
        lines.append("")

        acq = strategic.get('acquisitions', [])
        if acq:
            lines.append("### Acquisitions")
            lines.append("")
            for a in acq:
                if isinstance(a, dict):
                    lines.append(f"- **{a.get('name', 'N/A')}:** {a.get('details', 'N/A')}")
                else:
                    lines.append(f"- {a}")
            lines.append("")

        partnerships = strategic.get('partnerships', [])
        if partnerships:
            lines.append("### Partnerships")
            lines.append("")
            for p in partnerships:
                if isinstance(p, dict):
                    lines.append(f"- **{p.get('partner', 'N/A')}:** {p.get('details', 'N/A')}")
                else:
                    lines.append(f"- {p}")
            lines.append("")

        products = strategic.get('product_launches', [])
        if products:
            lines.append("### Product Launches")
            lines.append("")
            for p in products:
                if isinstance(p, dict):
                    lines.append(f"- **{p.get('product', 'N/A')}:** {p.get('details', 'N/A')}")
                else:
                    lines.append(f"- {p}")
            lines.append("")

        initiatives = strategic.get('initiatives', [])
        if initiatives:
            lines.append("### Strategic Initiatives")
            lines.append("")
            for i in initiatives:
                if isinstance(i, dict):
                    lines.append(f"- **{i.get('initiative', 'N/A')}:** {i.get('progress', 'N/A')}")
                else:
                    lines.append(f"- {i}")
            lines.append("")

        advantages = strategic.get('competitive_advantages', [])
        if advantages:
            lines.append("### Competitive Advantages")
            lines.append("")
            for a in advantages:
                lines.append(f"- {a}")
            lines.append("")

    # Risks
    risks = strategic.get('risks', []) if strategic else []
    if risks:
        lines.append("## Risks & Challenges")
        lines.append("")
        for r in risks:
            if isinstance(r, dict):
                lines.append(f"- **{r.get('risk', 'N/A')}:** {r.get('details', 'N/A')}")
            else:
                lines.append(f"- {r}")
        lines.append("")

    # Investment Highlights
    if highlights:
        lines.append("## Investment Highlights")
        lines.append("")

        positives = highlights.get('key_positives', [])
        if positives:
            lines.append("### Key Positives")
            lines.append("")
            for p in positives:
                lines.append(f"- {p}")
            lines.append("")

        concerns = highlights.get('key_concerns', [])
        if concerns:
            lines.append("### Key Concerns")
            lines.append("")
            for c in concerns:
                lines.append(f"- {c}")
            lines.append("")

        quotes = highlights.get('notable_quotes', [])
        if quotes:
            lines.append("### Notable Quotes")
            lines.append("")
            for q in quotes:
                if isinstance(q, dict):
                    lines.append(f"> \"{q.get('quote', 'N/A')}\"")
                    lines.append(f"> — {q.get('speaker', 'N/A')}")
                    lines.append("")
            lines.append("")

    # Metadata
    meta = normalized_data.get('metadata', {})
    lines.append("---")
    lines.append("")
    lines.append("## Data Quality")
    lines.append("")
    lines.append(f"- **Quality Score:** {meta.get('data_quality_score', 'N/A')}")
    lines.append(f"- **Completeness:** {meta.get('completeness', 'N/A')}")
    if pipeline_info:
        lines.append(f"- **Sources Processed:** {pipeline_info.get('sources_processed', 'N/A')}")
    lines.append(f"- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    return "\n".join(lines)


def save_reports(normalized_data: dict, output_path: str, pipeline_info: dict = None) -> tuple:
    """
    Save both JSON and Markdown reports.

    Args:
        normalized_data: Normalized data from the pipeline
        output_path: Base path without extension
        pipeline_info: Optional pipeline metadata

    Returns:
        Tuple of (json_path, md_path)
    """
    import json

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save JSON
    json_path = output_path.with_suffix('.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(normalized_data, f, indent=2, ensure_ascii=False)

    # Save Markdown
    md_path = output_path.with_suffix('.md')
    md_content = generate_markdown_report(normalized_data, pipeline_info)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    return str(json_path), str(md_path)
