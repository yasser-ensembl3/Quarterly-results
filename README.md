# Quarterly Financials

A full-stack application for comparing quarterly financial results from e-commerce, crypto, and fintech companies. Includes a Python CLI for data extraction and a modern Next.js web dashboard.

## Features

- **Google Drive Sync**: Automatically download quarterly reports from Google Drive
- **Multi-format Extraction**: Extract financial data from PDF, Markdown, and image files
- **AI-Powered Analysis**: Uses OpenAI + Claude to extract and validate structured financial metrics
- **Web Dashboard**: Modern Next.js interface for visualizing and comparing data
- **Company Comparison**: Compare metrics across multiple companies and quarters
- **Data Export**: Export data to CSV or JSON formats
- **SQLite Storage**: Persistent local database for financial data

## Supported Company Types

- **Crypto**: Coinbase, Circle (trading volume, assets on platform, stablecoin metrics)
- **E-commerce**: Amazon, Shopify, Etsy, eBay, Wayfair (GMV, orders, AWS/advertising revenue)
- **Tech**: NVIDIA, Constellation Software (AI revenue, data center metrics)
- **Retail**: LVMH, YETI, FIGS (segment breakdown, international sales)
- **Fintech**: Circle (stablecoin metrics, reserve income)

## Project Structure

```
quarterly-financials/
├── src/                    # Python backend
│   ├── agents/             # AI extraction agents (OpenAI + Claude)
│   ├── cli/                # Typer CLI commands
│   ├── database/           # SQLAlchemy models and CRUD
│   ├── extractors/         # File extractors (PDF, Markdown, Image)
│   ├── gdrive/             # Google Drive sync
│   ├── models/             # Pydantic data models
│   └── parsers/            # Data normalization
├── web/                    # Next.js frontend
│   ├── app/                # App Router pages
│   │   ├── page.tsx        # Dashboard
│   │   ├── company/[slug]/ # Company detail page
│   │   └── compare/        # Comparison tool
│   ├── components/         # React components
│   ├── lib/                # Utilities and data loader
│   └── data/companies/     # JSON data files
├── data/
│   ├── db/                 # SQLite database
│   ├── raw/                # Downloaded source files
│   └── processed/          # Processed JSON/MD results
├── tests/                  # Test suite
└── pyproject.toml          # Python project config
```

## Web Dashboard

The web interface provides a modern dashboard for exploring financial data.

### Pages

1. **Dashboard** (`/`)
   - Overview of all 12 companies with key metrics
   - Revenue comparison bar chart
   - Filter by company type (crypto, ecommerce, tech, etc.)
   - Sort by revenue, growth, margin, or name

2. **Company Detail** (`/company/[ticker]`)
   - Complete financial breakdown (Income Statement, Balance Sheet)
   - Revenue segments pie chart
   - Investment thesis and key highlights
   - Guidance and management commentary
   - Key positives and concerns
   - Notable quotes from earnings calls

3. **Compare** (`/compare`)
   - Side-by-side comparison of 2-4 companies
   - Revenue, growth, and margin charts
   - Detailed comparison table
   - Investment thesis comparison

### Running the Web App

```bash
cd web
npm install
npm run dev
```

Open http://localhost:3000

### Deploying to Vercel

```bash
cd web
npx vercel
```

Or connect your GitHub repository to Vercel for automatic deployments.

## CLI Usage

### Prerequisites

- Python 3.11+
- Google Cloud project with Drive API enabled
- OpenAI API key
- Anthropic API key (for Claude validation)

### Installation

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

### Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Configure the `.env` file:
   ```env
   # Google Drive
   GDRIVE_CREDENTIALS_PATH=credentials.json
   GDRIVE_TOKEN_PATH=token.json
   GDRIVE_ROOT_FOLDER_ID=your_folder_id

   # Database
   DATABASE_URL=sqlite:///data/db/financials.db

   # AI APIs
   OPENAI_API_KEY=your_openai_key
   ANTHROPIC_API_KEY=your_anthropic_key
   ```

3. Set up Google Drive API:
   - Create a project on [Google Cloud Console](https://console.cloud.google.com)
   - Enable the Google Drive API
   - Create OAuth 2.0 credentials
   - Download `credentials.json` to the project root

### CLI Commands

```bash
# Initialize database
qf init

# Sync files from Google Drive
qf sync
qf sync --folder <folder_id>

# Add companies
qf add-company "Coinbase" --type crypto --ticker COIN
qf add-company "Amazon" --type ecommerce --ticker AMZN

# Extract data from files
qf extract path/to/file.pdf
qf extract data/raw/ --verbose

# View status
qf status

# List downloaded files
qf list

# Compare companies
qf compare "Coinbase" "Circle" --metric revenue

# Export data
qf export --output financials.csv --format csv
qf export --output financials.json --format json
```

## Data Pipeline

1. **Sync**: Download PDF reports from Google Drive
2. **Extract**: Convert PDFs to markdown, extract data with OpenAI
3. **Validate**: Review extracted data with Claude
4. **Normalize**: Standardize metrics to common schema
5. **Export**: Generate JSON and Markdown reports

## Data Models

### Core Financials (All Companies)
- Revenue, Gross Profit, Operating Income, Net Income
- Margins (Gross, Operating, Net)
- EPS (Basic and Diluted)
- Year-over-Year and Quarter-over-Quarter growth
- Free Cash Flow, Balance Sheet metrics
- Guidance and outlook

### Sector-Specific Metrics

**Crypto**
- Trading Volume, Transaction Revenue
- Assets on Platform, Custody Assets
- Stablecoin Market Cap, Monthly Transacting Users

**E-commerce**
- GMV, Orders, Average Order Value
- Active Customers, Prime Members
- AWS Revenue, Advertising Revenue

**Tech**
- Data Center Revenue, AI Revenue
- Gaming Revenue, Automotive Revenue

## Current Companies (Q3 2025)

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

## Google Drive Folder Structure

```
Root Folder/
├── Q3 2025/
│   ├── Coinbase/
│   │   ├── Q3-25-Shareholder-Letter.pdf
│   │   ├── Q3-25-Earnings-Call-Transcript.pdf
│   │   ├── coinbase_q3_2025.json      # Generated
│   │   └── coinbase_q3_2025.md        # Generated
│   ├── Amazon/
│   │   └── ...
│   └── ...
└── Q4 2025/
    └── ...
```

## Tech Stack

**Backend (Python)**
- Typer (CLI)
- SQLAlchemy (Database)
- pdfplumber (PDF extraction)
- OpenAI API (Data extraction)
- Anthropic API (Validation)

**Frontend (Next.js)**
- Next.js 14 (App Router)
- Tailwind CSS
- Recharts (Charts)
- Lucide React (Icons)

## License

MIT
