'use client'

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { CompanyData } from '@/lib/data'

interface RevenueChartProps {
  companies: CompanyData[]
}

const COLORS = [
  '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
  '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1',
  '#14B8A6', '#A855F7'
]

export function RevenueChart({ companies }: RevenueChartProps) {
  const data = companies
    .filter(c => c.financials.income_statement.revenue)
    .map((c, i) => ({
      name: c.id.ticker,
      revenue: c.financials.income_statement.revenue! / 1000, // Convert to billions
      growth: c.financials.income_statement.revenue_yoy_pct || 0,
      color: COLORS[i % COLORS.length]
    }))
    .sort((a, b) => b.revenue - a.revenue)

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue Comparison (Billions USD)</h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `$${value}B`}
            />
            <Tooltip
              formatter={(value: number) => [`$${value.toFixed(1)}B`, 'Revenue']}
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #E5E7EB',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
            />
            <Bar dataKey="revenue" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
