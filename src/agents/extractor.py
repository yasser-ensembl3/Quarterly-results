"""OpenAI agent for COMPLETE data extraction from Markdown."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import List

from openai import OpenAI

# Token limit for chunking (conservative, under 100K)
MAX_CHUNK_CHARS = 80000  # ~20K tokens (4 chars/token average)

EXTRACTION_PROMPT = """You are an expert financial analyst. Analyze this quarterly earnings document and extract ALL information relevant to an investor.

CRITICAL: You MUST respond ONLY in English. All extracted data, quotes, summaries, and commentary must be in English.

DOCUMENT:
{markdown_content}

---

CRITICAL INSTRUCTIONS:
- Extract ABSOLUTELY EVERYTHING relevant to an investor
- Do NOT limit yourself to basic financial metrics
- Capture strategic insights, management commentary, risks, competitive positioning, etc.
- Use exact values from the document
- All monetary amounts in millions USD unless otherwise specified
- All percentages as numbers (25.5 for 25.5%)
- ALL OUTPUT MUST BE IN ENGLISH

Return an EXHAUSTIVE JSON with this structure (add fields if necessary):

{{
  "company_info": {{
    "name": "Full company name",
    "ticker": "SYMBOL",
    "quarter": "Q3",
    "year": 2025,
    "report_date": "report date",
    "currency": "USD"
  }},

  "financial_highlights": {{
    "revenue": {{"value": <number>, "unit": "millions", "yoy_change_pct": <number or null>, "qoq_change_pct": <number or null>}},
    "net_income": {{"value": <number>, "unit": "millions", "yoy_change_pct": <number or null>}},
    "gross_profit": {{"value": <number or null>, "margin_pct": <number or null>}},
    "operating_income": {{"value": <number or null>, "margin_pct": <number or null>}},
    "ebitda": {{"value": <number or null>, "adjusted": <number or null>}},
    "eps": {{"basic": <number or null>, "diluted": <number or null>}},
    "free_cash_flow": <number or null>,
    "cash_and_equivalents": <number or null>,
    "total_debt": <number or null>
  }},

  "revenue_breakdown": {{
    "by_segment": [
      {{"name": "...", "revenue": <number>, "pct_of_total": <number>, "yoy_change_pct": <number or null>}}
    ],
    "by_geography": [
      {{"region": "...", "revenue": <number>, "pct_of_total": <number>}}
    ],
    "by_product": [
      {{"product": "...", "revenue": <number>, "details": "..."}}
    ]
  }},

  "operational_metrics": {{
    "employees": {{"count": <number>, "change_qoq": <number or null>}},
    "customers": {{"total": <number or null>, "active": <number or null>, "new": <number or null>}},
    "users": {{"monthly_active": <number or null>, "transacting": <number or null>, "verified": <number or null>}},
    "other_kpis": [
      {{"name": "...", "value": "...", "context": "..."}}
    ]
  }},

  "sector_specific_metrics": {{
    // For crypto: trading_volume, assets_on_platform, stablecoin_data, etc.
    // For ecommerce: gmv, orders, aov, prime_members, etc.
    // For tech/SaaS: arr, mrr, churn, nrr, etc.
    // Include ALL sector-specific metrics
  }},

  "guidance_and_outlook": {{
    "next_quarter": {{
      "revenue_low": <number or null>,
      "revenue_high": <number or null>,
      "other_guidance": [
        {{"metric": "...", "guidance": "..."}}
      ]
    }},
    "full_year": {{
      "revenue_guidance": "...",
      "other_guidance": "..."
    }},
    "management_commentary": "Key quotes or summary of management's comments"
  }},

  "strategic_updates": {{
    "acquisitions": [
      {{"name": "...", "details": "...", "impact": "..."}}
    ],
    "partnerships": [
      {{"partner": "...", "details": "..."}}
    ],
    "product_launches": [
      {{"product": "...", "details": "...", "impact": "..."}}
    ],
    "strategic_initiatives": [
      {{"initiative": "...", "progress": "...", "expected_impact": "..."}}
    ]
  }},

  "risks_and_challenges": [
    {{"risk": "...", "details": "...", "mitigation": "..."}}
  ],

  "competitive_position": {{
    "market_share": "...",
    "competitive_advantages": ["...", "..."],
    "market_trends": "..."
  }},

  "capital_allocation": {{
    "capex": <number or null>,
    "dividends": <number or null>,
    "buybacks": {{"amount": <number or null>, "shares": <number or null>}},
    "investments": "..."
  }},

  "notable_quotes": [
    {{"speaker": "CEO/CFO/...", "quote": "Important quote"}}
  ],

  "key_takeaways": [
    "Key point 1 for investors",
    "Key point 2",
    "Key point 3"
  ],

  "extraction_metadata": {{
    "confidence_score": 0.0-1.0,
    "data_completeness": "high/medium/low",
    "notes": "Any difficulties or missing information"
  }}
}}

IMPORTANT: Add additional fields if the document contains relevant information not covered by this structure. The goal is to MISS NOTHING important for an investor. ALL OUTPUT MUST BE IN ENGLISH.
"""


class OpenAIExtractor:
    """Extracts ALL relevant data from Markdown via OpenAI."""

    def __init__(self, model_name: str = "gpt-4o"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

    def _split_into_chunks(self, markdown_content: str) -> List[str]:
        """
        Split markdown into chunks by pages, respecting token limits.

        Args:
            markdown_content: Full markdown content

        Returns:
            List of chunks
        """
        # Split by pages (## Page X)
        page_pattern = r'(## Page \d+)'
        parts = re.split(page_pattern, markdown_content)

        # Reconstruct pages (header + content)
        pages = []
        current_header = ""
        for part in parts:
            if re.match(page_pattern, part):
                current_header = part
            elif current_header:
                pages.append(current_header + "\n" + part)
                current_header = ""
            elif part.strip():
                # Content before first page (document title)
                pages.insert(0, part)

        # If no pages detected, split by size
        if len(pages) <= 1:
            return self._split_by_size(markdown_content)

        # Group pages into chunks
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

        # Split by paragraphs
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
        """
        Merge extractions from multiple chunks.

        Args:
            extractions: List of extractions per chunk

        Returns:
            Merged extraction
        """
        if not extractions:
            return {}

        if len(extractions) == 1:
            return extractions[0]

        # Start with first extraction
        merged = extractions[0].copy()

        for ext in extractions[1:]:
            # Merge company_info (take first non-empty)
            if not merged.get('company_info') and ext.get('company_info'):
                merged['company_info'] = ext['company_info']

            # Merge financial_highlights (take non-null values)
            if ext.get('financial_highlights'):
                if 'financial_highlights' not in merged:
                    merged['financial_highlights'] = {}
                for key, value in ext['financial_highlights'].items():
                    if value and not merged['financial_highlights'].get(key):
                        merged['financial_highlights'][key] = value

            # Merge lists (revenue_breakdown, strategic_updates, etc.)
            list_fields = [
                ('revenue_breakdown', 'by_segment'),
                ('revenue_breakdown', 'by_geography'),
                ('revenue_breakdown', 'by_product'),
                ('operational_metrics', 'other_kpis'),
                ('strategic_updates', 'acquisitions'),
                ('strategic_updates', 'partnerships'),
                ('strategic_updates', 'product_launches'),
                ('strategic_updates', 'strategic_initiatives'),
                ('guidance_and_outlook', 'other_guidance'),
            ]

            for parent, child in list_fields:
                if ext.get(parent, {}).get(child):
                    if parent not in merged:
                        merged[parent] = {}
                    if child not in merged[parent]:
                        merged[parent][child] = []
                    # Avoid duplicates
                    existing = [json.dumps(x, sort_keys=True) for x in merged[parent][child]]
                    for item in ext[parent][child]:
                        if json.dumps(item, sort_keys=True) not in existing:
                            merged[parent][child].append(item)

            # Merge simple lists
            simple_lists = ['risks_and_challenges', 'notable_quotes', 'key_takeaways']
            for field in simple_lists:
                if ext.get(field):
                    if field not in merged:
                        merged[field] = []
                    existing = [json.dumps(x, sort_keys=True) if isinstance(x, dict) else x for x in merged[field]]
                    for item in ext[field]:
                        item_key = json.dumps(item, sort_keys=True) if isinstance(item, dict) else item
                        if item_key not in existing:
                            merged[field].append(item)

            # Merge simple dicts
            dict_fields = ['sector_specific_metrics', 'competitive_position', 'capital_allocation']
            for field in dict_fields:
                if ext.get(field):
                    if field not in merged:
                        merged[field] = {}
                    for key, value in ext[field].items():
                        if value and not merged[field].get(key):
                            merged[field][key] = value

        return merged

    def _extract_single_chunk(self, markdown_content: str, chunk_info: str = "") -> dict:
        """Extract data from a single chunk."""
        prompt = EXTRACTION_PROMPT.format(markdown_content=markdown_content)
        if chunk_info:
            prompt = f"[{chunk_info}]\n\n" + prompt

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are an expert financial analyst. Extract ALL information relevant to an investor. Be exhaustive. Respond ONLY in valid JSON and ONLY in English."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=8192,
            response_format={"type": "json_object"},
        )

        try:
            text = response.choices[0].message.content.strip()
            return json.loads(text)
        except json.JSONDecodeError as e:
            return {"error": f"JSON parsing error: {e}"}

    def extract_from_markdown(self, markdown_content: str, source_file: str = "") -> dict:
        """
        Extract ALL relevant information from markdown.
        Automatically uses chunking if content is too large.

        Args:
            markdown_content: Markdown content from PDF
            source_file: Source file name

        Returns:
            Exhaustive dict with all data
        """
        # Check if chunking is needed
        if len(markdown_content) > MAX_CHUNK_CHARS:
            chunks = self._split_into_chunks(markdown_content)
            print(f"    -> Large document ({len(markdown_content):,} chars)")
            print(f"    -> Split into {len(chunks)} chunks")

            extractions = []
            for i, chunk in enumerate(chunks, 1):
                print(f"    -> Extracting chunk {i}/{len(chunks)} ({len(chunk):,} chars)...")
                chunk_info = f"Part {i}/{len(chunks)} of document"
                extraction = self._extract_single_chunk(chunk, chunk_info)

                if "error" not in extraction:
                    extractions.append(extraction)
                else:
                    print(f"      Warning: Chunk {i} error: {extraction['error']}")

            if not extractions:
                return {
                    "error": "No chunks could be extracted",
                    "_source_file": source_file,
                }

            # Merge extractions
            print(f"    -> Merging {len(extractions)} extractions...")
            merged = self._merge_extractions(extractions)
            merged["_extraction_model"] = self.model_name
            merged["_source_file"] = source_file
            merged["_chunking"] = {
                "total_chunks": len(chunks),
                "successful_chunks": len(extractions),
                "original_size": len(markdown_content)
            }
            return merged

        # Simple extraction (short document)
        data = self._extract_single_chunk(markdown_content)

        if "error" in data:
            data["_source_file"] = source_file
            return data

        data["_extraction_model"] = self.model_name
        data["_source_file"] = source_file
        return data


def extract_from_markdown(markdown_content: str, source_file: str = "") -> dict:
    """Utility function to extract data from markdown."""
    extractor = OpenAIExtractor()
    return extractor.extract_from_markdown(markdown_content, source_file)
