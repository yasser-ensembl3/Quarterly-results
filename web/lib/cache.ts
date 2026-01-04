interface CacheEntry<T> {
  data: T;
  expiresAt: number;
}

class MemoryCache {
  private cache: Map<string, CacheEntry<unknown>> = new Map();
  private defaultTTL: number = 5 * 60 * 1000; // 5 minutes

  set<T>(key: string, data: T, ttlMs?: number): void {
    const now = Date.now();
    this.cache.set(key, {
      data,
      expiresAt: now + (ttlMs ?? this.defaultTTL),
    });
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return null;
    }

    return entry.data as T;
  }

  has(key: string): boolean {
    return this.get(key) !== null;
  }

  delete(key: string): void {
    this.cache.delete(key);
  }

  clear(): void {
    this.cache.clear();
  }

  keys(): string[] {
    return Array.from(this.cache.keys());
  }
}

export const cache = new MemoryCache();

export const CACHE_KEYS = {
  ALL_COMPANIES: 'companies:all',
  COMPANY: (ticker: string) => `companies:${ticker.toUpperCase()}`,
  QUARTER_STRUCTURE: 'drive:quarter',
} as const;

export const CACHE_TTL = {
  COMPANIES: 5 * 60 * 1000,      // 5 minutes
  STRUCTURE: 30 * 60 * 1000,     // 30 minutes
  DEVELOPMENT: 60 * 1000,        // 1 minute
} as const;

export function getCacheTTL(): number {
  return process.env.NODE_ENV === 'development'
    ? CACHE_TTL.DEVELOPMENT
    : CACHE_TTL.COMPANIES;
}
