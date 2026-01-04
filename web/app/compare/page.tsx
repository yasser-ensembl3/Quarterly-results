import { fetchAllCompanies } from '@/lib/data'
import ComparePageClient from './ComparePageClient'

export default async function ComparePage() {
  const companies = await fetchAllCompanies()
  return <ComparePageClient initialCompanies={companies} />
}

export const revalidate = 300 // 5 minutes ISR
