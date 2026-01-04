'use client'

import { useState, useMemo } from 'react'
import Link from 'next/link'
import { CompanyData } from '@/lib/data'
import { formatCurrency, formatPercent, getCompanyTypeColor } from '@/lib/utils'
import { ArrowLeft, X, Plus } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444']

interface Props {
  initialCompanies: CompanyData[]
}

export default function ComparePageClient({ initialCompanies }: Props) {
  const allCompanies = initialCompanies
  const [selectedTickers, setSelectedTickers] = useState<string[]>(['NVDA', 'AMZN'])

  const selectedCompanies = useMemo(() => {
    return selectedTickers
      .map(ticker => allCompanies.find(c => c.id.ticker === ticker))
      .filter((c): c is CompanyData => c !== undefined)
  }, [selectedTickers, allCompanies])

  const availableCompanies = useMemo(() => {
    return allCompanies.filter(c => !selectedTickers.includes(c.id.ticker))
  }, [allCompanies, selectedTickers])

  const addCompany = (ticker: string) => {
    if (selectedTickers.length < 4 && !selectedTickers.includes(ticker)) {
      setSelectedTickers([...selectedTickers, ticker])
    }
  }

  const removeCompany = (ticker: string) => {
    setSelectedTickers(selectedTickers.filter(t => t !== ticker))
  }

  // Prepare chart data
  const revenueChartData = [{
    name: 'Revenue',
    ...Object.fromEntries(
      selectedCompanies.map(c => [c.id.ticker, (c.financials.income_statement.revenue || 0) / 1000])
    )
  }]

  const growthChartData = [{
    name: 'YoY Growth',
    ...Object.fromEntries(
      selectedCompanies.map(c => [c.id.ticker, c.financials.income_statement.revenue_yoy_pct || 0])
    )
  }]

  const marginChartData = [
    {
      name: 'Gross Margin',
      ...Object.fromEntries(
        selectedCompanies.map(c => [c.id.ticker, c.financials.income_statement.gross_margin_pct || 0])
      )
    },
    {
      name: 'Operating Margin',
      ...Object.fromEntries(
        selectedCompanies.map(c => [c.id.ticker, c.financials.income_statement.operating_margin_pct || 0])
      )
    },
    {
      name: 'Net Margin',
      ...Object.fromEntries(
        selectedCompanies.map(c => [c.id.ticker, c.financials.income_statement.net_margin_pct || 0])
      )
    }
  ]

  return (
    <div className="space-y-8">
      {/* Back button */}
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </Link>

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Compare Companies</h1>
        <p className="mt-2 text-gray-600">
          Select up to 4 companies to compare side by side
        </p>
      </div>

      {/* Company Selector */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex flex-wrap items-center gap-3">
          {selectedCompanies.map((company, i) => (
            <div
              key={company.id.ticker}
              className="flex items-center gap-2 px-4 py-2 rounded-full border-2"
              style={{ borderColor: COLORS[i % COLORS.length] }}
            >
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: COLORS[i % COLORS.length] }}
              />
              <span className="font-medium">{company.id.ticker}</span>
              <span className="text-gray-500 text-sm">{company.id.company}</span>
              <button
                onClick={() => removeCompany(company.id.ticker)}
                className="ml-1 text-gray-400 hover:text-red-500"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}

          {selectedTickers.length < 4 && (
            <div className="relative">
              <select
                onChange={(e) => {
                  if (e.target.value) {
                    addCompany(e.target.value)
                    e.target.value = ''
                  }
                }}
                className="appearance-none pl-10 pr-4 py-2 border border-gray-300 rounded-full text-sm focus:ring-blue-500 focus:border-blue-500 cursor-pointer"
                defaultValue=""
              >
                <option value="">Add company...</option>
                {availableCompanies.map(c => (
                  <option key={c.id.ticker} value={c.id.ticker}>
                    {c.id.ticker} - {c.id.company}
                  </option>
                ))}
              </select>
              <Plus className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            </div>
          )}
        </div>
      </div>

      {selectedCompanies.length < 2 ? (
        <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
          <p className="text-gray-500">Select at least 2 companies to compare</p>
        </div>
      ) : (
        <>
          {/* Revenue Chart */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue Comparison (Billions USD)</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={revenueChartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis dataKey="name" />
                  <YAxis tickFormatter={(value) => `$${value}B`} />
                  <Tooltip formatter={(value: number) => [`$${value.toFixed(1)}B`, '']} />
                  <Legend />
                  {selectedCompanies.map((company, i) => (
                    <Bar
                      key={company.id.ticker}
                      dataKey={company.id.ticker}
                      fill={COLORS[i % COLORS.length]}
                      name={company.id.ticker}
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Growth Chart */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">YoY Revenue Growth (%)</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={growthChartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis dataKey="name" />
                  <YAxis tickFormatter={(value) => `${value}%`} />
                  <Tooltip formatter={(value: number) => [`${value.toFixed(1)}%`, '']} />
                  <Legend />
                  {selectedCompanies.map((company, i) => (
                    <Bar
                      key={company.id.ticker}
                      dataKey={company.id.ticker}
                      fill={COLORS[i % COLORS.length]}
                      name={company.id.ticker}
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Margins Chart */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Margin Comparison (%)</h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={marginChartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis dataKey="name" />
                  <YAxis tickFormatter={(value) => `${value}%`} />
                  <Tooltip formatter={(value: number) => [`${value.toFixed(1)}%`, '']} />
                  <Legend />
                  {selectedCompanies.map((company, i) => (
                    <Bar
                      key={company.id.ticker}
                      dataKey={company.id.ticker}
                      fill={COLORS[i % COLORS.length]}
                      name={company.id.ticker}
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Comparison Table */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <h3 className="text-lg font-semibold text-gray-900 p-6 border-b">Detailed Comparison</h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Metric
                    </th>
                    {selectedCompanies.map((company, i) => (
                      <th
                        key={company.id.ticker}
                        className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider"
                        style={{ color: COLORS[i % COLORS.length] }}
                      >
                        {company.id.ticker}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  <CompareRow
                    label="Company Type"
                    values={selectedCompanies.map(c => (
                      <span className={`px-2 py-1 rounded-full text-xs ${getCompanyTypeColor(c.id.company_type)}`}>
                        {c.id.company_type}
                      </span>
                    ))}
                  />
                  <CompareRow
                    label="Revenue"
                    values={selectedCompanies.map(c => formatCurrency(c.financials.income_statement.revenue))}
                  />
                  <CompareRow
                    label="YoY Growth"
                    values={selectedCompanies.map(c => formatPercent(c.financials.income_statement.revenue_yoy_pct))}
                    highlight={selectedCompanies.map(c => c.financials.income_statement.revenue_yoy_pct)}
                  />
                  <CompareRow
                    label="Net Income"
                    values={selectedCompanies.map(c => formatCurrency(c.financials.income_statement.net_income))}
                  />
                  <CompareRow
                    label="Net Margin"
                    values={selectedCompanies.map(c =>
                      c.financials.income_statement.net_margin_pct
                        ? `${c.financials.income_statement.net_margin_pct.toFixed(1)}%`
                        : 'N/A'
                    )}
                  />
                  <CompareRow
                    label="Operating Margin"
                    values={selectedCompanies.map(c =>
                      c.financials.income_statement.operating_margin_pct
                        ? `${c.financials.income_statement.operating_margin_pct.toFixed(1)}%`
                        : 'N/A'
                    )}
                  />
                  <CompareRow
                    label="Gross Margin"
                    values={selectedCompanies.map(c =>
                      c.financials.income_statement.gross_margin_pct
                        ? `${c.financials.income_statement.gross_margin_pct.toFixed(1)}%`
                        : 'N/A'
                    )}
                  />
                  <CompareRow
                    label="Free Cash Flow"
                    values={selectedCompanies.map(c => formatCurrency(c.financials.cash_flow.free_cash_flow))}
                  />
                  <CompareRow
                    label="Cash & Equivalents"
                    values={selectedCompanies.map(c => formatCurrency(c.financials.balance_sheet.cash_and_equivalents))}
                  />
                  <CompareRow
                    label="Net Cash"
                    values={selectedCompanies.map(c => formatCurrency(c.financials.balance_sheet.net_cash))}
                    highlight={selectedCompanies.map(c => c.financials.balance_sheet.net_cash)}
                  />
                  <CompareRow
                    label="Employees"
                    values={selectedCompanies.map(c =>
                      c.operations.employees ? c.operations.employees.toLocaleString() : 'N/A'
                    )}
                  />
                  <CompareRow
                    label="Data Quality"
                    values={selectedCompanies.map(c => `${Math.round((c.metadata.data_quality_score || 0) * 100)}%`)}
                  />
                </tbody>
              </table>
            </div>
          </div>

          {/* Investment Thesis Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {selectedCompanies.map((company, i) => (
              <div
                key={company.id.ticker}
                className="bg-white rounded-xl border-2 p-6"
                style={{ borderColor: COLORS[i % COLORS.length] }}
              >
                <div className="flex items-center gap-2 mb-4">
                  <div
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: COLORS[i % COLORS.length] }}
                  />
                  <h3 className="text-lg font-semibold text-gray-900">
                    {company.id.ticker} - Investment Thesis
                  </h3>
                </div>
                <p className="text-gray-700">{company.highlights.investment_thesis}</p>

                {company.highlights.key_positives.length > 0 && (
                  <div className="mt-4">
                    <p className="text-sm font-medium text-green-700 mb-2">Key Positives:</p>
                    <ul className="text-sm text-gray-600 space-y-1">
                      {company.highlights.key_positives.slice(0, 3).map((point, j) => (
                        <li key={j} className="flex items-start gap-2">
                          <span className="text-green-500">+</span>
                          <span>{point}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {company.highlights.key_concerns.length > 0 && (
                  <div className="mt-4">
                    <p className="text-sm font-medium text-red-700 mb-2">Key Concerns:</p>
                    <ul className="text-sm text-gray-600 space-y-1">
                      {company.highlights.key_concerns.slice(0, 3).map((point, j) => (
                        <li key={j} className="flex items-start gap-2">
                          <span className="text-red-500">-</span>
                          <span>{point}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function CompareRow({
  label,
  values,
  highlight
}: {
  label: string
  values: (string | React.ReactNode)[]
  highlight?: (number | null | undefined)[]
}) {
  return (
    <tr>
      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
        {label}
      </td>
      {values.map((value, i) => (
        <td
          key={i}
          className={`px-6 py-4 whitespace-nowrap text-sm text-right font-medium ${
            highlight && highlight[i] !== null && highlight[i] !== undefined
              ? highlight[i]! > 0 ? 'text-green-600' : highlight[i]! < 0 ? 'text-red-600' : 'text-gray-900'
              : 'text-gray-900'
          }`}
        >
          {value}
        </td>
      ))}
    </tr>
  )
}
