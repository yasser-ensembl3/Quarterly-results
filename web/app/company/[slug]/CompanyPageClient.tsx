'use client'

import Link from 'next/link'
import { CompanyData } from '@/lib/data'
import { formatCurrency, formatPercent, getCompanyTypeColor } from '@/lib/utils'
import { ArrowLeft, TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Quote, FileText, Headphones, Video, Image, File, Download, ExternalLink } from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899']

interface SourceFile {
  id: string
  name: string
  mimeType: string
  type: 'pdf' | 'audio' | 'video' | 'image' | 'document' | 'other'
  viewUrl: string
  downloadUrl: string
}

interface Props {
  company: CompanyData
  sourceFiles?: SourceFile[]
}

const FILE_ICONS = {
  pdf: FileText,
  audio: Headphones,
  video: Video,
  image: Image,
  document: FileText,
  other: File,
}

const FILE_COLORS = {
  pdf: 'text-red-500 bg-red-50',
  audio: 'text-purple-500 bg-purple-50',
  video: 'text-blue-500 bg-blue-50',
  image: 'text-green-500 bg-green-50',
  document: 'text-orange-500 bg-orange-50',
  other: 'text-gray-500 bg-gray-50',
}

export default function CompanyPageClient({ company, sourceFiles = [] }: Props) {
  const { id, financials, segments, operations, guidance, strategic, highlights, metadata } = company
  const { income_statement, balance_sheet, cash_flow, per_share } = financials

  // Prepare segment data for pie chart
  const segmentData = segments.by_business.map((seg, i) => ({
    name: seg.name,
    value: seg.revenue,
    color: COLORS[i % COLORS.length]
  }))

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
      <div className="bg-white rounded-xl border border-gray-200 p-8">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold text-gray-900">{id.company}</h1>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getCompanyTypeColor(id.company_type)}`}>
                {id.company_type}
              </span>
            </div>
            <p className="text-gray-500 text-lg">
              {id.ticker} • {id.quarter} {id.year} • Report Date: {id.report_date}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">Data Quality</p>
            <p className="text-2xl font-bold text-blue-600">
              {Math.round((metadata.data_quality_score || 0) * 100)}%
            </p>
          </div>
        </div>

        {/* Investment Thesis */}
        {highlights.investment_thesis && (
          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-100">
            <h3 className="font-semibold text-blue-900 mb-2">Investment Thesis</h3>
            <p className="text-blue-800">{highlights.investment_thesis}</p>
          </div>
        )}
      </div>

      {/* Source Documents */}
      {sourceFiles.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Source Documents</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {sourceFiles.map((file) => {
              const IconComponent = FILE_ICONS[file.type]
              const colorClass = FILE_COLORS[file.type]
              return (
                <div
                  key={file.id}
                  className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
                >
                  <div className={`p-2 rounded-lg ${colorClass}`}>
                    <IconComponent className="w-5 h-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate" title={file.name}>
                      {file.name}
                    </p>
                    <p className="text-xs text-gray-500 uppercase">{file.type}</p>
                  </div>
                  <div className="flex items-center gap-1">
                    <a
                      href={file.viewUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                      title="View"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                    <a
                      href={file.downloadUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-1.5 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded transition-colors"
                      title="Download"
                    >
                      <Download className="w-4 h-4" />
                    </a>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="Revenue"
          value={formatCurrency(income_statement.revenue)}
          subValue={income_statement.revenue_yoy_pct ? `${formatPercent(income_statement.revenue_yoy_pct)} YoY` : undefined}
          positive={income_statement.revenue_yoy_pct ? income_statement.revenue_yoy_pct > 0 : undefined}
        />
        <MetricCard
          label="Net Income"
          value={formatCurrency(income_statement.net_income)}
          subValue={income_statement.net_margin_pct ? `${income_statement.net_margin_pct.toFixed(1)}% margin` : undefined}
        />
        <MetricCard
          label="Operating Income"
          value={formatCurrency(income_statement.operating_income)}
          subValue={income_statement.operating_margin_pct ? `${income_statement.operating_margin_pct.toFixed(1)}% margin` : undefined}
        />
        <MetricCard
          label="Free Cash Flow"
          value={formatCurrency(cash_flow.free_cash_flow)}
        />
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Income Statement */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Income Statement</h3>
          <table className="w-full">
            <tbody className="divide-y divide-gray-100">
              <TableRow label="Revenue" value={formatCurrency(income_statement.revenue)} />
              <TableRow label="YoY Growth" value={formatPercent(income_statement.revenue_yoy_pct)} highlight={income_statement.revenue_yoy_pct} />
              <TableRow label="Gross Profit" value={formatCurrency(income_statement.gross_profit)} />
              <TableRow label="Gross Margin" value={income_statement.gross_margin_pct ? `${income_statement.gross_margin_pct.toFixed(1)}%` : 'N/A'} />
              <TableRow label="Operating Income" value={formatCurrency(income_statement.operating_income)} />
              <TableRow label="Operating Margin" value={income_statement.operating_margin_pct ? `${income_statement.operating_margin_pct.toFixed(1)}%` : 'N/A'} />
              <TableRow label="Net Income" value={formatCurrency(income_statement.net_income)} />
              <TableRow label="Net Margin" value={income_statement.net_margin_pct ? `${income_statement.net_margin_pct.toFixed(1)}%` : 'N/A'} />
              <TableRow label="EBITDA" value={formatCurrency(income_statement.ebitda)} />
              <TableRow label="Adjusted EBITDA" value={formatCurrency(income_statement.adjusted_ebitda)} />
            </tbody>
          </table>
        </div>

        {/* Segments Pie Chart */}
        {segmentData.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue by Segment</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={segmentData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="value"
                    label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                    labelLine={false}
                  >
                    {segmentData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number) => [`$${(value / 1000).toFixed(1)}B`, 'Revenue']}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 space-y-2">
              {segments.by_business.map((seg, i) => (
                <div key={seg.name} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                    <span className="text-gray-700">{seg.name}</span>
                  </div>
                  <div className="text-right">
                    <span className="font-medium">{formatCurrency(seg.revenue)}</span>
                    {seg.yoy_pct && (
                      <span className={`ml-2 ${seg.yoy_pct > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatPercent(seg.yoy_pct)}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Balance Sheet & Cash */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Balance Sheet</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Cash & Equivalents</span>
              <span className="font-medium">{formatCurrency(balance_sheet.cash_and_equivalents)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Total Debt</span>
              <span className="font-medium">{formatCurrency(balance_sheet.total_debt)}</span>
            </div>
            <div className="flex justify-between border-t pt-3">
              <span className="text-gray-900 font-medium">Net Cash</span>
              <span className={`font-bold ${(balance_sheet.net_cash || 0) > 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(balance_sheet.net_cash)}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Per Share</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">EPS (Basic)</span>
              <span className="font-medium">{per_share.eps_basic ? `$${per_share.eps_basic.toFixed(2)}` : 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">EPS (Diluted)</span>
              <span className="font-medium">{per_share.eps_diluted ? `$${per_share.eps_diluted.toFixed(2)}` : 'N/A'}</span>
            </div>
          </div>
        </div>

        {operations.employees && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Operations</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Employees</span>
                <span className="font-medium">{operations.employees.toLocaleString()}</span>
              </div>
              {operations.employee_change_qoq && (
                <div className="flex justify-between">
                  <span className="text-gray-600">QoQ Change</span>
                  <span className={`font-medium ${operations.employee_change_qoq > 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPercent(operations.employee_change_qoq)}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Guidance */}
      {(guidance.q_plus_1.revenue_low || guidance.commentary) && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Guidance & Outlook</h3>
          {guidance.q_plus_1.revenue_low && guidance.q_plus_1.revenue_high && (
            <div className="mb-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Next Quarter Revenue Guidance</p>
              <p className="text-xl font-bold text-gray-900">
                {formatCurrency(guidance.q_plus_1.revenue_low)} - {formatCurrency(guidance.q_plus_1.revenue_high)}
              </p>
            </div>
          )}
          {guidance.commentary && (
            <p className="text-gray-700 italic">&quot;{guidance.commentary}&quot;</p>
          )}
        </div>
      )}

      {/* Key Positives & Concerns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {highlights.key_positives.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              Key Positives
            </h3>
            <ul className="space-y-2">
              {highlights.key_positives.map((point, i) => (
                <li key={i} className="flex items-start gap-2 text-gray-700">
                  <TrendingUp className="w-4 h-4 text-green-500 mt-1 flex-shrink-0" />
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {highlights.key_concerns.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              Key Concerns
            </h3>
            <ul className="space-y-2">
              {highlights.key_concerns.map((point, i) => (
                <li key={i} className="flex items-start gap-2 text-gray-700">
                  <TrendingDown className="w-4 h-4 text-red-500 mt-1 flex-shrink-0" />
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Notable Quotes */}
      {highlights.notable_quotes.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Quote className="w-5 h-5 text-blue-500" />
            Notable Quotes
          </h3>
          <div className="space-y-4">
            {highlights.notable_quotes.map((quote, i) => (
              <blockquote key={i} className="border-l-4 border-blue-500 pl-4 py-2">
                <p className="text-gray-700 italic">&quot;{quote.quote}&quot;</p>
                <footer className="text-sm text-gray-500 mt-1">— {quote.speaker}</footer>
              </blockquote>
            ))}
          </div>
        </div>
      )}

      {/* Competitive Advantages */}
      {strategic.competitive_advantages.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Competitive Advantages</h3>
          <div className="flex flex-wrap gap-2">
            {strategic.competitive_advantages.map((advantage, i) => (
              <span key={i} className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm">
                {advantage}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function MetricCard({
  label,
  value,
  subValue,
  positive
}: {
  label: string
  value: string
  subValue?: string
  positive?: boolean
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <p className="text-sm text-gray-500 uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
      {subValue && (
        <p className={`text-sm mt-1 ${positive === true ? 'text-green-600' : positive === false ? 'text-red-600' : 'text-gray-500'}`}>
          {subValue}
        </p>
      )}
    </div>
  )
}

function TableRow({
  label,
  value,
  highlight
}: {
  label: string
  value: string
  highlight?: number | null
}) {
  return (
    <tr>
      <td className="py-2 text-gray-600">{label}</td>
      <td className={`py-2 text-right font-medium ${
        highlight !== undefined && highlight !== null
          ? highlight > 0 ? 'text-green-600' : highlight < 0 ? 'text-red-600' : 'text-gray-900'
          : 'text-gray-900'
      }`}>
        {value}
      </td>
    </tr>
  )
}
