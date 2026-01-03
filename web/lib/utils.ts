import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(value: number | null | undefined, decimals = 1): string {
  if (value === null || value === undefined) return "N/A"
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(decimals)}B`
  }
  return `$${value.toFixed(decimals)}M`
}

export function formatPercent(value: number | null | undefined, decimals = 1): string {
  if (value === null || value === undefined) return "N/A"
  const sign = value > 0 ? "+" : ""
  return `${sign}${value.toFixed(decimals)}%`
}

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return "N/A"
  return new Intl.NumberFormat('en-US').format(value)
}

export function getCompanyTypeColor(type: string): string {
  const colors: Record<string, string> = {
    crypto: "bg-orange-100 text-orange-800",
    ecommerce: "bg-blue-100 text-blue-800",
    tech: "bg-purple-100 text-purple-800",
    fintech: "bg-green-100 text-green-800",
    retail: "bg-pink-100 text-pink-800",
    luxury: "bg-amber-100 text-amber-800",
    software: "bg-indigo-100 text-indigo-800",
  }
  return colors[type.toLowerCase()] || "bg-gray-100 text-gray-800"
}

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '')
}
