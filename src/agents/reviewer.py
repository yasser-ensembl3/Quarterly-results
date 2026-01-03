"""Claude agent for validation and normalization of extracted data."""

from __future__ import annotations

import json
import os

import anthropic

REVIEW_PROMPT = """You are a senior financial analyst with deep expertise in data validation. Your role is to validate, correct, and enrich data extracted from a quarterly earnings report.

CRITICAL: You MUST respond ONLY in English. All output, analysis, and commentary must be in English.

EXTRACTED DATA:
{extracted_data}

CRITICAL INSTRUCTIONS:

1. FINANCIAL VALIDATION:
   - Verify mathematical consistency (net_income <= gross_profit <= revenue)
   - Verify margins are consistent with absolute figures
   - Verify growth percentages are plausible
   - Ensure all monetary values are in millions USD

2. LOGICAL VALIDATION:
   - Dates and quarters are consistent
   - Segment/region names are standardized
   - Sector metrics match the company type

3. ENRICHMENT:
   - Calculate missing metrics where possible (e.g., net_margin = net_income/revenue)
   - Add context to raw data
   - Identify key highlights for investors

4. ALERTS:
   - Flag potential anomalies
   - Identify important missing data
   - Note inconsistencies with industry practices

Return a JSON with this structure (ALL OUTPUT MUST BE IN ENGLISH):

{{
  "validated_data": {{
    "company_info": {{
      "name": "...",
      "ticker": "...",
      "quarter": "...",
      "year": ...,
      "company_type": "crypto/ecommerce/tech/fintech/other",
      "report_date": "..."
    }},

    "financial_highlights": {{
      "revenue": {{"value": <number>, "unit": "millions_usd", "yoy_change_pct": <number or null>}},
      "net_income": {{"value": <number>, "unit": "millions_usd", "yoy_change_pct": <number or null>}},
      "gross_profit": {{"value": <number or null>, "margin_pct": <number or null>}},
      "operating_income": {{"value": <number or null>, "margin_pct": <number or null>}},
      "ebitda": {{"value": <number or null>, "adjusted": <number or null>}},
      "eps": {{"basic": <number or null>, "diluted": <number or null>}},
      "free_cash_flow": <number or null>,
      "cash_position": <number or null>,
      "total_debt": <number or null>
    }},

    "revenue_breakdown": {{
      "by_segment": [...],
      "by_geography": [...],
      "by_product": [...]
    }},

    "operational_metrics": {{
      "employees": {{}},
      "customers": {{}},
      "users": {{}},
      "other_kpis": [...]
    }},

    "sector_specific_metrics": {{}},

    "guidance_and_outlook": {{
      "next_quarter": {{}},
      "full_year": {{}},
      "management_commentary": "..."
    }},

    "strategic_updates": {{
      "acquisitions": [...],
      "partnerships": [...],
      "product_launches": [...],
      "strategic_initiatives": [...]
    }},

    "risks_and_challenges": [...],

    "competitive_position": {{}},

    "capital_allocation": {{}},

    "notable_quotes": [...],

    "key_takeaways": [...]
  }},

  "validation": {{
    "is_valid": true/false,
    "confidence_score": 0.0-1.0,
    "data_completeness": "high/medium/low",
    "corrections_made": [
      {{"field": "...", "old_value": "...", "new_value": "...", "reason": "..."}}
    ],
    "warnings": [
      {{"field": "...", "message": "...", "severity": "low/medium/high"}}
    ],
    "missing_critical_data": ["..."]
  }},

  "analysis_summary": {{
    "financial_health": "strong/stable/weak/unknown",
    "growth_trajectory": "accelerating/stable/decelerating/unknown",
    "key_positives": ["...", "..."],
    "key_concerns": ["...", "..."],
    "investment_highlights": ["...", "...", "..."]
  }}
}}

IMPORTANT: ALL OUTPUT MUST BE IN ENGLISH.
"""

NORMALIZE_PROMPT = """You are an expert in financial data normalization for a comparative analysis platform. Your role is to transform validated data into a uniform format comparable across all companies.

CRITICAL: You MUST respond ONLY in English. All output, analysis, and commentary must be in English.

VALIDATED DATA:
{validated_data}

OBJECTIVE: Create a normalized data structure that allows easy comparison of different companies (crypto, e-commerce, tech, fintech) on the same criteria.

NORMALIZATION INSTRUCTIONS:

1. MONETARY STANDARDIZATION:
   - All monetary values in millions USD
   - Convert if necessary (billions -> millions)

2. PERCENTAGE STANDARDIZATION:
   - All percentages as decimal numbers (25.5 for 25.5%, not 0.255)

3. NAME STANDARDIZATION:
   - Regions: "North America", "EMEA", "APAC", "LATAM", "International"
   - Segments: use consistent and comparable names

4. ENRICHMENT:
   - Calculate all missing margins
   - Calculate standard financial ratios
   - Add useful derived metrics

5. QUALITY:
   - Keep ALL important qualitative information
   - Do not remove strategic insights

Return a normalized JSON with this COMPLETE structure (ALL OUTPUT MUST BE IN ENGLISH):

{{
  "id": {{
    "company": "Full company name",
    "ticker": "SYMBOL",
    "quarter": "Q3",
    "year": 2025,
    "company_type": "crypto/ecommerce/tech/fintech/retail/other",
    "report_date": "YYYY-MM-DD"
  }},

  "financials": {{
    "income_statement": {{
      "revenue": <number>,
      "revenue_yoy_pct": <number or null>,
      "revenue_qoq_pct": <number or null>,
      "gross_profit": <number or null>,
      "gross_margin_pct": <number or null>,
      "operating_income": <number or null>,
      "operating_margin_pct": <number or null>,
      "net_income": <number>,
      "net_margin_pct": <number or null>,
      "ebitda": <number or null>,
      "adjusted_ebitda": <number or null>
    }},
    "per_share": {{
      "eps_basic": <number or null>,
      "eps_diluted": <number or null>
    }},
    "cash_flow": {{
      "operating_cash_flow": <number or null>,
      "free_cash_flow": <number or null>,
      "capex": <number or null>
    }},
    "balance_sheet": {{
      "cash_and_equivalents": <number or null>,
      "total_debt": <number or null>,
      "net_cash": <number or null>
    }}
  }},

  "segments": {{
    "by_business": [
      {{"name": "...", "revenue": <number>, "pct_of_total": <number>, "yoy_pct": <number or null>}}
    ],
    "by_geography": [
      {{"region": "...", "revenue": <number>, "pct_of_total": <number>}}
    ]
  }},

  "operations": {{
    "employees": <number or null>,
    "employee_change_qoq": <number or null>,
    "key_metrics": [
      {{"name": "...", "value": "...", "unit": "...", "context": "..."}}
    ]
  }},

  "sector_specific": {{
    // For CRYPTO:
    "trading_volume": <number or null>,
    "transaction_revenue": <number or null>,
    "assets_on_platform": <number or null>,
    "monthly_transacting_users": <number or null>,
    "verified_users": <number or null>,
    "stablecoin_market_cap": <number or null>,

    // For E-COMMERCE:
    "gmv": <number or null>,
    "orders": <number or null>,
    "aov": <number or null>,
    "prime_members": <number or null>,
    "active_sellers": <number or null>,

    // For TECH/SAAS:
    "arr": <number or null>,
    "mrr": <number or null>,
    "net_revenue_retention": <number or null>,
    "churn_rate": <number or null>,
    "dau_mau": <number or null>
  }},

  "guidance": {{
    "q_plus_1": {{
      "revenue_low": <number or null>,
      "revenue_high": <number or null>,
      "revenue_midpoint": <number or null>,
      "other": [...]
    }},
    "full_year": {{
      "revenue_guidance": "...",
      "other": [...]
    }},
    "commentary": "Summary of key management comments"
  }},

  "strategic": {{
    "acquisitions": [...],
    "partnerships": [...],
    "product_launches": [...],
    "initiatives": [...],
    "risks": [...],
    "competitive_advantages": [...]
  }},

  "highlights": {{
    "key_positives": ["...", "...", "..."],
    "key_concerns": ["...", "..."],
    "notable_quotes": [
      {{"speaker": "...", "quote": "..."}}
    ],
    "investment_thesis": "2-3 sentence summary for investors"
  }},

  "metadata": {{
    "data_quality_score": 0.0-1.0,
    "completeness": "high/medium/low",
    "normalized_at": "ISO timestamp",
    "notes": "..."
  }}
}}

IMPORTANT: Do not simplify the data. The goal is to have ALL information relevant to an investor, in a standardized and comparable format. ALL OUTPUT MUST BE IN ENGLISH.
"""


class ClaudeReviewer:
    """Validates extracted data via Claude."""

    def __init__(self, model_name: str = "claude-sonnet-4-20250514"):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model_name

    def review(self, extracted_data: dict) -> dict:
        """Validate and correct extracted data."""
        prompt = REVIEW_PROMPT.format(
            extracted_data=json.dumps(extracted_data, indent=2, ensure_ascii=False)
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            text = response.content[0].text.strip()
            # Clean markdown
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            text = text.strip()
            # Find valid JSON (between { and })
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                text = text[start:end]
            data = json.loads(text)
            data["_review_model"] = self.model
            return data
        except json.JSONDecodeError as e:
            return {"error": f"JSON parse error: {e}", "raw": response.content[0].text}


class ClaudeNormalizer:
    """Normalizes validated data via Claude."""

    def __init__(self, model_name: str = "claude-sonnet-4-20250514"):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model_name

    def normalize(self, validated_data: dict) -> dict:
        """Normalize data for comparison."""
        prompt = NORMALIZE_PROMPT.format(
            validated_data=json.dumps(validated_data, indent=2, ensure_ascii=False)
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            text = response.content[0].text.strip()
            # Clean markdown
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            text = text.strip()
            # Find valid JSON (between { and })
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                text = text[start:end]
            data = json.loads(text)
            data["_normalize_model"] = self.model
            return data
        except json.JSONDecodeError as e:
            return {"error": f"JSON parse error: {e}", "raw": response.content[0].text}


def review_extraction(extracted_data: dict) -> dict:
    """Utility function to validate data."""
    reviewer = ClaudeReviewer()
    return reviewer.review(extracted_data)


def normalize_data(validated_data: dict) -> dict:
    """Utility function to normalize data."""
    normalizer = ClaudeNormalizer()
    return normalizer.normalize(validated_data)
