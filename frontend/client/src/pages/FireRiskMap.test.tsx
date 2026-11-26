import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// ---- Fakes for the parts that are not under test -------------------------
// The page layout (sidebar, router) and the search box are not what we test here.
vi.mock('../components/Layout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))
vi.mock('../components/MapPage/SearchLocation', () => ({ default: () => null }))
vi.mock('../components/MapPage/MapLegend', () => ({ default: () => null }))
vi.mock('../components/MapPage/FullscreenMap', () => ({ default: () => null }))

// A fake WebSocket so a test can "push" a new forecast from the server.
// (vi.hoisted makes it available to vi.mock, which vitest moves to the top of the file.)
const { sockets, FakeSocket } = vi.hoisted(() => {
  const sockets: Array<{ onmessage: ((e: { data: string }) => void) | null }> = []
  class FakeSocket {
    onmessage: ((e: { data: string }) => void) | null = null
    onerror: ((e: unknown) => void) | null = null
    constructor(public url: string) {
      sockets.push(this)
    }
    close() {}
  }
  return { sockets, FakeSocket }
})
vi.mock('reconnecting-websocket', () => ({ default: FakeSocket }))

import FireRiskMap from './FireRiskMap'

// ---- Sample forecasts ----------------------------------------------------
const NOW = Date.parse('2026-11-27T12:00:00Z')
const minutesAgo = (m: number) => new Date(NOW - m * 60_000).toISOString()

const square = (lon: number, lat: number) => ({
  type: 'Polygon',
  coordinates: [[[lon, lat], [lon + 0.1, lat], [lon + 0.1, lat + 0.1], [lon, lat + 0.1], [lon, lat]]],
})

const feature = (risk: number, lon: number) => ({
  type: 'Feature',
  geometry: square(lon, -37.5),
  properties: { risk_factor: risk, fire_probability: 0.5 },
})

const forecast = (metadata?: Record<string, unknown>, risks = [1, 3]) => ({
  type: 'FeatureCollection',
  features: risks.map((r, i) => feature(r, 142 + i * 0.3)),
  ...(metadata ? { metadata } : {}),
})

const liveMeta = (ageMinutes = 5) => ({
  generated_at: minutesAgo(ageMinutes),
  source: 'live',
  stale_after_seconds: 7200,
})

// ---- Helpers -------------------------------------------------------------
const jsonResponse = (body: unknown, status = 200) =>
  Promise.resolve({ ok: status >= 200 && status < 300, status, json: () => Promise.resolve(body) })

const mockFetch = (impl: () => Promise<unknown>) => {
  const fn = vi.fn(impl)
  vi.stubGlobal('fetch', fn)
  return fn
}

const badge = () => screen.getByTestId('forecast-status-badge')
const polygons = () => document.querySelectorAll('path.leaflet-interactive')

beforeEach(() => {
  sockets.length = 0
  vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval', 'Date'] })
  vi.setSystemTime(NOW)
  vi.spyOn(console, 'error').mockImplementation(() => {}) // the page logs failures on purpose
  vi.spyOn(console, 'log').mockImplementation(() => {})
})

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

// ---- 1. Successful forecast rendering -------------------------------------
describe('Fire Risk Map: successful forecast', () => {
  it('draws one polygon for each forecast area', async () => {
    mockFetch(() => jsonResponse(forecast(liveMeta())))
    render(<FireRiskMap />)
    await waitFor(() => expect(polygons()).toHaveLength(2))
  })

  it('colours polygons by risk (1 is the most severe)', async () => {
    mockFetch(() => jsonResponse(forecast(liveMeta(), [1, 2, 3, 4, 5])))
    render(<FireRiskMap />)
    await waitFor(() => expect(polygons()).toHaveLength(5))
    const colours = Array.from(polygons()).map((p) => p.getAttribute('stroke'))
    expect(colours).toEqual(['#cc2e2e', '#cd5c00', '#ffd043', '#37d90f', '#95a5a6'])
  })

  it('shows Live when the backend says live and the data is recent', async () => {
    mockFetch(() => jsonResponse(forecast(liveMeta(5))))
    render(<FireRiskMap />)
    await waitFor(() => expect(badge()).toHaveAttribute('data-status', 'live'))
    expect(badge()).toHaveTextContent('Updated 5 min ago')
  })

  it('shows Stale when the data is older than the backend limit', async () => {
    mockFetch(() => jsonResponse(forecast(liveMeta(3 * 60))))
    render(<FireRiskMap />)
    await waitFor(() => expect(badge()).toHaveAttribute('data-status', 'stale'))
    expect(polygons()).toHaveLength(2) // old data is still drawn, just clearly labelled
  })

  it('turns Live into Stale by itself as time passes', async () => {
    mockFetch(() => jsonResponse(forecast(liveMeta(119)))) // 1 minute before the 2 hour limit
    render(<FireRiskMap />)
    await waitFor(() => expect(badge()).toHaveAttribute('data-status', 'live'))
    await act(async () => {
      vi.advanceTimersByTime(3 * 60_000)
    })
    expect(badge()).toHaveAttribute('data-status', 'stale')
  })

  it('applies a live update pushed over the WebSocket', async () => {
    mockFetch(() => jsonResponse(forecast(liveMeta(), [1])))
    render(<FireRiskMap />)
    await waitFor(() => expect(polygons()).toHaveLength(1))

    act(() => {
      sockets[0].onmessage?.({ data: JSON.stringify(forecast(liveMeta(0), [2, 3, 4])) })
    })
    await waitFor(() => expect(polygons()).toHaveLength(3))
    expect(badge()).toHaveAttribute('data-status', 'live')
  })
})

// ---- 2. Sample and unproven data is never shown as live --------------------
describe('Fire Risk Map: sample and unproven data', () => {
  it('shows Sample, never Live, when the backend says sample', async () => {
    mockFetch(() => jsonResponse(forecast({ ...liveMeta(1), source: 'sample' })))
    render(<FireRiskMap />)
    await waitFor(() => expect(badge()).toHaveAttribute('data-status', 'sample'))
    expect(badge()).not.toHaveTextContent(/^Live/)
    expect(polygons()).toHaveLength(2)
  })

  it('shows Unverified when the backend sends no freshness information', async () => {
    mockFetch(() => jsonResponse(forecast()))
    render(<FireRiskMap />)
    await waitFor(() => expect(badge()).toHaveAttribute('data-status', 'unverified'))
  })

  it('shows Unverified, not Live, for an unknown source', async () => {
    mockFetch(() => jsonResponse(forecast({ ...liveMeta(), source: 'mock' })))
    render(<FireRiskMap />)
    await waitFor(() => expect(badge()).toHaveAttribute('data-status', 'unverified'))
  })

  it('a WebSocket update labelled sample replaces a live label', async () => {
    mockFetch(() => jsonResponse(forecast(liveMeta())))
    render(<FireRiskMap />)
    await waitFor(() => expect(badge()).toHaveAttribute('data-status', 'live'))
    act(() => {
      sockets[0].onmessage?.({ data: JSON.stringify(forecast({ ...liveMeta(0), source: 'sample' })) })
    })
    await waitFor(() => expect(badge()).toHaveAttribute('data-status', 'sample'))
  })
})

// ---- 3. Loading state ------------------------------------------------------
describe('Fire Risk Map: loading', () => {
  it('shows Loading while the forecast request is still running', () => {
    mockFetch(() => new Promise(() => {})) // never finishes
    render(<FireRiskMap />)
    expect(badge()).toHaveAttribute('data-status', 'loading')
    expect(badge()).toHaveTextContent('Loading forecast')
  })

  it('leaves the loading state once the forecast arrives', async () => {
    mockFetch(() => jsonResponse(forecast(liveMeta())))
    render(<FireRiskMap />)
    expect(badge()).toHaveAttribute('data-status', 'loading')
    await waitFor(() => expect(badge()).not.toHaveAttribute('data-status', 'loading'))
  })
})

// ---- 4. Unavailable states -------------------------------------------------
describe('Fire Risk Map: unavailable forecast', () => {
  it('shows Unavailable for a 503 response and draws nothing', async () => {
    mockFetch(() => jsonResponse({ detail: 'Forecast data temporarily unavailable' }, 503))
    render(<FireRiskMap />)
    await waitFor(() => expect(badge()).toHaveAttribute('data-status', 'unavailable'))
    expect(badge()).toHaveTextContent('could not be loaded')
    expect(polygons()).toHaveLength(0)
  })

  it('shows Unavailable for a 503 even if the body looks like a valid forecast', async () => {
    // e.g. a proxy or cache that answers with an old body but an error status
    mockFetch(() => jsonResponse(forecast(liveMeta()), 503))
    render(<FireRiskMap />)
    await waitFor(() => expect(badge()).toHaveAttribute('data-status', 'unavailable'))
    expect(polygons()).toHaveLength(0)
  })

  it('shows Unavailable when the network request fails', async () => {
    mockFetch(() => Promise.reject(new TypeError('Failed to fetch')))
    render(<FireRiskMap />)
    await waitFor(() => expect(badge()).toHaveAttribute('data-status', 'unavailable'))
  })

  it('shows Unavailable when the server answers 200 with a bare null', async () => {
    mockFetch(() => jsonResponse(null))
    render(<FireRiskMap />)
    await waitFor(() => expect(badge()).toHaveAttribute('data-status', 'unavailable'))
  })

  it('shows Unavailable when the answer is not a FeatureCollection', async () => {
    mockFetch(() => jsonResponse({ hello: 'world' }))
    render(<FireRiskMap />)
    await waitFor(() => expect(badge()).toHaveAttribute('data-status', 'unavailable'))
  })

  it('shows Unavailable, with its own message, for an empty forecast', async () => {
    mockFetch(() => jsonResponse({ type: 'FeatureCollection', features: [] }))
    render(<FireRiskMap />)
    await waitFor(() => expect(badge()).toHaveAttribute('data-status', 'unavailable'))
    expect(badge()).toHaveTextContent('No forecast data is available')
  })

  it('does not show Live for an empty forecast even if it claims to be live', async () => {
    mockFetch(() => jsonResponse({ ...forecast(liveMeta()), features: [] }))
    render(<FireRiskMap />)
    await waitFor(() => expect(badge()).toHaveAttribute('data-status', 'unavailable'))
  })

  it('recovers when Try again is pressed and the backend is back', async () => {
    const fetchMock = mockFetch(() => jsonResponse({ detail: 'down' }, 503))
    render(<FireRiskMap />)
    await waitFor(() => expect(badge()).toHaveAttribute('data-status', 'unavailable'))

    fetchMock.mockImplementation(() => jsonResponse(forecast(liveMeta())) as Promise<never>)
    await userEvent.click(screen.getByRole('button', { name: 'Try again' }))

    await waitFor(() => expect(badge()).toHaveAttribute('data-status', 'live'))
    expect(polygons()).toHaveLength(2)
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })
})
