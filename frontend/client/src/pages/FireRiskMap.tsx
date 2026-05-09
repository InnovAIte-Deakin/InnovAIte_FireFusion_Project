//import the style sheet
import '../components/MapPage/MapPage.layout.css'

//import websocket connection dependency 
import ReconnectingWebSocket from 'reconnecting-websocket'

//import Leaflet
import { useEffect } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

//import Layout
import Layout from "../components/Layout"

export default function MapPage() {
  useEffect(() => {
    //Create map
    const map = L.map('map', {
      zoomControl: false,
    }) 

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
        case 5: return '#95a5a6' //less than low
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

    //Load initial data
    const loadGeoJSON = async () => {
      try {
        const response = await fetch(
          'http://localhost:8080/api/bushfire-forecast'
        )
        const data = await response.json()

        renderGeoJSON(data)
      } catch (error) {
        console.error('Error loading GeoJSON:', error)
      }
    }

    loadGeoJSON()

    //WebSocket set up for live updates 
    const ws = new ReconnectingWebSocket('ws://localhost:8080/api/ws') 

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

        const bounds = geoJsonLayer.getBounds()
        if (bounds.isValid()) {
          map.fitBounds(bounds, {
            padding: [20, 20],
          })
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
        <div id="map"></div>
      </div>
    </Layout>
  )
}