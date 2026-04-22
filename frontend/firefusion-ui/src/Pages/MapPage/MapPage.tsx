//import the style sheet
import './MapPage.layout.css'

//import Leaflet map library
import { useEffect } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

export default function MapPage() {
  //render map using Leaflet
  useEffect(() => {
    const map = L.map('map').setView([-37.8136, 144.9631], 13) //Coordinates for Melbourne, can change later

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map)

    return () => {
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

          {/*<div className="overlay search">Search Bar</div>   temp commenting out UI components to work on later
          <div className="overlay zoom">Zoom Controls</div>
          <div className="overlay legend">Legend</div>
          */}
        </div>
      </main>
    </div>
  )
}