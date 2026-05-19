import { useState } from "react";

const LEGEND_ITEMS = [
  { color: "#cc2e2e", label: "Level 1: Extreme" },
  { color: "#cd5c00", label: "Level 2: High" },
  { color: "#ffd043", label: "Level 3: Medium" },
  { color: "#37d90f", label: "Level 4: Low" },
  { color: "#95a5a6", label: "Level 5: Very Low" },
];

export default function MapLegend() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="map-legend">
      <button
        className="map-legend-toggle"
        onClick={() => setCollapsed(!collapsed)}
      >
        {collapsed ? "▲" : "▼"}
      </button>

      {collapsed && (
        <div className="map-legend-collapsed-label">
          Legend
        </div>
      )}

      {!collapsed && (
        <>
          <p className="map-legend-title">Fire Risk Rating</p>

          <div className="map-legend-items">
            {LEGEND_ITEMS.map((item) => (
              <div key={item.label} className="map-legend-item">
                <span
                  className="map-legend-swatch"
                  style={{ background: item.color }}
                />
                <span>{item.label}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}