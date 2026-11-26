import { describe, it, expect } from 'vitest'
import { getForecastStatus, formatAge, DEFAULT_STALE_AFTER_SECONDS } from './forecastStatus'

const NOW = Date.parse('2026-11-25T12:00:00Z')
const minutesAgo = (m: number) => new Date(NOW - m * 60_000).toISOString()
const base = { loading: false, failed: false, empty: false, now: NOW }

describe('getForecastStatus: successful response', () => {
  it('is live when the data is real and recent', () => {
    const metadata = { source: 'live', generated_at: minutesAgo(5), stale_after_seconds: 7200 }
    expect(getForecastStatus({ ...base, metadata })).toBe('live')
  })

  it('is live when the data is exactly at the limit', () => {
    const metadata = { source: 'live', generated_at: minutesAgo(120), stale_after_seconds: 7200 }
    expect(getForecastStatus({ ...base, metadata })).toBe('live')
  })

  it('is live when the timestamp is a minute in the future (clock difference)', () => {
    const metadata = { source: 'live', generated_at: minutesAgo(-1), stale_after_seconds: 7200 }
    expect(getForecastStatus({ ...base, metadata })).toBe('live')
  })
})

describe('getForecastStatus: delayed / old data', () => {
  it('is stale when older than the backend limit', () => {
    const metadata = { source: 'live', generated_at: minutesAgo(30), stale_after_seconds: 600 }
    expect(getForecastStatus({ ...base, metadata })).toBe('stale')
  })

  it('uses the default limit when the backend sends none', () => {
    const limitMinutes = DEFAULT_STALE_AFTER_SECONDS / 60
    const fresh = { source: 'live', generated_at: minutesAgo(limitMinutes - 1) }
    const old = { source: 'live', generated_at: minutesAgo(limitMinutes + 1) }
    expect(getForecastStatus({ ...base, metadata: fresh })).toBe('live')
    expect(getForecastStatus({ ...base, metadata: old })).toBe('stale')
  })

  it('shows loading while the request is still running', () => {
    expect(getForecastStatus({ ...base, loading: true, metadata: null })).toBe('loading')
  })
})

describe('getForecastStatus: failed response', () => {
  it('is unavailable when the request failed', () => {
    expect(getForecastStatus({ ...base, failed: true, metadata: null })).toBe('unavailable')
  })

  it('is unavailable when the request failed, even if old metadata exists', () => {
    const metadata = { source: 'live', generated_at: minutesAgo(1), stale_after_seconds: 7200 }
    expect(getForecastStatus({ ...base, failed: true, metadata })).toBe('unavailable')
  })

  it('is unavailable when the forecast has no features', () => {
    const metadata = { source: 'live', generated_at: minutesAgo(1), stale_after_seconds: 7200 }
    expect(getForecastStatus({ ...base, empty: true, metadata })).toBe('unavailable')
  })
})

describe('getForecastStatus: sample data is never shown as live', () => {
  it('is sample when the backend says sample, even with a fresh timestamp', () => {
    const metadata = { source: 'sample', generated_at: minutesAgo(0), stale_after_seconds: 7200 }
    expect(getForecastStatus({ ...base, metadata })).toBe('sample')
  })

  it('is sample when the backend says sample and sends no timestamp', () => {
    expect(getForecastStatus({ ...base, metadata: { source: 'sample' } })).toBe('sample')
  })

  it('is unverified when there is no metadata at all', () => {
    expect(getForecastStatus({ ...base, metadata: null })).toBe('unverified')
    expect(getForecastStatus({ ...base, metadata: undefined })).toBe('unverified')
  })

  it('is unverified when the source field is missing', () => {
    expect(getForecastStatus({ ...base, metadata: { generated_at: minutesAgo(1) } })).toBe('unverified')
  })

  it('is unverified for an unknown source such as "mock"', () => {
    const metadata = { source: 'mock', generated_at: minutesAgo(1) }
    expect(getForecastStatus({ ...base, metadata })).toBe('unverified')
  })

  it('is unverified when the timestamp is missing', () => {
    expect(getForecastStatus({ ...base, metadata: { source: 'live' } })).toBe('unverified')
  })

  it('is unverified when the timestamp is nonsense', () => {
    expect(getForecastStatus({ ...base, metadata: { source: 'live', generated_at: 'banana' } })).toBe('unverified')
  })

  it('is unverified when the timestamp is far in the future', () => {
    const metadata = { source: 'live', generated_at: minutesAgo(-120) }
    expect(getForecastStatus({ ...base, metadata })).toBe('unverified')
  })
})

describe('formatAge', () => {
  it('formats minutes, hours and days', () => {
    expect(formatAge(minutesAgo(0), NOW)).toBe('just now')
    expect(formatAge(minutesAgo(5), NOW)).toBe('5 min ago')
    expect(formatAge(minutesAgo(180), NOW)).toBe('3 h ago')
    expect(formatAge(minutesAgo(60 * 24 * 3), NOW)).toBe('3 days ago')
  })

  it('returns null when the time is missing or invalid', () => {
    expect(formatAge(undefined, NOW)).toBeNull()
    expect(formatAge('banana', NOW)).toBeNull()
  })
})
