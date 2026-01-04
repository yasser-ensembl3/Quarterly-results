import { notFound } from 'next/navigation'
import { fetchCompanyBySlug, fetchAllCompanies } from '@/lib/data'
import { getCompanySourceFiles, isGoogleDriveConfigured, SourceFile } from '@/lib/google-drive'
import CompanyPageClient from './CompanyPageClient'

interface Props {
  params: Promise<{ slug: string }>
}

async function fetchSourceFiles(ticker: string): Promise<SourceFile[]> {
  if (!isGoogleDriveConfigured()) return []
  try {
    return await getCompanySourceFiles(ticker)
  } catch (error) {
    console.error('Failed to fetch source files:', error)
    return []
  }
}

export default async function CompanyPage({ params }: Props) {
  const { slug } = await params
  const company = await fetchCompanyBySlug(slug)

  if (!company) {
    notFound()
  }

  const sourceFiles = await fetchSourceFiles(company.id.ticker)

  return <CompanyPageClient company={company} sourceFiles={sourceFiles} />
}

export async function generateStaticParams() {
  const companies = await fetchAllCompanies()
  return companies.map((c) => ({
    slug: c.id.ticker.toLowerCase(),
  }))
}

export const revalidate = 300 // 5 minutes ISR
