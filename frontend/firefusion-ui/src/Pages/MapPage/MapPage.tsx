//import the style sheet
import './MapPage.layout.css'

//import Leaflet
import { useEffect } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

export default function MapPage() {
  useEffect(() => {
    //Create map
    const map = L.map('map', {
      zoomControl: false,
    }) 

    //Create tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map)

    //Store current GeoJSON layer
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
          'http://localhost/api/bushfire-forecast' //Docker proxy mapping
        )
        const data = await response.json()

        renderGeoJSON(data)
      } catch (error) {
        console.error('Error loading GeoJSON:', error)
      }
    }

    loadGeoJSON()

    //WebSocket set up for live updates - to do: debug
    const ws = new WebSocket('ws://localhost:80/api/ws') //Docker mapping

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

        //when web socket updates, centre map on new polygons
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

    //Cleanup
    return () => {
      ws.close()
      map.remove()
    }
  }, [])

  return (
    <div className="map-page">
      <aside className="sidebar">
        <h2>Menu</h2>
        <ul>
          <li>Map</li>
          <li>Settings</li>
        </ul>
      </aside>

      <main className="map-main">
        <div className="map-container">
          <div id="map"></div>

          {/*
          <div className="overlay search">Search Bar</div> can edit these back in later, temp removing UI components
          <div className="overlay zoom">Zoom Controls</div>
          <div className="overlay legend">Legend</div>
          */}
        </div>
      </main>
    </div>
  )
}