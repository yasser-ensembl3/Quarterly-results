import { NextResponse } from 'next/server';
import { CompanyData } from '@/lib/data';
import {
  isGoogleDriveConfigured,
  getLatestQuarterStructure,
  fetchFileContent,
} from '@/lib/google-drive';
import { cache, CACHE_KEYS, getCacheTTL } from '@/lib/cache';

// Static imports for fallback
import amazonData from '@/data/companies/amazon_q3_2025.json';
import circleData from '@/data/companies/circle_q3_2025.json';
import coinbaseData from '@/data/companies/coinbase_q3_2025.json';
import constellationData from '@/data/companies/constellation_software_q3_2025.json';
import ebayData from '@/data/companies/ebay_q3_2025.json';
import etsyData from '@/data/companies/etsy_q3_2025.json';
import figsData from '@/data/companies/figs_q3_2025.json';
import lvmhData from '@/data/companies/lvmh_q3_2025.json';
import nvidiaData from '@/data/companies/nvidia_q3_2025.json';
import shopifyData from '@/data/companies/shopify_q3_2025.json';
import wayfairData from '@/data/companies/wayfair_q3_2025.json';
import yetiData from '@/data/companies/yeti_q3_2025.json';

const staticFallback: CompanyData[] = [
  amazonData,
  circleData,
  coinbaseData,
  constellationData,
  ebayData,
  etsyData,
  figsData,
  lvmhData,
  nvidiaData,
  shopifyData,
  wayfairData,
  yetiData,
] as unknown as CompanyData[];

export async function GET() {
  try {
    // Check cache first
    const cached = cache.get<CompanyData[]>(CACHE_KEYS.ALL_COMPANIES);
    if (cached) {
      return NextResponse.json({
        data: cached,
        source: 'cache',
        timestamp: new Date().toISOString(),
      });
    }

    // Check if Google Drive is configured
    if (!isGoogleDriveConfigured()) {
      console.warn('[API] Google Drive not configured, using static fallback');
      return NextResponse.json({
        data: staticFallback,
        source: 'static',
        timestamp: new Date().toISOString(),
      });
    }

    // Fetch from Google Drive
    const quarterStructure = await getLatestQuarterStructure();

    if (!quarterStructure || quarterStructure.companies.length === 0) {
      console.warn('[API] No companies found in Google Drive, using static fallback');
      return NextResponse.json({
        data: staticFallback,
        source: 'static-fallback',
        timestamp: new Date().toISOString(),
      });
    }

    // Fetch all company JSON files in parallel
    const companies = await Promise.all(
      quarterStructure.companies.map(async (company) => {
        try {
          return await fetchFileContent<CompanyData>(company.jsonFileId!);
        } catch (error) {
          console.error(`[API] Failed to fetch ${company.name}:`, error);
          return null;
        }
      })
    );

    const validCompanies = companies.filter((c): c is CompanyData => c !== null);

    if (validCompanies.length === 0) {
      console.warn('[API] No valid company data fetched, using static fallback');
      return NextResponse.json({
        data: staticFallback,
        source: 'static-fallback',
        timestamp: new Date().toISOString(),
      });
    }

    // Cache the results
    const ttl = getCacheTTL();
    cache.set(CACHE_KEYS.ALL_COMPANIES, validCompanies, ttl);

    // Also cache individual companies
    validCompanies.forEach((company) => {
      cache.set(CACHE_KEYS.COMPANY(company.id.ticker), company, ttl);
    });

    return NextResponse.json({
      data: validCompanies,
      source: 'drive',
      quarter: quarterStructure.name,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('[API] Error fetching companies:', error);

    return NextResponse.json({
      data: staticFallback,
      source: 'static-fallback',
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString(),
    });
  }
}

export const revalidate = 300; // 5 minutes ISR
