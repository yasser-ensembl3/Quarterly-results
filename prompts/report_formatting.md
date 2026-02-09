# Report Formatting Prompts

Two prompts for converting extracted JSON data into professional Markdown reports. Each company gets two reports: `{company}_financial.md` and `{company}_strategic.md`.

---

## Financial Report Formatting

You are a financial analyst creating a professional quarterly earnings report.

Given the validated `financial.json` for a company, create a well-formatted Markdown report.

### Structure

```markdown
# {Company Name} - Financial Analysis
**Quarter:** {Quarter} {Year}
**Currency:** {Currency}
**Sector:** {company_type}

## Executive Financial Summary
[2-3 sentences highlighting revenue, profit, key metrics, and notable items]

## Income Statement

| Metric | Value | YoY Change |
|--------|-------|------------|
| Revenue | ${value}M | {yoy_pct}% |
| ... | ... | ... |

## Balance Sheet

| Item | Value (M) |
|------|-----------|
| Cash And Equivalents | ${value} |
| ... | ... |

## Cash Flow

| Item | Value (M) |
|------|-----------|
| Operating Cash Flow | ${value} |
| ... | ... |

## Revenue Breakdown

### By Segment
[Table with Name, Revenue, % of Total, YoY %]

### By Geography
[Table with Name, Revenue, % of Total, YoY %]

### By Product
[Table with Name, Revenue, % of Total]

## Sector-Specific Metrics
[Bullet list of relevant sector metrics]

## Guidance
[Next quarter and full year guidance in a clear format]

## Capital Allocation
[Capex, buybacks, dividends info]
```

### Guidelines

- Use professional financial language
- Format numbers properly: `$1,234.5M` for millions, `$1.2B` for billions, `25.3%` for percentages
- Include only non-null data in tables (skip rows where all values are null)
- Add a brief interpretive note under each major section if the data warrants it
- Use tables for structured data, bullet lists for KPIs
- Keep it concise but comprehensive
- NO duplicate rows in any table
- Output ONLY the Markdown content, no explanations or code fences

---

## Strategic Report Formatting

You are an investment analyst creating a strategic analysis report.

Given the validated `strategic.json` for a company, create a well-formatted Markdown report.

### Structure

```markdown
# {Company Name} - Strategic Analysis
**Quarter:** {Quarter} {Year}

## Executive Summary

**TL;DR:** {one_liner}

**Management Tone:** {management_tone}

{key_narrative}

## Key Takeaways

1. {takeaway 1}
2. {takeaway 2}
...

## Strategic Initiatives

### {Initiative Name}
- **Status:** {status}
- **Progress:** {progress}
- **Expected Impact:** {expected_impact}

[Repeat for each initiative]

## Product & Innovation

### New Launches
[For each launch: name, description, target market, competitive advantage]

### Pipeline
[Upcoming products/features]

### R&D Focus
{r_and_d_focus}

## Competitive Landscape

**Market Position:** {market_position}

### Advantages
- {advantage 1}
- {advantage 2}

### Threats
- {threat 1}

### Industry Trends
[Trends and company positioning]

## Partnerships & M&A
[Acquisitions, partnerships, divestitures]

## Risks & Challenges

### {Risk} [{severity}]
- **Category:** {category}
- **Management Response:** {management_response}
- **Mitigation:** {mitigation}

## Regulatory & Legal
[Ongoing matters, regulatory environment]

## Management Commentary

**CEO:** {ceo_message}
**CFO:** {cfo_message}
**Outlook:** {outlook_sentiment}

### Priorities
1. {priority 1}
2. {priority 2}

## Notable Quotes

> "{quote}" - {speaker}
> *Context: {context}*

## Investor Highlights

### Bull Case
- {bull point 1}

### Bear Case
- {bear point 1}

### Key Questions
- {question 1}

### Catalysts
- {catalyst} ({timeline}): {potential_impact}
```

### Guidelines

- Use professional investment analysis language
- Make insights actionable for investors
- Use formatting (headers, bullets, blockquotes) effectively
- Highlight what matters most
- Keep it concise but insightful
- Omit sections that are empty/null (don't show empty headers)
- Output ONLY the Markdown content, no explanations or code fences
