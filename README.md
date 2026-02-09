# Quarterly Financials

Analyze and compare quarterly financial results from e-commerce, crypto, and fintech companies. Uses Claude Code for AI-powered extraction and validation, with Python scripts for PDF conversion and Google Drive sync.

## Workflow

```
0. python scripts/00_download_from_drive.py --quarter Q4  # Drive -> data/raw/
1. python scripts/01_convert_pdfs.py --quarter Q4          # PDF -> Markdown
2. Claude Code: read data/markdown/Q4/, use prompts/       # Extract, validate, format
3. python scripts/05_upload_to_drive.py --quarter Q4       # Upload to Drive
```

### Step 0: Download PDFs from Google Drive
```bash
python scripts/00_download_from_drive.py --quarter Q4                # All companies
python scripts/00_download_from_drive.py --quarter Q4 --company Amazon  # Single company
python scripts/00_download_from_drive.py --quarter Q4 --force        # Re-download all
```
Downloads PDF earnings reports from `Drive/<quarter>/<company>/` into `data/raw/<quarter>/<company>/`. Skips files that already exist locally.

### Step 1: Convert PDFs to Markdown
```bash
python scripts/01_convert_pdfs.py --quarter Q4
```
Converts PDF earnings reports in `data/raw/<quarter>/` to Markdown files in `data/markdown/<quarter>/`. Uses LlamaParse (with pdfplumber fallback).

### Step 2: Extract & Analyze (Claude Code)
Use Claude Code to read the markdown files and apply the prompts in `prompts/`:

1. **`prompts/financial_extraction.md`** - Extract financial data (income statement, balance sheet, cash flow, KPIs)
2. **`prompts/strategic_extraction.md`** - Extract strategic insights (initiatives, risks, competitive position)
3. **`prompts/validation.md`** - Validate and cross-check extracted data
4. **`prompts/normalization.md`** - Normalize data into comparable format across companies
5. **`prompts/report_formatting.md`** - Format into professional Markdown reports

Output per company: `{company}_financial.json`, `{company}_strategic.json`, `{company}_financial.md`, `{company}_strategic.md` in `data/insights/<quarter>/<company>/`.

### Step 3: Upload to Google Drive
```bash
python scripts/05_upload_to_drive.py --quarter Q4                    # All companies
python scripts/05_upload_to_drive.py --quarter Q4 --company Amazon   # Single company
python scripts/05_upload_to_drive.py --quarter Q4 --insights-only    # Insights only
python scripts/05_upload_to_drive.py --quarter Q4 --markdown-only    # Markdown only
```
Uploads insights (JSON + MD) and/or markdown files to `Drive/<quarter>/<company>/`.

### Pipeline Runner
```bash
python scripts/run_pipeline.py --quarter Q4 --all              # Run steps 0, 1, 3
python scripts/run_pipeline.py --quarter Q4 --steps 0           # Download only
python scripts/run_pipeline.py --quarter Q4 --steps 0,1         # Download + convert
python scripts/run_pipeline.py --quarter Q4 --steps 3           # Upload only
python scripts/run_pipeline.py --quarter Q4 --company Amazon    # Single company
```

## Project Structure

```
quarterly-financials/
├── prompts/                # Claude Code prompts for analysis
│   ├── financial_extraction.md
│   ├── strategic_extraction.md
│   ├── validation.md
│   ├── normalization.md
│   └── report_formatting.md
├── scripts/                # Pipeline scripts
│   ├── 00_download_from_drive.py  # Download PDFs from Drive
│   ├── 01_convert_pdfs.py         # PDF -> Markdown
│   ├── 05_upload_to_drive.py      # Upload results to Drive
│   └── run_pipeline.py            # Pipeline orchestrator
├── src/                    # Python backend
│   ├── agents/             # PDF converter, report generator
│   ├── database/           # SQLAlchemy models and CRUD
│   ├── extractors/         # File extractors (PDF, Markdown, Image)
│   ├── gdrive/             # Google Drive sync
│   ├── models/             # Pydantic data models
│   └── parsers/            # Data normalization
├── data/
│   ├── raw/                # Source PDF files
│   ├── markdown/           # Converted Markdown files
│   └── insights/           # Extracted JSON + formatted reports
└── pyproject.toml
```

## Supported Companies

| Company | Ticker | Type | Revenue | YoY Growth |
|---------|--------|------|---------|------------|
| Amazon | AMZN | ecommerce | $180.2B | +13% |
| LVMH | LVMH | retail | $64.1B | -4% |
| NVIDIA | NVDA | tech | $35.1B | +94% |
| Wayfair | W | ecommerce | $3.1B | +8% |
| Constellation Software | CSI | tech | $2.9B | +16% |
| Shopify | SHOP | ecommerce | $2.8B | +32% |
| eBay | EBAY | ecommerce | $2.8B | +9% |
| Coinbase | COIN | crypto | $1.9B | +55% |
| Circle | CRCL | fintech | $740M | +66% |
| Etsy | ETSY | ecommerce | $678M | +2% |
| YETI | YETI | retail | $488M | +2% |
| FIGS | FIGS | ecommerce | $152M | +8% |

## Prerequisites

- Python 3.11+
- Google Cloud project with Drive API enabled (for upload)

### Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -e .
```

### Configuration

```bash
cp .env.example .env
```

Required in `.env`:
```env
# Google Drive (for download/upload)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REFRESH_TOKEN=your_refresh_token
GDRIVE_ROOT_FOLDER_ID=your_folder_id

# LlamaParse (for PDF conversion)
LLAMA_CLOUD_API_KEY=your_api_key
```

## Tech Stack

- **Python**: pdfplumber (PDF extraction), SQLAlchemy, Pydantic, Typer
- **AI**: Claude Code (extraction, validation, formatting via prompts)
- **Google Drive API**: Download source PDFs and upload results

## License

MIT
