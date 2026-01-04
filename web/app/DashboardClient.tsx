'use client'

import { useState, useMemo } from 'react'
import { filterByType, sortCompanies, CompanyData } from '@/lib/data'
import { CompanyCard } from '@/components/CompanyCard'
import { FilterBar } from '@/components/FilterBar'
import { RevenueChart } from '@/components/RevenueChart'
import { formatCurrency, formatPercent } from '@/lib/utils'

interface Props {
  initialCompanies: CompanyData[]
}

export default function DashboardClient({ initialCompanies }: Props) {
  const allCompanies = initialCompanies
  const [selectedType, setSelectedType] = useState('all')
  const [sortBy, setSortBy] = useState<'revenue' | 'growth' | 'margin' | 'name'>('revenue')

  const filteredCompanies = useMemo(() => {
    const filtered = filterByType(allCompanies, selectedType)
    return sortCompanies(filtered, sortBy)
  }, [allCompanies, selectedType, sortBy])

  // Calculate summary stats
  const stats = useMemo(() => {
    const revenues = filteredCompanies
      .map(c => c.financials.income_statement.revenue)
      .filter((r): r is number => r !== null)
    const growths = filteredCompanies
      .map(c => c.financials.income_statement.revenue_yoy_pct)
      .filter((g): g is number => g !== null)

    return {
      totalRevenue: revenues.reduce((a, b) => a + b, 0),
      avgGrowth: growths.length ? growths.reduce((a, b) => a + b, 0) / growths.length : 0,
      companiesCount: filteredCompanies.length,
      topGrower: filteredCompanies.reduce((max, c) =>
        (c.financials.income_statement.revenue_yoy_pct || 0) > (max.financials.income_statement.revenue_yoy_pct || 0) ? c : max
      , filteredCompanies[0])
    }
  }, [filteredCompanies])

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Q3 2025 Earnings Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Compare quarterly financial results across {allCompanies.length} companies
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <p className="text-sm text-gray-500 uppercase tracking-wide">Companies</p>
          <p className="text-3xl font-bold text-gray-900">{stats.companiesCount}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <p className="text-sm text-gray-500 uppercase tracking-wide">Total Revenue</p>
          <p className="text-3xl font-bold text-gray-900">{formatCurrency(stats.totalRevenue)}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <p className="text-sm text-gray-500 uppercase tracking-wide">Avg YoY Growth</p>
          <p className={`text-3xl font-bold ${stats.avgGrowth > 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatPercent(stats.avgGrowth)}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <p className="text-sm text-gray-500 uppercase tracking-wide">Top Grower</p>
          <p className="text-2xl font-bold text-gray-900">{stats.topGrower?.id.ticker}</p>
          <p className="text-sm text-green-600">
            {formatPercent(stats.topGrower?.financials.income_statement.revenue_yoy_pct)}
          </p>
        </div>
      </div>

      {/* Revenue Chart */}
      <RevenueChart companies={filteredCompanies} />

      {/* Filters */}
      <FilterBar
        selectedType={selectedType}
        onTypeChange={setSelectedType}
        sortBy={sortBy}
        onSortChange={setSortBy}
      />

      {/* Company Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredCompanies.map((company) => (
          <CompanyCard key={company.id.ticker} company={company} />
        ))}
      </div>

      {filteredCompanies.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500">No companies found for the selected filter.</p>
        </div>
      )}
    </div>
  )
}
