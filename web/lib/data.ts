import amazonData from '@/data/companies/amazon_q3_2025.json'
import circleData from '@/data/companies/circle_q3_2025.json'
import coinbaseData from '@/data/companies/coinbase_q3_2025.json'
import constellationData from '@/data/companies/constellation_software_q3_2025.json'
import ebayData from '@/data/companies/ebay_q3_2025.json'
import etsyData from '@/data/companies/etsy_q3_2025.json'
import figsData from '@/data/companies/figs_q3_2025.json'
import lvmhData from '@/data/companies/lvmh_q3_2025.json'
import nvidiaData from '@/data/companies/nvidia_q3_2025.json'
import shopifyData from '@/data/companies/shopify_q3_2025.json'
import wayfairData from '@/data/companies/wayfair_q3_2025.json'
import yetiData from '@/data/companies/yeti_q3_2025.json'

export interface CompanyData {
  id: {
    company: string
    ticker: string
    quarter: string
    year: number
    company_type: string
    report_date: string
  }
  financials: {
    income_statement: {
      revenue: number | null
      revenue_yoy_pct: number | null
      revenue_qoq_pct: number | null
      gross_profit: number | null
      gross_margin_pct: number | null
      operating_income: number | null
      operating_margin_pct: number | null
      net_income: number | null
      net_margin_pct: number | null
      ebitda: number | null
      adjusted_ebitda: number | null
    }
    per_share: {
      eps_basic: number | null
      eps_diluted: number | null
    }
    cash_flow: {
      operating_cash_flow: number | null
      free_cash_flow: number | null
      capex: number | null
    }
    balance_sheet: {
      cash_and_equivalents: number | null
      total_debt: number | null
      net_cash: number | null
    }
  }
  segments: {
    by_business: Array<{
      name: string
      revenue: number
      pct_of_total: number
      yoy_pct: number | null
    }>
    by_geography: Array<{
      region: string
      revenue: number
      pct_of_total: number
    }>
  }
  operations: {
    employees: number | null
    employee_change_qoq: number | null
    key_metrics: Array<{
      name: string
      value: string
      unit: string
      context: string
    }>
  }
  sector_specific: Record<string, unknown>
  guidance: {
    q_plus_1: {
      revenue_low: number | null
      revenue_high: number | null
      revenue_midpoint: number | null
      other: unknown[]
    }
    full_year: {
      revenue_guidance: number | string | null
      other: unknown[]
    }
    commentary: string
  }
  strategic: {
    acquisitions: unknown[]
    partnerships: unknown[]
    product_launches: unknown[]
    initiatives: unknown[]
    risks: unknown[]
    competitive_advantages: string[]
  }
  highlights: {
    key_positives: string[]
    key_concerns: string[]
    notable_quotes: Array<{
      speaker: string
      quote: string
    }>
    investment_thesis: string
  }
  metadata: {
    data_quality_score: number
    completeness: string
    normalized_at: string
    notes: string
  }
}

const allCompanies: CompanyData[] = [
  amazonData as unknown as CompanyData,
  circleData as unknown as CompanyData,
  coinbaseData as unknown as CompanyData,
  constellationData as unknown as CompanyData,
  ebayData as unknown as CompanyData,
  etsyData as unknown as CompanyData,
  figsData as unknown as CompanyData,
  lvmhData as unknown as CompanyData,
  nvidiaData as unknown as CompanyData,
  shopifyData as unknown as CompanyData,
  wayfairData as unknown as CompanyData,
  yetiData as unknown as CompanyData,
]

export function getAllCompanies(): CompanyData[] {
  return allCompanies.sort((a, b) =>
    (b.financials.income_statement.revenue || 0) - (a.financials.income_statement.revenue || 0)
  )
}

export function getCompanyBySlug(slug: string): CompanyData | undefined {
  return allCompanies.find(c =>
    c.id.ticker.toLowerCase() === slug.toLowerCase() ||
    c.id.company.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '') === slug.toLowerCase()
  )
}

export function getCompanyTypes(): string[] {
  const types = new Set(allCompanies.map(c => c.id.company_type))
  return Array.from(types).sort()
}

export function filterByType(companies: CompanyData[], type: string): CompanyData[] {
  if (!type || type === 'all') return companies
  return companies.filter(c => c.id.company_type.toLowerCase() === type.toLowerCase())
}

export function sortCompanies(
  companies: CompanyData[],
  sortBy: 'revenue' | 'growth' | 'margin' | 'name'
): CompanyData[] {
  return [...companies].sort((a, b) => {
    switch (sortBy) {
      case 'revenue':
        return (b.financials.income_statement.revenue || 0) - (a.financials.income_statement.revenue || 0)
      case 'growth':
        return (b.financials.income_statement.revenue_yoy_pct || 0) - (a.financials.income_statement.revenue_yoy_pct || 0)
      case 'margin':
        return (b.financials.income_statement.net_margin_pct || 0) - (a.financials.income_statement.net_margin_pct || 0)
      case 'name':
        return a.id.company.localeCompare(b.id.company)
      default:
        return 0
    }
  })
}
