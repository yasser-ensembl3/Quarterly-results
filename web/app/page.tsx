import { fetchAllCompanies } from '@/lib/data'
import DashboardClient from './DashboardClient'

export default async function Dashboard() {
  const companies = await fetchAllCompanies()
  return <DashboardClient initialCompanies={companies} />
}

export const revalidate = 300 // 5 minutes ISR
