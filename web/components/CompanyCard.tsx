'use client'

import Link from 'next/link'
import { CompanyData } from '@/lib/data'
import { formatCurrency, formatPercent, getCompanyTypeColor, slugify } from '@/lib/utils'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface CompanyCardProps {
  company: CompanyData
}

export function CompanyCard({ company }: CompanyCardProps) {
  const { id, financials, highlights } = company
  const { income_statement } = financials

  const growthIcon = () => {
    const growth = income_statement.revenue_yoy_pct
    if (!growth) return <Minus className="w-4 h-4 text-gray-400" />
    if (growth > 0) return <TrendingUp className="w-4 h-4 text-green-500" />
    return <TrendingDown className="w-4 h-4 text-red-500" />
  }

  const slug = id.ticker.toLowerCase()

  return (
    <Link href={`/company/${slug}`}>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md hover:border-blue-300 transition-all cursor-pointer">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="font-semibold text-lg text-gray-900">{id.company}</h3>
            <p className="text-sm text-gray-500">{id.ticker} • {id.quarter} {id.year}</p>
          </div>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCompanyTypeColor(id.company_type)}`}>
            {id.company_type}
          </span>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">Revenue</p>
            <p className="text-xl font-bold text-gray-900">
              {formatCurrency(income_statement.revenue)}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">YoY Growth</p>
            <div className="flex items-center gap-1">
              {growthIcon()}
              <p className={`text-xl font-bold ${
                (income_statement.revenue_yoy_pct || 0) > 0 ? 'text-green-600' :
                (income_statement.revenue_yoy_pct || 0) < 0 ? 'text-red-600' : 'text-gray-900'
              }`}>
                {formatPercent(income_statement.revenue_yoy_pct)}
              </p>
            </div>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">Net Income</p>
            <p className="text-lg font-semibold text-gray-900">
              {formatCurrency(income_statement.net_income)}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">Net Margin</p>
            <p className="text-lg font-semibold text-gray-900">
              {income_statement.net_margin_pct ? `${income_statement.net_margin_pct.toFixed(1)}%` : 'N/A'}
            </p>
          </div>
        </div>

        {/* Investment Thesis Preview */}
        {highlights.investment_thesis && (
          <div className="pt-4 border-t border-gray-100">
            <p className="text-sm text-gray-600 line-clamp-2">
              {highlights.investment_thesis}
            </p>
          </div>
        )}

        {/* Data Quality Indicator */}
        <div className="mt-4 flex items-center gap-2">
          <div className="flex-1 bg-gray-200 rounded-full h-1.5">
            <div
              className="bg-blue-600 h-1.5 rounded-full"
              style={{ width: `${(company.metadata.data_quality_score || 0) * 100}%` }}
            />
          </div>
          <span className="text-xs text-gray-500">
            {Math.round((company.metadata.data_quality_score || 0) * 100)}% quality
          </span>
        </div>
      </div>
    </Link>
  )
}
