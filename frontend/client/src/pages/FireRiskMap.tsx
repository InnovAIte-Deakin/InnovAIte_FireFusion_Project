//import the style sheet
import '../components/MapPage/MapPage.layout.css'

//import UI components
import FullscreenMap from '../components/MapPage/FullscreenMap'
import MapLegend from '../components/MapPage/MapLegend'
import SearchLocation from '../components/MapPage/SearchLocation'

//import Layout
import Layout from "../components/Layout"

//import websocket connection dependency 
import ReconnectingWebSocket from 'reconnecting-websocket'

//import Leaflet
import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const SAMPLE_GEOJSON = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      properties: { risk_factor: 1 },
      geometry: {
        type: "Polygon",
        coordinates: [[[147.15, -37.56], [147.72, -37.74], [147.91, -37.25], [147.38, -37.11], [147.15, -37.56]]]
      }
    },
    {
      type: "Feature",
      properties: { risk_factor: 2 },
      geometry: {
        type: "Polygon",
        coordinates: [[[142.15, -37.16], [142.62, -37.44], [142.81, -37.05], [142.38, -36.91], [142.15, -37.16]]]
      }
    },
    {
      type: "Feature",
      properties: { risk_factor: 3 },
      geometry: {
        type: "Polygon",
        coordinates: [[[145.15, -37.86], [145.42, -37.94], [145.61, -37.65], [145.28, -37.51], [145.15, -37.86]]]
      }
    },
    {
      type: "Feature",
      properties: { risk_factor: 4 },
      geometry: {
        type: "Polygon",
        coordinates: [[[143.55, -38.12], [143.92, -38.31], [144.11, -38.05], [143.78, -37.88], [143.55, -38.12]]]
      }
    }
  ]
}

export default function MapPage() {

  //store map
  const mapRef = useRef<L.Map | null>(null)

  //centre map from search bar
  const centerMap = (lat: number, lon: number) => {
    if (!mapRef.current) return

    mapRef.current.flyTo([lat, lon], 11, {
      duration: 1.2,
    })
  }

  useEffect(() => {

    //Create map centered on Victoria, Australia
    const map = L.map('map', {
      zoomControl: false,
    }).setView([-37.0, 144.5], 7)

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
      try {
        const bounds = geoJsonLayer.getBounds()
        if (bounds && typeof bounds.isValid === 'function' && bounds.isValid()) {
          map.fitBounds(bounds, {
            padding: [20, 20],
          })
        }
      } catch (e) {
        console.warn('Could not fit bounds of GeoJSON layer:', e)
      }
    }

    //Load initial data
    const loadGeoJSON = async () => {
      try {
        const response = await fetch('/api/bushfire-forecast')
        if (!response.ok) throw new Error(`HTTP error ${response.status}`)
        const data = await response.json()

        renderGeoJSON(data)
      } catch (error) {
        console.warn('Backend API offline, rendering fallback Victoria risk map:', error)
        renderGeoJSON(SAMPLE_GEOJSON)
      }
    }

    loadGeoJSON()

    //WebSocket set up for live updates
    const ws = new ReconnectingWebSocket('/api/ws')

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        if (geoJsonLayer) {
          geoJsonLayer.remove()
        }

        geoJsonLayer = L.geoJSON(data, {
          style: (feature: any) => ({
            color: getColor(feature.properties?.risk_factor),
            fillColor: getColor(feature.properties?.risk_factor),
            fillOpacity: 0.4,
            weight: 2,
          }),
        }).addTo(map)

        try {
          const bounds = geoJsonLayer.getBounds()
          if (bounds && typeof bounds.isValid === 'function' && bounds.isValid()) {
            map.fitBounds(bounds, {
              padding: [20, 20],
            })
          }
        } catch (e) {
          console.warn('Could not fit bounds of GeoJSON layer in WS update:', e)
        }
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

        <div className="map-main">
          <div id="map"></div>
        </div>

      </div>
    </Layout>
  )
}