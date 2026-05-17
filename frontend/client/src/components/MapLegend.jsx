const LEGEND_ITEMS = [
  { color: "#7f1d1d", label: "Catastrophic" },
  { color: "#ef4444", label: "Extreme" },
  { color: "#f97316", label: "Severe" },
  { color: "#eab308", label: "High" },
  { color: "#22c55e", label: "Low–Moderate" },
];

export default function MapLegend() {
  return (
    <div className="map-legend">
      <p className="map-legend-title">Fire Danger Rating</p>
      <div className="map-legend-items">
        {LEGEND_ITEMS.map((item) => (
          <div key={item.label} className="map-legend-item">
            <span className="map-legend-swatch" style={{ background: item.color }} />
            <span>{item.label}</span>
          </div>
        ))}
        <div className="map-legend-item">
          <span className="map-legend-swatch map-legend-fire-icon">🔥</span>
          <span>Active Fire</span>
        </div>
        <div className="map-legend-item">
          <span className="map-legend-swatch" style={{ background: "#3b82f6", borderRadius: "50%" }} />
          <span>Evacuation</span>
        </div>
      </div>
    </div>
  );
}
