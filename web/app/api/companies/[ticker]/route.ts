import { NextRequest, NextResponse } from 'next/server';
import { CompanyData } from '@/lib/data';
import {
  isGoogleDriveConfigured,
  getLatestQuarterStructure,
  fetchFileContent,
} from '@/lib/google-drive';
import { cache, CACHE_KEYS, getCacheTTL } from '@/lib/cache';

// Mapping ticker -> folder name (for fuzzy matching)
const TICKER_TO_FOLDER: Record<string, string[]> = {
  AMZN: ['amazon', 'amzn'],
  COIN: ['coinbase', 'coin'],
  SHOP: ['shopify', 'shop'],
  NVDA: ['nvidia', 'nvda'],
  EBAY: ['ebay'],
  ETSY: ['etsy'],
  W: ['wayfair'],
  YETI: ['yeti'],
  FIGS: ['figs'],
  LVMH: ['lvmh'],
  CSI: ['constellation', 'constellation software'],
  CRCL: ['circle', 'crcl'],
};

interface RouteContext {
  params: Promise<{ ticker: string }>;
}

export async function GET(
  request: NextRequest,
  context: RouteContext
) {
  const { ticker: rawTicker } = await context.params;
  const ticker = rawTicker.toUpperCase();

  try {
    // Check cache first
    const cached = cache.get<CompanyData>(CACHE_KEYS.COMPANY(ticker));
    if (cached) {
      return NextResponse.json({
        data: cached,
        source: 'cache',
        timestamp: new Date().toISOString(),
      });
    }

    // Check if all companies are cached
    const allCached = cache.get<CompanyData[]>(CACHE_KEYS.ALL_COMPANIES);
    if (allCached) {
      const company = allCached.find(
        (c) => c.id.ticker.toUpperCase() === ticker
      );
      if (company) {
        return NextResponse.json({
          data: company,
          source: 'cache',
          timestamp: new Date().toISOString(),
        });
      }
    }

    // Check if Google Drive is configured
    if (!isGoogleDriveConfigured()) {
      return NextResponse.json(
        { error: 'Company not found', ticker },
        { status: 404 }
      );
    }

    // Fetch from Google Drive
    const quarterStructure = await getLatestQuarterStructure();

    if (!quarterStructure) {
      return NextResponse.json(
        { error: 'No quarter data found' },
        { status: 500 }
      );
    }

    // Find matching company folder
    const matchingFolderNames = TICKER_TO_FOLDER[ticker] || [ticker.toLowerCase()];
    const companyEntry = quarterStructure.companies.find((c) => {
      const folderName = c.name.toLowerCase();
      return matchingFolderNames.some(
        (match) => folderName.includes(match) || match.includes(folderName)
      );
    });

    if (!companyEntry || !companyEntry.jsonFileId) {
      return NextResponse.json(
        { error: 'Company not found', ticker },
        { status: 404 }
      );
    }

    const company = await fetchFileContent<CompanyData>(companyEntry.jsonFileId);

    // Cache the result
    const ttl = getCacheTTL();
    cache.set(CACHE_KEYS.COMPANY(ticker), company, ttl);

    return NextResponse.json({
      data: company,
      source: 'drive',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error(`[API] Error fetching company ${ticker}:`, error);
    return NextResponse.json(
      {
        error: 'Failed to fetch company data',
        ticker,
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
