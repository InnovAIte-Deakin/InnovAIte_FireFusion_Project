import 'MapPage.css'

export default function MapPage() {
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
        <div id="map" className="map-container"></div>

        <div className="overlay-panel">
          <div className="search">Search Bar</div>
          <div className="zoom">Zoom Controls</div>
          <div className="legend">Legend</div>
        </div>
      </main>
    </div>
  )
}