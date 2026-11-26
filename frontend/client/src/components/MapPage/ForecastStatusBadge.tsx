import type { CSSProperties } from 'react'
import { formatAge } from '../../utils/forecastStatus'
import type { ForecastMetadata, ForecastStatus } from '../../utils/forecastStatus'

interface ForecastStatusBadgeProps {
  status: ForecastStatus
  metadata: ForecastMetadata | null
  now: number
  empty?: boolean // true when the request worked but there are no forecast areas
  onRetry?: () => void
}

// Each state has an icon AND words, so it does not rely on colour alone.
const LOOK: Record<ForecastStatus, { icon: string; label: string; background: string; color: string }> = {
  loading: { icon: '⏳', label: 'Loading forecast…', background: '#eef2f5', color: '#2c3e50' },
  live: { icon: '🟢', label: 'Live', background: '#e6f6ea', color: '#176b2c' },
  stale: { icon: '🟡', label: 'Stale', background: '#fff4d6', color: '#7a5200' },
  sample: { icon: '🧪', label: 'Sample data (not live)', background: '#e8eaf6', color: '#283593' },
  unverified: { icon: '❔', label: 'Freshness unverified', background: '#eceff1', color: '#455a64' },
  unavailable: { icon: '🔴', label: 'Forecast unavailable', background: '#fdeaea', color: '#a12626' },
}

function describe(status: ForecastStatus, metadata: ForecastMetadata | null, now: number, empty?: boolean) {
  const age = formatAge(metadata?.generated_at, now)
  switch (status) {
    case 'live':
      return age ? `Updated ${age}` : ''
    case 'stale':
      return age ? `Last updated ${age}. This may be out of date.` : 'This may be out of date.'
    case 'sample':
      return 'This is example data, not a real-time forecast.'
    case 'unverified':
      return 'We cannot confirm this forecast is current.'
    case 'unavailable':
      return empty ? 'No forecast data is available right now.' : 'The forecast could not be loaded.'
    default:
      return ''
  }
}

const wrapperStyle: CSSProperties = {
  position: 'absolute',
  left: 16,
  bottom: 24,
  zIndex: 1100, // above the Leaflet map layers
  maxWidth: 320,
  padding: '8px 12px',
  borderRadius: 8,
  boxShadow: '0 2px 8px rgba(0,0,0,0.25)',
  fontFamily: 'system-ui, sans-serif',
  fontSize: 14,
  lineHeight: 1.4,
}

export default function ForecastStatusBadge({ status, metadata, now, empty, onRetry }: ForecastStatusBadgeProps) {
  const look = LOOK[status]
  const detail = describe(status, metadata, now, empty)
  const canRetry = onRetry && status === 'unavailable'

  return (
    <div
      role="status"
      aria-live="polite"
      data-testid="forecast-status-badge"
      data-status={status}
      style={{ ...wrapperStyle, background: look.background, color: look.color }}
    >
      <div style={{ fontWeight: 600 }}>
        <span aria-hidden="true">{look.icon}</span> {look.label}
      </div>
      {detail && <div style={{ fontSize: 12 }}>{detail}</div>}
      {canRetry && (
        <button type="button" onClick={onRetry} style={{ marginTop: 6, cursor: 'pointer' }}>
          Try again
        </button>
      )}
    </div>
  )
}
