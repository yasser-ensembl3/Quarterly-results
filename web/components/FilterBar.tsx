'use client'

import { getCompanyTypes } from '@/lib/data'

interface FilterBarProps {
  selectedType: string
  onTypeChange: (type: string) => void
  sortBy: 'revenue' | 'growth' | 'margin' | 'name'
  onSortChange: (sort: 'revenue' | 'growth' | 'margin' | 'name') => void
}

export function FilterBar({ selectedType, onTypeChange, sortBy, onSortChange }: FilterBarProps) {
  const types = getCompanyTypes()

  return (
    <div className="flex flex-wrap items-center gap-4 p-4 bg-white rounded-lg border border-gray-200 mb-6">
      {/* Type Filter */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-700">Type:</label>
        <select
          value={selectedType}
          onChange={(e) => onTypeChange(e.target.value)}
          className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="all">All</option>
          {types.map(type => (
            <option key={type} value={type}>
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {/* Sort */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-700">Sort by:</label>
        <select
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value as 'revenue' | 'growth' | 'margin' | 'name')}
          className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="revenue">Revenue (High to Low)</option>
          <option value="growth">Growth (High to Low)</option>
          <option value="margin">Margin (High to Low)</option>
          <option value="name">Name (A-Z)</option>
        </select>
      </div>
    </div>
  )
}
