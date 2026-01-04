import { NextRequest, NextResponse } from 'next/server';
import { getCompanySourceFiles, isGoogleDriveConfigured } from '@/lib/google-drive';
import { cache, CACHE_KEYS, getCacheTTL } from '@/lib/cache';
import { SourceFile } from '@/lib/google-drive';

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
    const cacheKey = `files:${ticker}`;
    const cached = cache.get<SourceFile[]>(cacheKey);
    if (cached) {
      return NextResponse.json({
        data: cached,
        source: 'cache',
        timestamp: new Date().toISOString(),
      });
    }

    // Check if Google Drive is configured
    if (!isGoogleDriveConfigured()) {
      return NextResponse.json({
        data: [],
        source: 'not-configured',
        timestamp: new Date().toISOString(),
      });
    }

    // Fetch from Google Drive
    const files = await getCompanySourceFiles(ticker);

    // Cache the result
    cache.set(cacheKey, files, getCacheTTL());

    return NextResponse.json({
      data: files,
      source: 'drive',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error(`[API] Error fetching files for ${ticker}:`, error);
    return NextResponse.json(
      {
        data: [],
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}
