// Decides which status the Fire Risk Map should show for the current forecast.
//
// The golden rule: "live" has to be PROVEN. If the map cannot prove the data is
// real and recent, it must never say "Live".

export type ForecastStatus =
  | 'loading' // waiting for the backend
  | 'live' // real data, newer than the stale limit
  | 'stale' // real data, older than the stale limit
  | 'sample' // backend says this is sample data, not a real forecast
  | 'unverified' // backend gave us no proof either way
  | 'unavailable' // request failed or there is no forecast data

// Extra block the backend adds to the forecast response (proposed contract).
export interface ForecastMetadata {
  generated_at?: string // ISO time with timezone, e.g. 2026-11-25T06:30:00+00:00
  source?: string // "live" or "sample"
  stale_after_seconds?: number // after this many seconds the data counts as stale
}

// Only used when the backend does not send stale_after_seconds.
// TODO: agree the real value with the backend team.
export const DEFAULT_STALE_AFTER_SECONDS = 2 * 60 * 60

// A timestamp slightly in the future is normal (computer clocks differ a little).
// A timestamp far in the future is not trustworthy.
const CLOCK_SKEW_MS = 5 * 60 * 1000

export interface StatusInput {
  loading: boolean
  failed: boolean
  empty: boolean
  metadata: ForecastMetadata | null | undefined
  now: number // current time in milliseconds (Date.now())
}

export function getForecastStatus({
  loading,
  failed,
  empty,
  metadata,
  now,
}: StatusInput): ForecastStatus {
  if (loading) return 'loading'
  if (failed || empty) return 'unavailable'

  // No metadata at all: we cannot prove anything, so never claim "live".
  if (!metadata) return 'unverified'

  // Sample data is never live, even if its timestamp looks fresh.
  if (metadata.source === 'sample') return 'sample'
  if (metadata.source !== 'live') return 'unverified'

  const generatedMs = metadata.generated_at ? Date.parse(metadata.generated_at) : NaN
  if (Number.isNaN(generatedMs)) return 'unverified'

  const ageMs = now - generatedMs
  if (ageMs < -CLOCK_SKEW_MS) return 'unverified'

  const limitSeconds =
    typeof metadata.stale_after_seconds === 'number' && metadata.stale_after_seconds > 0
      ? metadata.stale_after_seconds
      : DEFAULT_STALE_AFTER_SECONDS

  return ageMs > limitSeconds * 1000 ? 'stale' : 'live'
}

// Turns a timestamp into friendly text like "5 min ago". Returns null if unknown.
export function formatAge(generatedAt: string | undefined, now: number): string | null {
  if (!generatedAt) return null
  const ms = Date.parse(generatedAt)
  if (Number.isNaN(ms)) return null

  const minutes = Math.max(0, Math.floor((now - ms) / 60000))
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes} min ago`

  const hours = Math.floor(minutes / 60)
  if (hours < 48) return `${hours} h ago`

  return `${Math.floor(hours / 24)} days ago`
}
