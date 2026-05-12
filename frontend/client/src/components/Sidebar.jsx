import {
  Home,
  Map,
  Shield,
  FileText,
  Bell,
  Settings,
  LogOut,
  Thermometer,
  Wind,
  Droplets,
  Eye,
  ChevronRight,
  PanelLeftClose,
  PanelLeft,
} from "lucide-react";
import { useSidebarCollapse } from "./SidebarCollapseContext";

const menuItems = [
  { label: "Dashboard", icon: Home, badge: null, active: true },
  { label: "Fire Map", icon: Map, badge: "7" },
  { label: "Misinformation Review", icon: Shield, badge: "14" },
  { label: "Reports", icon: FileText, badge: null },
];

function InfoBox({ icon: Icon, title, value }) {
  return (
    <div className="info-box">
      <Icon size={16} />
      <div className="info-box-copy">
        <span className="info-box-title">{title}</span>
        <b className="info-box-value">{value}</b>
      </div>
    </div>
  );
}

export default function Sidebar() {
  const { collapsed, toggle } = useSidebarCollapse();

  return (
    <aside className={`sidebar${collapsed ? " sidebar--collapsed" : ""}`}>
      <div className="sidebar-toolbar">
        <button
          type="button"
          className="sidebar-collapse-btn"
          onClick={toggle}
          aria-expanded={!collapsed}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <PanelLeft size={20} /> : <PanelLeftClose size={20} />}
        </button>
      </div>

      <div className="brand">
        <div className="brand-logo">FF</div>
        <div className="brand-text">
          <h1>FireFusion</h1>
          <p>Emergency Operations</p>
        </div>
      </div>

      <p className="section-title">Main Menu</p>

      <nav className="nav-list">
        {menuItems.map((item) => {
          const Icon = item.icon;

          return (
            <button
              key={item.label}
              type="button"
              className={`nav-item ${item.active ? "active" : ""}`}
              onClick={
                item.label === "Fire Map"
                  ? () => {
                      window.location.href = "/fire-map";
                    }
                  : item.label === "Dashboard"
                    ? () => {
                        window.location.href = "/";
                      }
                    : item.label === "Misinformation Review"
                      ? () => {
                          window.location.href = "/alerts";
                        }
                      : undefined
              }
            >
              <span>
                <Icon size={17} />
                <span className="nav-item-label">{item.label}</span>
              </span>

              {item.badge ? (
                <b className="nav-item-badge">{item.badge}</b>
              ) : null}
              {item.active ? <ChevronRight size={16} className="nav-item-chevron" /> : null}
            </button>
          );
        })}
      </nav>

      <div className="ban-card">
        <h3>
          <span></span>Total Fire Ban
        </h3>
        <p>No fires permitted</p>
        <small>Catastrophic conditions.</small>
      </div>

      <div className="weather-grid">
        <InfoBox icon={Thermometer} title="Temperature" value="42°C" />
        <InfoBox icon={Wind} title="Wind Speed" value="45 km/h" />
        <InfoBox icon={Droplets} title="Humidity" value="18%" />
        <InfoBox icon={Eye} title="Visibility" value="3 km" />
      </div>

      <p className="last-update">Last updated: 14:30</p>

      <div className="sidebar-bottom">
        <p className="section-title">System</p>

        <button type="button" className="nav-item">
          <span>
            <Bell size={17} />
            <span className="nav-item-label">Notifications</span>
          </span>
          <b className="nav-item-badge">3</b>
        </button>

        <button type="button" className="nav-item">
          <span>
            <Settings size={17} />
            <span className="nav-item-label">Settings</span>
          </span>
        </button>

        <div className="profile-card">
          <div>JD</div>
          <span className="profile-card-text">
            <strong>Gaveesha Nuwansara</strong>
            <small>Emergency Manager</small>
          </span>
        </div>

        <button type="button" className="signout">
          <LogOut size={16} />
          <span className="nav-item-label">Sign Out</span>
        </button>

        <small className="version">
          Version 2.4.1<br />
          Last sync: 2 min ago
        </small>
      </div>
    </aside>
  );
}
