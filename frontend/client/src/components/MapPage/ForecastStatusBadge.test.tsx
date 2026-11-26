import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ForecastStatusBadge from './ForecastStatusBadge'
import type { ForecastStatus } from '../../utils/forecastStatus'

const NOW = Date.parse('2026-11-27T12:00:00Z')

const labels: Array<[ForecastStatus, string]> = [
  ['loading', 'Loading forecast…'],
  ['live', 'Live'],
  ['stale', 'Stale'],
  ['sample', 'Sample data (not live)'],
  ['unverified', 'Freshness unverified'],
  ['unavailable', 'Forecast unavailable'],
]

describe('ForecastStatusBadge: every state says what it is in words', () => {
  it.each(labels)('shows the %s state', (status, label) => {
    render(<ForecastStatusBadge status={status} metadata={null} now={NOW} />)
    const badge = screen.getByTestId('forecast-status-badge')
    expect(badge).toHaveAttribute('data-status', status)
    expect(badge).toHaveTextContent(label)
  })

  it('is announced to screen readers as a polite status message', () => {
    render(<ForecastStatusBadge status="live" metadata={null} now={NOW} />)
    expect(screen.getByRole('status')).toHaveAttribute('aria-live', 'polite')
  })
})

describe('ForecastStatusBadge: details', () => {
  it('shows how old a live forecast is', () => {
    const generated = new Date(NOW - 10 * 60 * 1000).toISOString()
    render(<ForecastStatusBadge status="live" metadata={{ generated_at: generated }} now={NOW} />)
    expect(screen.getByTestId('forecast-status-badge')).toHaveTextContent('Updated 10 min ago')
  })

  it('warns that stale data may be out of date', () => {
    const generated = new Date(NOW - 3 * 60 * 60 * 1000).toISOString()
    render(<ForecastStatusBadge status="stale" metadata={{ generated_at: generated }} now={NOW} />)
    expect(screen.getByTestId('forecast-status-badge')).toHaveTextContent('3 h ago')
    expect(screen.getByTestId('forecast-status-badge')).toHaveTextContent('may be out of date')
  })

  it('says sample data is not a real-time forecast', () => {
    render(<ForecastStatusBadge status="sample" metadata={{ source: 'sample' }} now={NOW} />)
    expect(screen.getByTestId('forecast-status-badge')).toHaveTextContent('not a real-time forecast')
  })

  it('explains the difference between failed and empty', () => {
    const { rerender } = render(<ForecastStatusBadge status="unavailable" metadata={null} now={NOW} />)
    expect(screen.getByTestId('forecast-status-badge')).toHaveTextContent('could not be loaded')
    rerender(<ForecastStatusBadge status="unavailable" metadata={null} now={NOW} empty />)
    expect(screen.getByTestId('forecast-status-badge')).toHaveTextContent('No forecast data is available')
  })
})

describe('ForecastStatusBadge: Try again button', () => {
  it('shows the button only when the forecast is unavailable, and calls onRetry', async () => {
    const onRetry = vi.fn()
    render(<ForecastStatusBadge status="unavailable" metadata={null} now={NOW} onRetry={onRetry} />)
    await userEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(onRetry).toHaveBeenCalledTimes(1)
  })

  it.each(['loading', 'live', 'stale', 'sample', 'unverified'] as ForecastStatus[])(
    'has no button in the %s state',
    (status) => {
      render(<ForecastStatusBadge status={status} metadata={null} now={NOW} onRetry={() => {}} />)
      expect(screen.queryByRole('button')).not.toBeInTheDocument()
    },
  )
})
