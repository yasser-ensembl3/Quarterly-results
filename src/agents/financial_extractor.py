"""Claude agent for FINANCIAL data extraction from Markdown."""

from __future__ import annotations

import json
import os
import re
from typing import List

import anthropic

# Token limit for chunking
MAX_CHUNK_CHARS = 80000

FINANCIAL_EXTRACTION_PROMPT = """You are an expert financial analyst specializing in quantitative analysis. Your task is to extract ALL FINANCIAL DATA from this quarterly earnings document.

DOCUMENT:
{markdown_content}

---

FOCUS EXCLUSIVELY ON FINANCIAL DATA:
- Income statement metrics (revenue, costs, profits, margins)
- Balance sheet data (cash, debt, assets)
- Cash flow data (operating, investing, financing)
- Per-share metrics (EPS, dividends)
- Revenue breakdowns (by segment, geography, product)
- Operational metrics with numbers (users, customers, employees)
- Sector-specific quantitative metrics
- Guidance with specific numbers

DO NOT EXTRACT:
- Strategic commentary (that's for another agent)
- Qualitative risk discussions
- Management quotes
- Competitive positioning analysis

Return a JSON with this structure:

{{
  "company_info": {{
    "name": "Full company name",
    "ticker": "SYMBOL",
    "quarter": "Q3",
    "year": 2025,
    "report_date": "YYYY-MM-DD or null",
    "currency": "USD",
    "company_type": "crypto/ecommerce/tech/fintech/retail/other"
  }},

  "income_statement": {{
    "revenue": {{"value": <number>, "unit": "millions", "yoy_pct": <number or null>, "qoq_pct": <number or null>}},
    "cost_of_revenue": {{"value": <number or null>, "unit": "millions"}},
    "gross_profit": {{"value": <number or null>, "margin_pct": <number or null>}},
    "operating_expenses": {{"value": <number or null>, "breakdown": {{}}}},
    "operating_income": {{"value": <number or null>, "margin_pct": <number or null>}},
    "ebitda": {{"value": <number or null>, "adjusted": <number or null>}},
    "net_income": {{"value": <number or null>, "margin_pct": <number or null>, "yoy_pct": <number or null>}},
    "eps": {{"basic": <number or null>, "diluted": <number or null>, "yoy_pct": <number or null>}}
  }},

  "balance_sheet": {{
    "cash_and_equivalents": <number or null>,
    "short_term_investments": <number or null>,
    "total_cash": <number or null>,
    "accounts_receivable": <number or null>,
    "inventory": <number or null>,
    "total_assets": <number or null>,
    "accounts_payable": <number or null>,
    "short_term_debt": <number or null>,
    "long_term_debt": <number or null>,
    "total_debt": <number or null>,
    "total_liabilities": <number or null>,
    "shareholders_equity": <number or null>,
    "net_cash_position": <number or null>
  }},

  "cash_flow": {{
    "operating_cash_flow": <number or null>,
    "investing_cash_flow": <number or null>,
    "financing_cash_flow": <number or null>,
    "capex": <number or null>,
    "free_cash_flow": <number or null>,
    "dividends_paid": <number or null>,
    "share_repurchases": <number or null>
  }},

  "revenue_breakdown": {{
    "by_segment": [
      {{"name": "Segment Name", "revenue": <number>, "pct_of_total": <number or null>, "yoy_pct": <number or null>}}
    ],
    "by_geography": [
      {{"region": "Region Name", "revenue": <number>, "pct_of_total": <number or null>, "yoy_pct": <number or null>}}
    ],
    "by_product": [
      {{"product": "Product Name", "revenue": <number>, "pct_of_total": <number or null>}}
    ]
  }},

  "operational_metrics": {{
    "employees": {{"count": <number or null>, "yoy_change": <number or null>}},
    "customers": {{"total": <number or null>, "active": <number or null>, "new": <number or null>, "churn_pct": <number or null>}},
    "users": {{"mau": <number or null>, "dau": <number or null>, "transacting": <number or null>, "verified": <number or null>}},
    "other_kpis": [
      {{"name": "KPI Name", "value": <number>, "unit": "string", "yoy_pct": <number or null>}}
    ]
  }},

  "sector_specific": {{
    // CRYPTO: trading_volume, assets_on_platform, stablecoin_market_cap, transaction_revenue, subscription_revenue
    // ECOMMERCE: gmv, orders, aov, prime_members, third_party_sales_pct
    // TECH/SAAS: arr, mrr, nrr, gross_retention, customers_over_100k
    // RETAIL: same_store_sales, store_count, revenue_per_sqft
    // Include ALL quantitative sector metrics found
  }},

  "guidance": {{
    "next_quarter": {{
      "revenue_low": <number or null>,
      "revenue_high": <number or null>,
      "revenue_midpoint": <number or null>,
      "eps_low": <number or null>,
      "eps_high": <number or null>,
      "other": [{{"metric": "...", "low": <number>, "high": <number>}}]
    }},
    "full_year": {{
      "revenue_low": <number or null>,
      "revenue_high": <number or null>,
      "eps_low": <number or null>,
      "eps_high": <number or null>,
      "other": [{{"metric": "...", "guidance": "..."}}]
    }}
  }},

  "capital_allocation": {{
    "capex": <number or null>,
    "capex_guidance": "...",
    "dividends_per_share": <number or null>,
    "buyback_authorization": <number or null>,
    "buyback_remaining": <number or null>,
    "shares_repurchased": <number or null>
  }},

  "extraction_metadata": {{
    "confidence_score": 0.0-1.0,
    "data_completeness": "high/medium/low",
    "notes": "Any difficulties or notable findings"
  }}
}}

CRITICAL:
- All monetary values in MILLIONS USD unless stated otherwise
- Percentages as numbers (25.5 for 25.5%)
- Use null for unavailable data, never guess
- Be exhaustive - capture ALL financial data
- Output ONLY valid JSON in ENGLISH
"""


class FinancialExtractor:
    """Extracts financial data from Markdown via Claude."""

    def __init__(self, model_name: str = "claude-sonnet-4-20250514"):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model_name = model_name

    def _split_into_chunks(self, markdown_content: str) -> List[str]:
        """Split markdown into chunks by pages, respecting token limits."""
        page_pattern = r'(## Page \d+)'
        parts = re.split(page_pattern, markdown_content)

        pages = []
        current_header = ""
        for part in parts:
            if re.match(page_pattern, part):
                current_header = part
            elif current_header:
                pages.append(current_header + "\n" + part)
                current_header = ""
            elif part.strip():
                pages.insert(0, part)

        if len(pages) <= 1:
            return self._split_by_size(markdown_content)

        chunks = []
        current_chunk = ""

        for page in pages:
            if len(current_chunk) + len(page) < MAX_CHUNK_CHARS:
                current_chunk += page
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = page

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _split_by_size(self, content: str) -> List[str]:
        """Split by size if no pages detected."""
        chunks = []
        paragraphs = content.split('\n\n')
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) < MAX_CHUNK_CHARS:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para + "\n\n"

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _merge_extractions(self, extractions: List[dict]) -> dict:
        """Merge financial extractions from multiple chunks."""
        if not extractions:
            return {}
        if len(extractions) == 1:
            return extractions[0]

        merged = extractions[0].copy()

        for ext in extractions[1:]:
            # Merge company_info (take first complete)
            if not merged.get('company_info', {}).get('name') and ext.get('company_info'):
                merged['company_info'] = ext['company_info']

            # Merge financial sections (take non-null values)
            for section in ['income_statement', 'balance_sheet', 'cash_flow', 'capital_allocation']:
                if ext.get(section):
                    if section not in merged:
                        merged[section] = {}
                    for key, value in ext[section].items():
                        if value is not None and merged[section].get(key) is None:
                            merged[section][key] = value

            # Merge lists
            for section in ['revenue_breakdown']:
                if ext.get(section):
                    if section not in merged:
                        merged[section] = {}
                    for key in ['by_segment', 'by_geography', 'by_product']:
                        if ext[section].get(key):
                            if key not in merged[section]:
                                merged[section][key] = []
                            existing = {json.dumps(x, sort_keys=True) for x in merged[section][key]}
                            for item in ext[section][key]:
                                if json.dumps(item, sort_keys=True) not in existing:
                                    merged[section][key].append(item)

            # Merge sector_specific
            if ext.get('sector_specific'):
                if 'sector_specific' not in merged:
                    merged['sector_specific'] = {}
                for key, value in ext['sector_specific'].items():
                    if value is not None and merged['sector_specific'].get(key) is None:
                        merged['sector_specific'][key] = value

            # Merge operational_metrics
            if ext.get('operational_metrics'):
                if 'operational_metrics' not in merged:
                    merged['operational_metrics'] = {}
                for key, value in ext['operational_metrics'].items():
                    if key == 'other_kpis' and value:
                        if 'other_kpis' not in merged['operational_metrics']:
                            merged['operational_metrics']['other_kpis'] = []
                        existing = {json.dumps(x, sort_keys=True) for x in merged['operational_metrics']['other_kpis']}
                        for item in value:
                            if json.dumps(item, sort_keys=True) not in existing:
                                merged['operational_metrics']['other_kpis'].append(item)
                    elif value and not merged['operational_metrics'].get(key):
                        merged['operational_metrics'][key] = value

        return merged

    def _extract_single_chunk(self, markdown_content: str, chunk_info: str = "") -> dict:
        """Extract financial data from a single chunk."""
        prompt = FINANCIAL_EXTRACTION_PROMPT.format(markdown_content=markdown_content)
        if chunk_info:
            prompt = f"[{chunk_info}]\n\n" + prompt

        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=8192,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )

        try:
            text = response.content[0].text.strip()
            # Extract JSON from response
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text)
        except json.JSONDecodeError as e:
            return {"error": f"JSON parsing error: {e}", "raw_response": text[:500]}

    def extract(self, markdown_content: str, source_file: str = "") -> dict:
        """
        Extract ALL financial data from markdown.

        Args:
            markdown_content: Markdown content from PDF
            source_file: Source file name for metadata

        Returns:
            Dict with all financial data
        """
        if len(markdown_content) > MAX_CHUNK_CHARS:
            chunks = self._split_into_chunks(markdown_content)
            print(f"    [Financial] Large doc ({len(markdown_content):,} chars) -> {len(chunks)} chunks")

            extractions = []
            for i, chunk in enumerate(chunks, 1):
                print(f"    [Financial] Extracting chunk {i}/{len(chunks)}...")
                extraction = self._extract_single_chunk(chunk, f"Part {i}/{len(chunks)}")

                if "error" not in extraction:
                    extractions.append(extraction)
                else:
                    print(f"      Warning: {extraction.get('error', 'Unknown error')}")

            if not extractions:
                return {"error": "No chunks extracted", "_source_file": source_file}

            print(f"    [Financial] Merging {len(extractions)} extractions...")
            merged = self._merge_extractions(extractions)
            merged["_extraction_type"] = "financial"
            merged["_model"] = self.model_name
            merged["_source_file"] = source_file
            return merged

        data = self._extract_single_chunk(markdown_content)

        if "error" in data:
            data["_source_file"] = source_file
            return data

        data["_extraction_type"] = "financial"
        data["_model"] = self.model_name
        data["_source_file"] = source_file
        return data


def extract_financials(markdown_content: str, source_file: str = "") -> dict:
    """Utility function to extract financial data."""
    extractor = FinancialExtractor()
    return extractor.extract(markdown_content, source_file)
