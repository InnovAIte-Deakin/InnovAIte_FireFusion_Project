import { useState } from "react";
import {
  AlertTriangle,
  Bell,
  Flag,
  Users,
  Clock,
  Megaphone,
  Activity,
  Wind,
  Thermometer,
  Droplets,
  MapPin,
  Truck,
  Plane,
  Shield,
  Flame,
  HeartHandshake,
  Radio,
  Smartphone,
  Home,
  BarChart3,
  Maximize2,
  ExternalLink,
} from "lucide-react";

import Layout from "../components/Layout";
import "../App.css";

const officialUpdates = [
  {
    agency: "CFA",
    title: "East Gippsland Fire Warning Upgraded",
    text: "Emergency Warning issued for communities in East Gippsland.",
    time: "6 min ago",
    type: "CRITICAL",
    color: "critical",
  },
  {
    agency: "VIC",
    title: "Total Fire Ban Declared",
    text: "Total Fire Ban in effect for Central, North Central, and Mallee districts until 11:59 PM.",
    time: "26 min ago",
    type: "WARNING",
    color: "warning",
  },
  {
    agency: "VicEmergency",
    title: "Smoke conditions worsening near Grampians",
    text: "Smoke levels increasing due to easterly winds.",
    time: "1 hr ago",
    type: "ADVISORY",
    color: "advisory",
  },
];

const resources = [
  {
    icon: Truck,
    name: "Fire Trucks",
    percent: "65%",
    value: "45 deployed / 23 available",
    status: "critical",
  },
  {
    icon: Users,
    name: "Personnel",
    percent: "67%",
    value: "312 deployed / 156 available",
    status: "warning",
  },
  {
    icon: Plane,
    name: "Water Bombers",
    percent: "73%",
    value: "8 deployed / 3 available",
    status: "critical",
  },
  {
    icon: Droplets,
    name: "Water Tankers",
    percent: "65%",
    value: "28 deployed / 15 available",
    status: "safe",
  },
];

const adviceCards = [
  {
    icon: Home,
    title: "Home fire prevention",
    text: "Reduce risk and protect your property.",
    image:
      "https://images.unsplash.com/photo-1523413651479-597eb2da0ad6?auto=format&fit=crop&w=900&q=80",
  },
  {
    icon: MapPin,
    title: "Find emergency services near you",
    text: "Locate hospitals, relief centres, and evacuation points.",
    image:
      "https://images.unsplash.com/photo-1587745416684-47953f16f02f?auto=format&fit=crop&w=900&q=80",
  },
  {
    icon: Smartphone,
    title: "Mobile phone safety warnings",
    text: "Stay informed and avoid network congestion.",
    image:
      "https://images.unsplash.com/photo-1516321497487-e288fb19713f?auto=format&fit=crop&w=900&q=80",
  },
  {
    icon: HeartHandshake,
    title: "Recovery support after an emergency",
    text: "Access support services and community resources.",
    image:
      "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?auto=format&fit=crop&w=900&q=80",
  },
];

export default function Dashboard() {
  const [activeFilter, setActiveFilter] = useState("ALL");
  const [selectedZone, setSelectedZone] = useState("East Gippsland");
  const [riskLevel, setRiskLevel] = useState("Extreme");
  const [isSimulating, setIsSimulating] = useState(false);
  const [sirenActive, setSirenActive] = useState(false);

  const filteredUpdates = activeFilter === "ALL"
    ? officialUpdates
    : officialUpdates.filter((item) => item.type === activeFilter);

  const zonesData = {
    "Grampians": { risk: "High", color: "#f97316", temp: "38°C", wind: "36 km/h W", threat: "Bushfire smoke & spotting" },
    "Dandenong Ranges": { risk: "Moderate", color: "#eab308", temp: "34°C", wind: "24 km/h SW", threat: "High fuel load, alert standby" },
    "Latrobe Valley": { risk: "Moderate", color: "#eab308", temp: "35°C", wind: "28 km/h S", threat: "Industrial perimeter patrol" },
    "East Gippsland": { risk: "Extreme", color: "#ef4444", temp: "41°C", wind: "45 km/h NW", threat: "Uncontrolled front, Evacuate Now" },
  };

  const handleSimulateAlert = () => {
    setIsSimulating(true);
    setSirenActive(true);
    setTimeout(() => {
      setIsSimulating(false);
    }, 4000);
  };

  return (
    <Layout title="Dashboard">
      <div className="ff-dashboard">
        {/* Simulation Banner Notice if siren or simulation is active */}
        {sirenActive && (
          <div className="ff-live-broadcast-banner">
            <div className="ff-broadcast-content">
              <span className="ff-beacon-ping"></span>
              <strong>🚨 LIVE EMERGENCY BROADCAST ACTIVE:</strong>
              <span>Immediate evacuation recommended for East Gippsland & Alpine sectors. Emergency sirens sounding.</span>
            </div>
            <button className="ff-broadcast-dismiss" onClick={() => setSirenActive(false)}>Dismiss Alarm</button>
          </div>
        )}

        <section className="ff-hero">
          <div className="ff-hero-overlay"></div>
          <div className="ff-fire-particles">
            <span className="particle p-1"></span>
            <span className="particle p-2"></span>
            <span className="particle p-3"></span>
            <span className="particle p-4"></span>
            <span className="particle p-5"></span>
            <span className="particle p-6"></span>
            <span className="particle p-7"></span>
            <span className="particle p-8"></span>
          </div>

          <div className="ff-hero-content">
            <div className="ff-hero-header-flex">
              <div>
                <div className="ff-system-badge">
                  <span className="ff-live-radar-dot"></span>
                  DEFCON-1 LEVEL SURVEILLANCE • VICTORIA COMMAND
                </div>
                <h1>FireFusion Emergency Intelligence Dashboard</h1>
                <p>
                  AI-powered bushfire forecasting and misinformation monitoring
                  interface for Victoria.
                </p>
              </div>

              {/* Quick Command Actions */}
              <div className="ff-hero-actions">
                <button 
                  className={`ff-action-btn ff-siren-btn ${sirenActive ? "active" : ""}`}
                  onClick={() => setSirenActive(!sirenActive)}
                  title="Toggle Emergency Siren"
                >
                  <Radio size={16} className={sirenActive ? "ff-spin-slow" : ""} />
                  <span>{sirenActive ? "Siren Muted" : "Alert Siren"}</span>
                </button>

                <button 
                  className={`ff-action-btn ff-sim-btn ${isSimulating ? "simulating" : ""}`}
                  onClick={handleSimulateAlert}
                  disabled={isSimulating}
                >
                  <Flame size={16} />
                  <span>{isSimulating ? "Broadcasting..." : "Simulate Alert"}</span>
                </button>
              </div>
            </div>

            <div className="ff-summary-grid">
              <SummaryCard
                icon={AlertTriangle}
                label="Current Risk"
                value={riskLevel}
                tone="danger"
                isPulsing={true}
              />
              <SummaryCard
                icon={Bell}
                label="Active Alerts"
                value="31"
                tone="red"
              />
              <SummaryCard
                icon={Flag}
                label="Misinformation Flags"
                value="14"
                tone="purple"
              />
              <SummaryCard
                icon={Users}
                label="Resources Deployed"
                value="65%"
                tone="green"
              />
              <SummaryCard
                icon={Clock}
                label="Last Updated"
                value="14:30"
                tone="blue"
              />
            </div>
          </div>
        </section>

        <div className="ff-dashboard-layout">
          <div className="ff-column-left">
            <Panel className="ff-updates-panel">
              <PanelHeader
                icon={Megaphone}
                title="Latest Official Updates"
                action="View All"
              />

              <div className="ff-filter-tabs">
                {["ALL", "CRITICAL", "WARNING", "ADVISORY"].map((filter) => (
                  <button
                    key={filter}
                    className={`ff-filter-btn ff-filter-btn-${filter.toLowerCase()} ${
                      activeFilter === filter ? "active" : ""
                    }`}
                    onClick={() => setActiveFilter(filter)}
                  >
                    {filter}
                  </button>
                ))}
              </div>

              <div className="ff-update-list">
                {filteredUpdates.map((item) => (
                  <UpdateCard key={item.title} {...item} />
                ))}
              </div>
            </Panel>

            {/* UPGRADED INTERACTIVE MAP PANEL */}
            <Panel className="ff-map-panel ff-map-enhanced">
              <div className="ff-map-head">
                <div className="ff-map-title-wrap">
                  <Flame size={18} className="ff-map-flame-icon" />
                  <div>
                    <h3>Victoria Real-Time Fire Risk Map</h3>
                    <small>Click zones to inspect live telemetry & conditions</small>
                  </div>
                </div>
                <div className="ff-map-head-controls">
                  <span className="ff-map-live-tag">● RADAR LIVE</span>
                  <button title="Full Map View">
                    <Maximize2 size={16} />
                  </button>
                </div>
              </div>

              <div className="ff-map-area ff-map-interactive-box">
                {/* Radar sweep animation effect */}
                <div className="ff-radar-sweep"></div>

                <div className="ff-map-legend">
                  <span className="legend-title">Risk Scale</span>
                  <span><i className="extreme"></i>Extreme</span>
                  <span><i className="high"></i>High</span>
                  <span><i className="moderate"></i>Moderate</span>
                  <span><i className="low"></i>Low</span>
                </div>

                <div className="ff-victoria-map">
                  {/* Glowing Interactive Zone Nodes */}
                  <div 
                    className={`zone zone-1 ${selectedZone === "Grampians" ? "zone-active" : ""}`}
                    onClick={() => setSelectedZone("Grampians")}
                  >
                    <span className="zone-pulse-beacon"></span>
                    Grampians<br /><small>High Risk</small>
                  </div>

                  <div 
                    className={`zone zone-2 ${selectedZone === "Dandenong Ranges" ? "zone-active" : ""}`}
                    onClick={() => setSelectedZone("Dandenong Ranges")}
                  >
                    Dandenong Ranges<br /><small>Moderate</small>
                  </div>

                  <div 
                    className={`zone zone-3 ${selectedZone === "Latrobe Valley" ? "zone-active" : ""}`}
                    onClick={() => setSelectedZone("Latrobe Valley")}
                  >
                    Latrobe Valley<br /><small>Moderate</small>
                  </div>

                  <div 
                    className={`zone zone-4 ${selectedZone === "East Gippsland" ? "zone-active" : ""}`}
                    onClick={() => setSelectedZone("East Gippsland")}
                  >
                    <span className="zone-pulse-beacon critical-beacon"></span>
                    East Gippsland<br /><small>🔥 Extreme</small>
                  </div>
                </div>

                {/* Live Zone Telemetry Card (Interactive on map click) */}
                <div className="ff-map-telemetry-card">
                  <div className="ff-telemetry-header">
                    <strong>{selectedZone}</strong>
                    <span 
                      className="ff-telemetry-badge"
                      style={{ backgroundColor: zonesData[selectedZone]?.color || '#ef4444' }}
                    >
                      {zonesData[selectedZone]?.risk}
                    </span>
                  </div>
                  <div className="ff-telemetry-details">
                    <div><span>Wind:</span> <b>{zonesData[selectedZone]?.wind}</b></div>
                    <div><span>Temp:</span> <b>{zonesData[selectedZone]?.temp}</b></div>
                    <div className="full-width"><span>Notice:</span> <small>{zonesData[selectedZone]?.threat}</small></div>
                  </div>
                </div>

                <button className="ff-map-btn">
                  Open Interactive Map View
                </button>
              </div>
            </Panel>

            <Panel className="ff-decision-panel">
              <PanelHeader icon={Shield} title="Decision Support & Automated Safeguards" />

              <div className="ff-decision-grid">
                <DecisionCard
                  icon={Users}
                  title="Evacuation Priority"
                  text="2 zones require immediate review"
                  button="Review Zones"
                  tone="red"
                />
                <DecisionCard
                  icon={Flame}
                  title="Resource Gap"
                  text="Water bombers critically low"
                  button="View Resources"
                  tone="orange"
                />
                <DecisionCard
                  icon={Shield}
                  title="Misinformation Risk"
                  text="14 posts require human review"
                  button="Review Posts"
                  tone="purple"
                />
              </div>
            </Panel>

            <Panel className="ff-chart-panel">
              <div className="ff-panel-title-row">
                <div className="ff-chart-title-wrap">
                  <Activity size={18} style={{ color: "#ef233c" }} />
                  <div>
                    <h3 style={{ margin: 0 }}>Fire Risk Trend & Predictive Surge (24h)</h3>
                    <small style={{ color: "#94a3b8" }}>AI Neural Forecast based on BoM wind & fuel load projections</small>
                  </div>
                </div>
                <a>View Full Analytics</a>
              </div>

              <div className="ff-trend-chart">
                <div className="ff-y-labels">
                  <span>Extreme</span>
                  <span>High</span>
                  <span>Moderate</span>
                  <span>Low</span>
                </div>

                <div className="ff-chart-svg-container">
                  <svg viewBox="0 0 700 170" preserveAspectRatio="none">
                    <defs>
                      <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#ef233c" stopOpacity="0.45" />
                        <stop offset="100%" stopColor="#ef233c" stopOpacity="0.0" />
                      </linearGradient>
                    </defs>
                    {/* Shaded area underneath */}
                    <polygon
                      points="0,95 45,85 85,55 120,70 160,45 205,35 250,22 300,42 345,36 390,65 440,80 490,110 535,120 575,95 620,100 660,135 700,150 700,170 0,170"
                      fill="url(#chartGradient)"
                    />
                    <polyline
                      className="ff-trend-line-animated"
                      points="0,95 45,85 85,55 120,70 160,45 205,35 250,22 300,42 345,36 390,65 440,80 490,110 535,120 575,95 620,100 660,135 700,150"
                      fill="none"
                      stroke="#ef233c"
                      strokeWidth="3.5"
                      strokeLinecap="round"
                    />
                    {/* Peak Marker Dot */}
                    <circle cx="250" cy="22" r="5" fill="#ffffff" stroke="#ef233c" strokeWidth="3" className="ff-pulse-circle" />
                  </svg>
                </div>

                <div className="ff-x-labels">
                  <span>15:00</span>
                  <span>18:00</span>
                  <span>21:00</span>
                  <span>00:00</span>
                  <span>03:00</span>
                  <span>06:00</span>
                  <span>09:00</span>
                  <span>12:00</span>
                  <span>15:00</span>
                </div>
              </div>
            </Panel>
          </div>

          <div className="ff-column-right">
            <Panel className="ff-incident-panel ff-incident-glow">
              <PanelHeader icon={Activity} title="Incident Overview" />

              <div className="ff-risk-header">
                <span className="ff-risk-label-group">
                  Current Threat Assessment
                  <small>Victoria Command Matrix</small>
                </span>
                <strong className="ff-extreme-badge">
                  <span className="ff-dot-glow"></span>
                  EXTREME
                </strong>
              </div>

              <div className="ff-risk-meter">
                <span className="ff-risk-meter-pin"></span>
              </div>

              <div className="ff-metric-grid">
                {/* UPGRADED DYNAMIC WIND GAUGE */}
                <div className="ff-metric-card ff-wind-gauge-card">
                  <div className="ff-wind-compass-circle">
                    <div className="ff-compass-arrow"></div>
                    <span className="ff-compass-deg">NW</span>
                  </div>
                  <div>
                    <span>Wind Velocity</span>
                    <strong>45 km/h NW</strong>
                    <small className="ff-metric-sub">Gusts up to 68 km/h</small>
                  </div>
                </div>

                <Metric 
                  icon={Thermometer} 
                  title="Temperature" 
                  value="41°C" 
                  sub="Extreme Heat Wave" 
                  accent="red" 
                />
                <Metric 
                  icon={Droplets} 
                  title="Humidity" 
                  value="12%" 
                  sub="Critical dryness" 
                  accent="orange" 
                />
                <Metric 
                  icon={Users} 
                  title="Evacuation Status" 
                  value="Active (2 zones)" 
                  sub="4,120 residents affected" 
                  accent="alert" 
                />
              </div>

              <div className="ff-source-row">
                <span>Data sources: BoM, CFA, VicEmergency Satellite Link</span>
                <b>Updated: 14:30</b>
              </div>
            </Panel>

            <Panel className="ff-resource-panel">
              <PanelHeader icon={Truck} title="Resource Allocation & Readiness" action="View All" />

              <div className="ff-resource-list">
                {resources.map((item) => (
                  <ResourceRow key={item.name} {...item} />
                ))}
              </div>

              <div className="ff-legend">
                <span><i className="safe"></i>Optimal</span>
                <span><i className="warning"></i>Stretched</span>
                <span><i className="critical"></i>Critical Shortage</span>
              </div>
            </Panel>

            <Panel className="ff-advice-panel">
              <PanelHeader icon={Radio} title="Emergency Advice & Field Guides" action="View All" />

              <div className="ff-advice-grid">
                {adviceCards.map((card) => (
                  <AdviceCard key={card.title} {...card} />
                ))}
              </div>
            </Panel>

            <Panel className="ff-misinfo-panel">
              <div className="ff-panel-title-row">
                <h3>Misinformation Posts by Platform</h3>
                <a>View Full Analytics</a>
              </div>

              <div className="ff-misinfo-content">
                <div className="ff-donut">
                  <span>Total<br /><b>378</b></span>
                </div>

                <div className="ff-platform-list">
                  <Platform name="Facebook" percent="38%" count="143" />
                  <Platform name="X (Twitter)" percent="28%" count="106" />
                  <Platform name="Instagram" percent="18%" count="68" />
                  <Platform name="TikTok" percent="10%" count="38" />
                  <Platform name="Other" percent="6%" count="23" />
                </div>

                <div className="ff-theme-box">
                  <h4>Top Misinformation Themes</h4>
                  <Theme label="False evacuation orders" value="42%" width="84%" />
                  <Theme label="Fake fire locations" value="28%" width="58%" />
                  <Theme label="Resource misinformation" value="18%" width="42%" />
                  <Theme label="Other" value="12%" width="30%" />
                </div>
              </div>
            </Panel>
          </div>
        </div>
      </div>
    </Layout>
  );
}

function Panel({ children, className = "" }) {
  return <section className={`ff-panel ${className}`}>{children}</section>;
}

function PanelHeader({ icon: Icon, title, action }) {
  return (
    <div className="ff-panel-header">
      <h3>
        <Icon size={18} />
        {title}
      </h3>
      {action && <a>{action}</a>}
    </div>
  );
}

function SummaryCard({ icon: Icon, label, value, tone, isPulsing }) {
  return (
    <article className={`ff-summary-card ${isPulsing ? "ff-summary-pulse" : ""}`}>
      <div className="ff-summary-icon-wrap">
        <Icon size={24} />
      </div>
      <div>
        <span>{label}</span>
        <strong className={`ff-tone-${tone}`}>{value}</strong>
      </div>
    </article>
  );
}

function Metric({ icon: Icon, title, value, sub, accent = "blue" }) {
  return (
    <article className={`ff-metric-card ff-metric-card-${accent}`}>
      <div className="ff-metric-icon-box">
        <Icon size={22} />
      </div>
      <div>
        <span>{title}</span>
        <strong>{value}</strong>
        {sub && <small className="ff-metric-sub">{sub}</small>}
      </div>
    </article>
  );
}

function UpdateCard({ agency, title, text, time, type, color }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <article className={`ff-update-card ${color} ${expanded ? "expanded" : ""}`}>
      <div className="ff-agency-container">
        <div className="ff-agency">{agency}</div>
        {type === "CRITICAL" && <span className="ff-pulse-dot"></span>}
      </div>

      <div className="ff-update-body">
        <div className="ff-update-content-wrapper">
          <div className="ff-update-header">
            <h4>{title}</h4>
            <span className={`ff-badge ff-badge-${color}`}>{type}</span>
          </div>
          <p>{text}</p>
          <div className="ff-update-meta">
            <span className="ff-time"><Clock size={12} style={{ display: "inline", marginRight: "3px" }} />{time}</span>
          </div>
          {expanded && (
            <div className="ff-expanded-info">
              <div className="ff-instructions">
                <strong>Recommended Safety Steps:</strong>
                <ul>
                  {type === "CRITICAL" && (
                    <>
                      <li>🔴 Evacuate immediately if you are in the highlighted zones.</li>
                      <li>🔴 Pack essential items, medications, and identification papers.</li>
                      <li>🔴 Do not attempt to drive through smoke or active fire fronts.</li>
                    </>
                  )}
                  {type === "WARNING" && (
                    <>
                      <li>🟠 Review your Bushfire Survival Plan now.</li>
                      <li>🟠 Keep hydrants and emergency access ways clear.</li>
                      <li>🟠 Monitor local news, CFA, and weather forecast websites.</li>
                    </>
                  )}
                  {type === "ADVISORY" && (
                    <>
                      <li>🔵 Close all windows and doors to keep smoke out.</li>
                      <li>🔵 Check on elderly neighbors or outdoor pets.</li>
                    </>
                  )}
                </ul>
              </div>
            </div>
          )}
        </div>

        <div className="ff-update-actions">
          <button className="ff-details-btn" onClick={() => setExpanded(!expanded)}>
            {expanded ? "Hide Details" : "View Details"}
          </button>
        </div>
      </div>
    </article>
  );
}


function ResourceRow({ icon: Icon, name, percent, value, status }) {
  return (
    <article className="ff-resource-row">
      <div className="ff-resource-info">
        <span>
          <Icon size={17} />
          {name}
        </span>
        <b>{percent}</b>
        <small>{value}</small>
      </div>

      <div className="ff-resource-bar">
        <i className={status} style={{ width: percent }}></i>
      </div>
    </article>
  );
}

function DecisionCard({ icon: Icon, title, text, button, tone }) {
  return (
    <article className={`ff-decision-card ${tone}`}>
      <Icon size={32} />
      <div>
        <h4>{title}</h4>
        <p>{text}</p>
        <button>
          <ExternalLink size={14} />
          {button}
        </button>
      </div>
    </article>
  );
}

function AdviceCard({ icon: Icon, title, text, image }) {
  return (
    <article className="ff-advice-card">
      <img src={image} alt={title} />
      <div className="ff-advice-cover"></div>
      <div className="ff-advice-text">
        <Icon size={24} />
        <h4>{title}</h4>
        <p>{text}</p>
      </div>
    </article>
  );
}

function Platform({ name, percent, count }) {
  return (
    <div className="ff-platform-row">
      <span>{name}</span>
      <b>{percent}</b>
      <small>{count}</small>
    </div>
  );
}

function Theme({ label, value, width }) {
  return (
    <div className="ff-theme-row">
      <span>{label}</span>
      <div>
        <i style={{ width }}></i>
      </div>
      <b>{value}</b>
    </div>
  );
}