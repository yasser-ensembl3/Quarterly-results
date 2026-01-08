"""Claude agent for STRATEGIC/QUALITATIVE insights extraction from Markdown."""

from __future__ import annotations

import json
import os
import re
from typing import List

import anthropic

# Token limit for chunking
MAX_CHUNK_CHARS = 80000

STRATEGIC_EXTRACTION_PROMPT = """You are a senior investment analyst specializing in qualitative analysis and strategic assessment. Your task is to extract ALL STRATEGIC AND QUALITATIVE INSIGHTS from this quarterly earnings document.

DOCUMENT:
{markdown_content}

---

FOCUS EXCLUSIVELY ON STRATEGIC/QUALITATIVE DATA:
- Management commentary and vision
- Strategic initiatives and their progress
- Competitive positioning and market dynamics
- Risks, challenges, and how management addresses them
- Acquisitions, partnerships, and key deals
- Product launches and innovation
- Industry trends and market opportunities
- Notable quotes from executives
- Key takeaways for investors

DO NOT EXTRACT:
- Detailed financial numbers (that's for another agent)
- Revenue breakdowns with specific figures
- Balance sheet data
- Numerical guidance

Return a JSON with this structure:

{{
  "company_info": {{
    "name": "Full company name",
    "ticker": "SYMBOL",
    "quarter": "Q3",
    "year": 2025
  }},

  "executive_summary": {{
    "one_liner": "One sentence summary of the quarter",
    "management_tone": "optimistic/cautious/neutral/defensive",
    "key_narrative": "2-3 sentence summary of management's main message"
  }},

  "strategic_initiatives": [
    {{
      "initiative": "Name/description of initiative",
      "status": "launched/in_progress/planned/completed",
      "progress": "Details on progress made",
      "expected_impact": "Expected business impact",
      "timeline": "Any mentioned timeline"
    }}
  ],

  "product_and_innovation": {{
    "new_launches": [
      {{
        "product": "Product/service name",
        "description": "What it is",
        "target_market": "Who it's for",
        "competitive_advantage": "Why it matters",
        "reception": "Market/customer reception if mentioned"
      }}
    ],
    "pipeline": [
      {{
        "product": "Upcoming product",
        "expected_launch": "Timeline",
        "details": "Any details shared"
      }}
    ],
    "r_and_d_focus": "Key areas of R&D investment and focus"
  }},

  "competitive_landscape": {{
    "market_position": "Company's stated or implied market position",
    "competitive_advantages": [
      "Advantage 1",
      "Advantage 2"
    ],
    "competitive_threats": [
      "Threat or competitor mentioned"
    ],
    "market_share_commentary": "Any comments on market share",
    "industry_trends": [
      {{
        "trend": "Industry trend",
        "company_positioning": "How company is positioned for this"
      }}
    ]
  }},

  "partnerships_and_ma": {{
    "acquisitions": [
      {{
        "target": "Company/asset acquired",
        "rationale": "Strategic rationale",
        "status": "completed/pending/announced",
        "expected_synergies": "Expected benefits"
      }}
    ],
    "partnerships": [
      {{
        "partner": "Partner name",
        "nature": "Type of partnership",
        "significance": "Why it matters"
      }}
    ],
    "divestitures": [
      {{
        "asset": "What was sold/discontinued",
        "rationale": "Why"
      }}
    ]
  }},

  "risks_and_challenges": [
    {{
      "risk": "Risk description",
      "category": "regulatory/competitive/operational/macro/execution/other",
      "severity": "high/medium/low",
      "management_response": "How management is addressing it",
      "mitigation": "Specific mitigation strategies"
    }}
  ],

  "regulatory_and_legal": {{
    "ongoing_matters": [
      {{
        "matter": "Description",
        "status": "Status",
        "potential_impact": "Impact"
      }}
    ],
    "regulatory_environment": "Commentary on regulatory landscape",
    "compliance_initiatives": "Any compliance efforts mentioned"
  }},

  "management_commentary": {{
    "ceo_message": "Key points from CEO",
    "cfo_message": "Key points from CFO",
    "outlook_sentiment": "How management views the future",
    "priorities": [
      "Priority 1",
      "Priority 2"
    ]
  }},

  "notable_quotes": [
    {{
      "speaker": "Name, Title",
      "quote": "Exact or near-exact quote",
      "context": "What they were discussing",
      "significance": "Why this quote matters"
    }}
  ],

  "investor_highlights": {{
    "bull_case": [
      "Reason to be bullish 1",
      "Reason to be bullish 2"
    ],
    "bear_case": [
      "Reason for concern 1",
      "Reason for concern 2"
    ],
    "key_questions": [
      "Important question for investors to monitor"
    ],
    "catalysts": [
      {{
        "catalyst": "Upcoming catalyst",
        "timeline": "When",
        "potential_impact": "Impact"
      }}
    ]
  }},

  "esg_and_sustainability": {{
    "environmental": "Environmental initiatives or metrics",
    "social": "Social initiatives, workforce, diversity",
    "governance": "Governance updates",
    "commitments": [
      "ESG commitment or target"
    ]
  }},

  "key_takeaways": [
    "Most important takeaway 1 for investors",
    "Most important takeaway 2",
    "Most important takeaway 3",
    "Most important takeaway 4",
    "Most important takeaway 5"
  ],

  "extraction_metadata": {{
    "confidence_score": 0.0-1.0,
    "richness": "high/medium/low (how much qualitative content was available)",
    "document_type": "earnings_release/10Q/transcript/presentation/shareholder_letter",
    "notes": "Any observations about the document"
  }}
}}

CRITICAL:
- Focus on QUALITATIVE insights, not numbers
- Capture management's tone and narrative
- Be thorough - extract ALL strategic information
- Include direct quotes when impactful
- Output ONLY valid JSON in ENGLISH
"""


class StrategicExtractor:
    """Extracts strategic/qualitative insights from Markdown via Claude."""

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
        """Merge strategic extractions from multiple chunks."""
        if not extractions:
            return {}
        if len(extractions) == 1:
            return extractions[0]

        merged = extractions[0].copy()

        for ext in extractions[1:]:
            # Merge company_info
            if not merged.get('company_info', {}).get('name') and ext.get('company_info'):
                merged['company_info'] = ext['company_info']

            # Merge executive_summary (prefer more detailed)
            if ext.get('executive_summary'):
                if 'executive_summary' not in merged:
                    merged['executive_summary'] = ext['executive_summary']
                else:
                    for key in ['one_liner', 'key_narrative']:
                        if ext['executive_summary'].get(key) and len(ext['executive_summary'].get(key, '')) > len(merged['executive_summary'].get(key, '')):
                            merged['executive_summary'][key] = ext['executive_summary'][key]

            # Merge lists (strategic_initiatives, notable_quotes, etc.)
            list_fields = [
                'strategic_initiatives',
                'risks_and_challenges',
                'notable_quotes',
                'key_takeaways'
            ]
            for field in list_fields:
                if ext.get(field):
                    if field not in merged:
                        merged[field] = []
                    existing = {json.dumps(x, sort_keys=True) if isinstance(x, dict) else x for x in merged[field]}
                    for item in ext[field]:
                        item_key = json.dumps(item, sort_keys=True) if isinstance(item, dict) else item
                        if item_key not in existing:
                            merged[field].append(item)

            # Merge nested lists
            nested_lists = [
                ('product_and_innovation', 'new_launches'),
                ('product_and_innovation', 'pipeline'),
                ('partnerships_and_ma', 'acquisitions'),
                ('partnerships_and_ma', 'partnerships'),
                ('partnerships_and_ma', 'divestitures'),
                ('competitive_landscape', 'competitive_advantages'),
                ('competitive_landscape', 'competitive_threats'),
                ('competitive_landscape', 'industry_trends'),
                ('investor_highlights', 'bull_case'),
                ('investor_highlights', 'bear_case'),
                ('investor_highlights', 'key_questions'),
                ('investor_highlights', 'catalysts'),
                ('regulatory_and_legal', 'ongoing_matters'),
                ('esg_and_sustainability', 'commitments'),
                ('management_commentary', 'priorities'),
            ]

            for parent, child in nested_lists:
                if ext.get(parent, {}).get(child):
                    if parent not in merged:
                        merged[parent] = {}
                    if child not in merged[parent]:
                        merged[parent][child] = []
                    existing = {json.dumps(x, sort_keys=True) if isinstance(x, dict) else x for x in merged[parent][child]}
                    for item in ext[parent][child]:
                        item_key = json.dumps(item, sort_keys=True) if isinstance(item, dict) else item
                        if item_key not in existing:
                            merged[parent][child].append(item)

            # Merge simple nested strings
            string_fields = [
                ('competitive_landscape', 'market_position'),
                ('competitive_landscape', 'market_share_commentary'),
                ('product_and_innovation', 'r_and_d_focus'),
                ('regulatory_and_legal', 'regulatory_environment'),
                ('regulatory_and_legal', 'compliance_initiatives'),
                ('management_commentary', 'ceo_message'),
                ('management_commentary', 'cfo_message'),
                ('management_commentary', 'outlook_sentiment'),
                ('esg_and_sustainability', 'environmental'),
                ('esg_and_sustainability', 'social'),
                ('esg_and_sustainability', 'governance'),
            ]

            for parent, child in string_fields:
                if ext.get(parent, {}).get(child):
                    if parent not in merged:
                        merged[parent] = {}
                    if not merged[parent].get(child):
                        merged[parent][child] = ext[parent][child]

        return merged

    def _extract_single_chunk(self, markdown_content: str, chunk_info: str = "") -> dict:
        """Extract strategic insights from a single chunk."""
        prompt = STRATEGIC_EXTRACTION_PROMPT.format(markdown_content=markdown_content)
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
        Extract ALL strategic/qualitative insights from markdown.

        Args:
            markdown_content: Markdown content from PDF
            source_file: Source file name for metadata

        Returns:
            Dict with all strategic insights
        """
        if len(markdown_content) > MAX_CHUNK_CHARS:
            chunks = self._split_into_chunks(markdown_content)
            print(f"    [Strategic] Large doc ({len(markdown_content):,} chars) -> {len(chunks)} chunks")

            extractions = []
            for i, chunk in enumerate(chunks, 1):
                print(f"    [Strategic] Extracting chunk {i}/{len(chunks)}...")
                extraction = self._extract_single_chunk(chunk, f"Part {i}/{len(chunks)}")

                if "error" not in extraction:
                    extractions.append(extraction)
                else:
                    print(f"      Warning: {extraction.get('error', 'Unknown error')}")

            if not extractions:
                return {"error": "No chunks extracted", "_source_file": source_file}

            print(f"    [Strategic] Merging {len(extractions)} extractions...")
            merged = self._merge_extractions(extractions)
            merged["_extraction_type"] = "strategic"
            merged["_model"] = self.model_name
            merged["_source_file"] = source_file
            return merged

        data = self._extract_single_chunk(markdown_content)

        if "error" in data:
            data["_source_file"] = source_file
            return data

        data["_extraction_type"] = "strategic"
        data["_model"] = self.model_name
        data["_source_file"] = source_file
        return data


def extract_strategic(markdown_content: str, source_file: str = "") -> dict:
    """Utility function to extract strategic insights."""
    extractor = StrategicExtractor()
    return extractor.extract(markdown_content, source_file)
