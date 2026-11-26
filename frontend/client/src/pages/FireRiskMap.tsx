//import the style sheet
import '../components/MapPage/MapPage.layout.css'

//import UI components
import FullscreenMap from '../components/MapPage/FullscreenMap'
import MapLegend from '../components/MapPage/MapLegend'
import SearchLocation from '../components/MapPage/SearchLocation'
import ForecastStatusBadge from '../components/MapPage/ForecastStatusBadge'

//import forecast status logic (live / stale / unavailable)
import { getForecastStatus } from '../utils/forecastStatus'
import type { ForecastMetadata } from '../utils/forecastStatus'

//import Layout
import Layout from "../components/Layout"

//import websocket connection dependency
import ReconnectingWebSocket from 'reconnecting-websocket'

//import Leaflet
import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

export default function MapPage() {

  //store map
  const mapRef = useRef<L.Map | null>(null)

  //forecast status: what the badge needs to know
  const [loading, setLoading] = useState(true)
  const [failed, setFailed] = useState(false)
  const [empty, setEmpty] = useState(false)
  const [metadata, setMetadata] = useState<ForecastMetadata | null>(null)
  const [now, setNow] = useState(Date.now())

  //lets the "Try again" button re-run the forecast request
  const reloadRef = useRef<() => void>(() => {})

  //re-check the time every 30 seconds so "Live" turns into "Stale" by itself
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 30_000)
    return () => clearInterval(timer)
  }, [])

  //centre map from search bar
  const centerMap = (lat: number, lon: number) => {
    if (!mapRef.current) return

    mapRef.current.flyTo([lat, lon], 11, {
      duration: 1.2,
    })
  }

  useEffect(() => {

    //Create map
    const map = L.map('map', {
      zoomControl: false,
    })

    //store map so SearchLocation.jsx can use it)
    mapRef.current = map

    //Create tile
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map)

    //store current GeoJSON layer
    let geoJsonLayer: L.GeoJSON | null = null

    //map risk level to colour
    const getColor = (risk: number) => {
      switch (risk) {
        case 1: return '#cc2e2e' //extreme
        case 2: return '#cd5c00' //high
        case 3: return '#ffd043' //medium
        case 4: return '#37d90f' //low
        case 5: return '#95a5a6' //very low
        default: return '#09a2ad' //unknown
      }
    }

    //help to render GeoJSON
    const renderGeoJSON = (data: any) => {
      if (geoJsonLayer) {
        geoJsonLayer.remove()
      }

      //style polygons with the risk level colours
      geoJsonLayer = L.geoJSON(data, {
        style: (feature: any) => ({
          color: getColor(feature.properties?.risk_factor),
          fillColor: getColor(feature.properties?.risk_factor),
          fillOpacity: 0.4,
          weight: 2,
        }),
        onEachFeature: (feature, layer) => {
          if (feature.properties) {
            const popupContent = `<b>Risk Level:</b> ${feature.properties.risk_factor}`
            layer.bindPopup(popupContent)
          }
        },
      }).addTo(map)

      //centre map to wherever polygons are
      const bounds = geoJsonLayer.getBounds()
      if (bounds.isValid()) {
        map.fitBounds(bounds, {
          padding: [20, 20],
        })
      }
    }

    //accept a forecast (from the first request or the WebSocket) and update the status
    const acceptForecast = (data: any) => {
      //a bare null or anything that is not a FeatureCollection is NOT a usable forecast
      if (!data || !Array.isArray(data.features)) {
        throw new Error('Forecast response was not a GeoJSON FeatureCollection')
      }

      renderGeoJSON(data)
      setMetadata(data.metadata ?? null)
      setEmpty(data.features.length === 0)
      setFailed(false)
    }

    //Load initial data
    const loadGeoJSON = async () => {
      setLoading(true)
      try {
        const response = await fetch('/api/bushfire-forecast')

        //a 503 or 500 must be treated as a failure, not as map data
        if (!response.ok) {
          throw new Error(`Forecast request failed with status ${response.status}`)
        }

        const data = await response.json()
        acceptForecast(data)
      } catch (error) {
        console.error('Error loading GeoJSON:', error)
        setFailed(true)
      } finally {
        setLoading(false)
      }
    }

    reloadRef.current = loadGeoJSON
    loadGeoJSON()

    //WebSocket set up for live updates
    const ws = new ReconnectingWebSocket('/api/ws')

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        acceptForecast(data)
      } catch (error) {
        console.error('WebSocket data error:', error)
      }
    }

    ws.onerror = (err) => {
      console.error('WebSocket error:', err)
    }

    return () => {
      ws.close()
      map.remove()
    }
  }, [])

  //work out which badge to show
  const status = getForecastStatus({ loading, failed, empty, metadata, now })

  //remove topbar for now, change showTopbar to true to show
  return (
    <Layout title="Fire Map" showTopbar={false}>
      <div className="map-page">

        <SearchLocation
          onSelect={(location) => {
            console.log(location)

            //validate location and recentre map
            if (location?.lat && location?.lon) {
              centerMap(location.lat, location.lon)
            }
          }}
        />

        <MapLegend />

        <ForecastStatusBadge
          status={status}
          metadata={metadata}
          now={now}
          empty={empty}
          onRetry={() => reloadRef.current()}
        />

        <div className="map-main">
          <div id="map"></div>
        </div>

      </div>
    </Layout>
  )
}
