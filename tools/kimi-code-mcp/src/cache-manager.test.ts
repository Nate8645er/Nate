import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { CacheManager, resetGlobalCacheManager, getGlobalCacheManager } from './cache-manager.js'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Create a CacheManager with short TTL for testing */
function createTestCache(overrides?: {
  maxSize?: number
  maxAgeMs?: number
  debug?: boolean
}) {
  return new CacheManager({
    maxSize: overrides?.maxSize ?? 5,
    maxAgeMs: overrides?.maxAgeMs ?? 5_000,
    debug: overrides?.debug ?? false,
  })
}

/**
 * Stub the private warmupCache method so tests don't spawn real Kimi processes.
 * Returns a fake session ID after a short delay.
 */
function stubWarmup(
  cache: CacheManager,
  opts?: { sessionId?: string; delayMs?: number; fail?: boolean }
) {
  const sessionId = opts?.sessionId ?? `fake-${Math.random().toString(36).slice(2, 10)}-0000-0000-000000000000`
  const delayMs = opts?.delayMs ?? 10
  const fail = opts?.fail ?? false

  // @ts-expect-error — accessing private method for testing
  cache.warmupCache = vi.fn(async () => {
    await new Promise(r => setTimeout(r, delayMs))
    if (fail) throw new Error('warmup failed')
    return sessionId
  })

  return sessionId
}

/**
 * Stub computeCodebaseHash to return a predictable value.
 * Optionally changes on nth call to simulate codebase change.
 */
function stubHash(cache: CacheManager, values?: string[]) {
  let callCount = 0
  const hashes = values ?? ['hash-v1']
  // @ts-expect-error — accessing private method for testing
  cache.computeCodebaseHash = vi.fn(async () => {
    const hash = hashes[Math.min(callCount, hashes.length - 1)]
    callCount++
    return hash
  })
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('CacheManager', () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    resetGlobalCacheManager()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  // =========================================================================
  // F1: Session Creation and Caching
  // =========================================================================
  describe('F1 — Session Creation and Caching', () => {
    it('TC-F1-001: first call creates cache (miss)', async () => {
      const cache = createTestCache()
      const sid = stubWarmup(cache)
      stubHash(cache)

      const result = await cache.getOrCreateSession('/project/a')

      expect(result.hit).toBe(false)
      expect(result.sessionId).toBe(sid)
      expect(cache.getStats().totalEntries).toBe(1)
      expect(cache.getStats().totalMisses).toBe(1)
    })

    it('TC-F1-002: session ID is persisted and retrievable', async () => {
      const cache = createTestCache()
      const sid = stubWarmup(cache)
      stubHash(cache)

      await cache.getOrCreateSession('/project/a')
      const entries = cache.listEntries()

      expect(entries).toHaveLength(1)
      expect(entries[0].sessionId).toBe(sid)
      expect(entries[0].workDir).toContain('project/a')
    })
  })

  // =========================================================================
  // F2: Cache Hit Detection and Reuse
  // =========================================================================
  describe('F2 — Cache Hit Detection and Reuse', () => {
    it('TC-F2-001: second call hits cache', async () => {
      const cache = createTestCache()
      stubWarmup(cache)
      stubHash(cache)

      const r1 = await cache.getOrCreateSession('/project/b')
      expect(r1.hit).toBe(false)

      const r2 = await cache.getOrCreateSession('/project/b')
      expect(r2.hit).toBe(true)
      expect(r2.sessionId).toBe(r1.sessionId)

      const stats = cache.getStats()
      expect(stats.totalHits).toBe(1)
      expect(stats.totalMisses).toBe(1)
    })

    it('TC-F2-003: use_cache=false bypass is handled by caller (CacheManager always caches)', async () => {
      // Note: use_cache=false is handled in index.ts, not CacheManager.
      // CacheManager itself always creates entries. This test verifies the entry exists.
      const cache = createTestCache()
      stubWarmup(cache)
      stubHash(cache)

      await cache.getOrCreateSession('/project/c')
      expect(cache.getStats().totalEntries).toBe(1)
    })
  })

  // =========================================================================
  // F3: Cache Expiration (Time-based)
  // =========================================================================
  describe('F3 — Cache Expiration', () => {
    it('TC-F3-001: cache expires after maxAgeMs', async () => {
      const cache = createTestCache({ maxAgeMs: 5_000 })
      stubWarmup(cache)
      stubHash(cache)

      await cache.getOrCreateSession('/project/d')

      // Advance past TTL
      vi.advanceTimersByTime(6_000)

      const r2 = await cache.getOrCreateSession('/project/d')
      expect(r2.hit).toBe(false) // expired → miss
      expect(cache.getStats().totalMisses).toBe(2)
    })

    it('TC-F3-002-KNOWN-BUG: cache access does NOT reset expiration (uses createdAt)', async () => {
      // BUG: isValid() compares Date.now() - entry.createdAt, not lastUsedAt.
      // This test documents the current (buggy) behavior.
      const cache = createTestCache({ maxAgeMs: 5_000 })
      stubWarmup(cache)
      stubHash(cache)

      await cache.getOrCreateSession('/project/e')         // t=0, miss

      vi.advanceTimersByTime(2_500)                         // t=2.5s
      const r2 = await cache.getOrCreateSession('/project/e') // hit
      expect(r2.hit).toBe(true)

      vi.advanceTimersByTime(3_000)                         // t=5.5s (>5s from creation)
      const r3 = await cache.getOrCreateSession('/project/e')
      // BUG: This should be a HIT if TTL refreshes on access, but is a MISS
      expect(r3.hit).toBe(false) // current behavior — createdAt-based expiry
    })
  })

  // =========================================================================
  // F4: Codebase Change Detection
  // =========================================================================
  describe('F4 — Codebase Change Detection', () => {
    it('TC-F4-001: cache invalidated when codebase hash changes', async () => {
      const cache = createTestCache()
      stubWarmup(cache)
      // First call gets 'hash-v1', validation + second call gets 'hash-v2'
      stubHash(cache, ['hash-v1', 'hash-v2'])

      const r1 = await cache.getOrCreateSession('/project/f')
      expect(r1.hit).toBe(false)

      const r2 = await cache.getOrCreateSession('/project/f')
      expect(r2.hit).toBe(false) // codebase changed → miss
      expect(cache.getStats().totalMisses).toBe(2)
    })

    it('TC-F4-002: unchanged hash → cache hit', async () => {
      const cache = createTestCache()
      stubWarmup(cache)
      stubHash(cache, ['same-hash', 'same-hash', 'same-hash'])

      await cache.getOrCreateSession('/project/g')
      const r2 = await cache.getOrCreateSession('/project/g')
      expect(r2.hit).toBe(true)
    })
  })

  // =========================================================================
  // F5: LRU Eviction Policy
  // =========================================================================
  describe('F5 — LRU Eviction', () => {
    it('TC-F5-001: oldest entry evicted when maxSize exceeded', async () => {
      const cache = createTestCache({ maxSize: 3 })
      stubHash(cache)

      // Create 3 entries
      stubWarmup(cache, { sessionId: 'sid-1' })
      await cache.getOrCreateSession('/p1')
      stubWarmup(cache, { sessionId: 'sid-2' })
      await cache.getOrCreateSession('/p2')
      stubWarmup(cache, { sessionId: 'sid-3' })
      await cache.getOrCreateSession('/p3')

      expect(cache.getStats().totalEntries).toBe(3)

      // Add 4th → should evict /p1
      stubWarmup(cache, { sessionId: 'sid-4' })
      await cache.getOrCreateSession('/p4')

      expect(cache.getStats().totalEntries).toBe(3)
      expect(cache.getStats().totalEvictions).toBe(1)

      const dirs = cache.listEntries().map(e => e.workDir)
      expect(dirs).not.toContainEqual(expect.stringContaining('/p1'))
    })

    it('TC-F5-002: access updates LRU order', async () => {
      const cache = createTestCache({ maxSize: 3 })
      stubHash(cache)

      stubWarmup(cache, { sessionId: 'sid-1' })
      await cache.getOrCreateSession('/p1')
      vi.advanceTimersByTime(100)

      stubWarmup(cache, { sessionId: 'sid-2' })
      await cache.getOrCreateSession('/p2')
      vi.advanceTimersByTime(100)

      stubWarmup(cache, { sessionId: 'sid-3' })
      await cache.getOrCreateSession('/p3')
      vi.advanceTimersByTime(100)

      // Access /p1 → moves it to most recent
      await cache.getOrCreateSession('/p1')
      vi.advanceTimersByTime(100)

      // Add /p4 → should evict /p2 (least recently used)
      stubWarmup(cache, { sessionId: 'sid-4' })
      await cache.getOrCreateSession('/p4')

      const dirs = cache.listEntries().map(e => e.workDir)
      expect(dirs).not.toContainEqual(expect.stringContaining('/p2'))
      expect(dirs).toContainEqual(expect.stringContaining('/p1'))
    })
  })

  // =========================================================================
  // F6: Cache Status Monitoring
  // =========================================================================
  describe('F6 — Cache Status', () => {
    it('TC-F6-001: initial stats are zero', () => {
      const cache = createTestCache()
      const stats = cache.getStats()

      expect(stats.totalEntries).toBe(0)
      expect(stats.totalHits).toBe(0)
      expect(stats.totalMisses).toBe(0)
      expect(stats.totalEvictions).toBe(0)
    })

    it('TC-F6-002: stats reflect operations', async () => {
      const cache = createTestCache()
      stubWarmup(cache)
      stubHash(cache)

      await cache.getOrCreateSession('/project/h')   // miss
      await cache.getOrCreateSession('/project/h')   // hit

      const stats = cache.getStats()
      expect(stats.totalEntries).toBe(1)
      expect(stats.totalHits).toBe(1)
      expect(stats.totalMisses).toBe(1)
    })

    it('TC-F6-003: listEntries returns entry details', async () => {
      const cache = createTestCache()
      const sid = stubWarmup(cache)
      stubHash(cache)

      await cache.getOrCreateSession('/project/i')
      await cache.getOrCreateSession('/project/i') // hit → hitCount=1

      const entries = cache.listEntries()
      expect(entries).toHaveLength(1)
      expect(entries[0].sessionId).toBe(sid)
      expect(entries[0].hitCount).toBe(1)
      expect(entries[0].lastUsedAt).toBeGreaterThan(0)
    })
  })

  // =========================================================================
  // F7: Manual Cache Invalidation
  // =========================================================================
  describe('F7 — Manual Invalidation', () => {
    it('TC-F7-001: invalidate specific directory', async () => {
      const cache = createTestCache()
      stubWarmup(cache)
      stubHash(cache)

      await cache.getOrCreateSession('/project/j')
      stubWarmup(cache, { sessionId: 'other-sid' })
      await cache.getOrCreateSession('/project/k')

      const existed = cache.invalidate('/project/j')
      expect(existed).toBe(true)
      expect(cache.getStats().totalEntries).toBe(1)

      const dirs = cache.listEntries().map(e => e.workDir)
      expect(dirs).not.toContainEqual(expect.stringContaining('/project/j'))
    })

    it('TC-F7-002: invalidateAll clears everything', async () => {
      const cache = createTestCache()
      stubWarmup(cache)
      stubHash(cache)

      await cache.getOrCreateSession('/project/l')
      stubWarmup(cache, { sessionId: 'sid-2' })
      await cache.getOrCreateSession('/project/m')

      const count = cache.invalidateAll()
      expect(count).toBe(2)
      expect(cache.getStats().totalEntries).toBe(0)
    })

    it('TC-F7-003: invalidate non-existent returns false', () => {
      const cache = createTestCache()
      const existed = cache.invalidate('/nonexistent')
      expect(existed).toBe(false)
    })
  })

  // =========================================================================
  // F8: Error Handling and Recovery
  // =========================================================================
  describe('F8 — Error Handling', () => {
    it('TC-F8-001: warmup failure throws, cache stays clean', async () => {
      const cache = createTestCache()
      stubWarmup(cache, { fail: true })
      stubHash(cache)

      await expect(cache.getOrCreateSession('/project/n'))
        .rejects.toThrow('warmup failed')

      expect(cache.getStats().totalEntries).toBe(0)
    })

    it('TC-F8-002: warmup returns undefined sessionId → no entry created', async () => {
      const cache = createTestCache()
      // @ts-expect-error — accessing private method
      cache.warmupCache = vi.fn(async () => undefined)
      stubHash(cache)

      const result = await cache.getOrCreateSession('/project/o')
      expect(result.sessionId).toBeUndefined()
      expect(cache.getStats().totalEntries).toBe(0)
    })
  })

  // =========================================================================
  // NF1: Concurrent Access (Race condition tests)
  // =========================================================================
  describe('NF1 — Concurrent Access', () => {
    it('TC-NF1-001: concurrent requests for EXISTING cache key — only 1 warmup', async () => {
      const cache = createTestCache()
      stubHash(cache)

      // Pre-populate an expired entry to trigger isWarming guard
      // @ts-expect-error — accessing private field
      cache.cache.set('/project/p', {
        sessionId: 'old-sid',
        workDir: '/project/p',
        codebaseHash: 'old-hash',
        createdAt: 0, // expired
        lastUsedAt: 0,
        hitCount: 0,
        isWarming: false,
      })

      const warmupFn = vi.fn(async () => {
        await new Promise(r => setTimeout(r, 200))
        return 'new-sid'
      })
      // @ts-expect-error — accessing private method
      cache.warmupCache = warmupFn

      // Fire 3 concurrent requests
      const promises = [
        cache.getOrCreateSession('/project/p'),
        cache.getOrCreateSession('/project/p'),
        cache.getOrCreateSession('/project/p'),
      ]

      vi.advanceTimersByTime(300)
      const results = await Promise.all(promises)

      // Only 1 warmup should have been called
      expect(warmupFn).toHaveBeenCalledTimes(1)
      expect(results.every(r => r.sessionId === 'new-sid')).toBe(true)
    })

    it('TC-NF1-002-KNOWN-BUG: concurrent requests for NEW key — both start warmup', async () => {
      // BUG: No isWarming guard for non-existing entries
      const cache = createTestCache()
      stubHash(cache)

      let warmupCount = 0
      // @ts-expect-error — accessing private method
      cache.warmupCache = vi.fn(async () => {
        warmupCount++
        await new Promise(r => setTimeout(r, 200))
        return `sid-${warmupCount}`
      })

      const p1 = cache.getOrCreateSession('/fresh')
      const p2 = cache.getOrCreateSession('/fresh')

      vi.advanceTimersByTime(300)
      await Promise.all([p1, p2])

      // BUG: Both requests start warmup because there's no existing entry
      expect(warmupCount).toBe(2) // should be 1 if bug is fixed
    })
  })

  // =========================================================================
  // Path normalization
  // =========================================================================
  describe('Path Normalization', () => {
    it('trailing slash does not create separate cache', async () => {
      const cache = createTestCache()
      stubWarmup(cache)
      stubHash(cache)

      await cache.getOrCreateSession('/project/q/')
      const r2 = await cache.getOrCreateSession('/project/q')
      // path.resolve strips trailing slash
      expect(r2.hit).toBe(true)
    })

    it('relative path normalized to absolute', async () => {
      const cache = createTestCache()
      stubWarmup(cache)
      stubHash(cache)

      await cache.getOrCreateSession('./src')
      const entries = cache.listEntries()
      // path.resolve converts to absolute
      expect(entries[0].workDir).toMatch(/^\//)
    })
  })

  // =========================================================================
  // Singleton
  // =========================================================================
  describe('Singleton — getGlobalCacheManager', () => {
    it('returns same instance on repeated calls', () => {
      const a = getGlobalCacheManager()
      const b = getGlobalCacheManager()
      expect(a).toBe(b)
    })

    it('reset creates new instance', () => {
      const a = getGlobalCacheManager()
      resetGlobalCacheManager()
      const b = getGlobalCacheManager()
      expect(a).not.toBe(b)
    })
  })
})
