import {
  Bell,
  FileText,
  Home,
  LogOut,
  Map,
  Menu,
  Search,
  Settings,
  Shield,
  TriangleAlert,
  Truck,
  User,
  Users,
  Droplets,
  Thermometer,
  Wind,
  Eye,
  ChevronRight,
  ArrowLeft,
  ArrowRight,
} from "lucide-react";

import "../App.css";

const menuItems = [
  { label: "Dashboard", icon: Home, badge: null, active: true },
  { label: "Fire Map", icon: Map, badge: "7" },
  { label: "Alerts", icon: TriangleAlert, badge: "31" },
  { label: "Misinformation Review", icon: Shield, badge: "14" },
  { label: "Reports", icon: FileText, badge: null },
];

const adviceCards = [
  {
    title: "ABC Radio Internet & Guide",
    text: "Stay informed with official emergency broadcasts from ABC Radio.",
    image:
      "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=800&q=80",
  },
  {
    title: "Find emergency services near you",
    text: "Locate nearby stations, hospitals, and evacuation services.",
    image:
      "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=800&q=80",
  },
  {
    title: "Your mobile phone could help save your life",
    text: "Enable emergency alerts and location services for critical warnings.",
    image:
      "https://images.unsplash.com/photo-1516321497487-e288fb19713f?auto=format&fit=crop&w=800&q=80",
  },
  {
    title: "Helping you recover after an emergency",
    text: "Access support resources, financial help, and community services.",
    image:
      "https://images.unsplash.com/photo-1521791055366-0d553872125f?auto=format&fit=crop&w=800&q=80",
  },
];

export default function Dashboard() {
  return (
    <div className="dashboard-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">FF</div>
          <div>
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
                className={`nav-item ${item.active ? "active" : ""}`}
              >
                <span>
                  <Icon size={17} />
                  {item.label}
                </span>

                {item.badge && <b>{item.badge}</b>}
                {item.active && <ChevronRight size={16} />}
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

          <button className="nav-item">
            <span>
              <Bell size={17} />
              Notifications
            </span>
            <b>3</b>
          </button>

          <button className="nav-item">
            <span>
              <Settings size={17} />
              Settings
            </span>
          </button>

          <div className="profile-card">
            <div>JD</div>
            <span>
              <strong>Gaveesha Nuwansara</strong>
              <small>Emergency Manager</small>
            </span>
          </div>

          <button className="signout">
            <LogOut size={16} />
            Sign Out
          </button>

          <small className="version">Version 2.4.1<br />Last sync: 2 min ago</small>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <h2>Dashboard</h2>

          <select>
            <option>Region: Australia</option>
          </select>

          <select>
            <option>Period: 18 Mar 2026, 14:00 - 20:00</option>
          </select>

          <div className="search">
            <Search size={18} />
            <input placeholder="Search locations, incidents, claims..." />
          </div>

          <span className="sync">Updated 2 min ago</span>

          <button className="user-btn">
            <User size={20} />
          </button>
        </header>

        <section className="stats-grid">
          <Stat title="Overall Bushfire Risk" value="EXTREME" note="Critical conditions" danger />
          <Stat title="Active Fire Zones" value="7" note="+2 since 12:00" />
          <Stat title="Misinformation Alerts" value="14" note="8 pending review" purple />
          <Stat title="Communities at Risk" value="23" note="Population: ~12,400" />
          <Stat title="Official Alerts Issued" value="31" note="Last 6 hours" blue />
        </section>

        <section className="content-grid">
          <div className="panel updates">
            <h3>Latest Official Updates</h3>

            <UpdateCard
              agency="CFA"
              time="8 min ago"
              title="East Gippsland Fire Warning Upgraded"
              text="Emergency Warning issued for communities in East Gippsland. Leave immediately if safe to do so."
              type="CRITICAL"
              color="red"
            />

            <UpdateCard
              agency="VicEmergency"
              time="25 min ago"
              title="Total Fire Ban Declared"
              text="Total Fire Ban in effect for Central, North Central, and Mallee districts until 11:59 PM."
              type="WARNING"
              color="orange"
            />
          </div>

          <div className="panel incident">
            <h3>Incident Overview</h3>
            <div className="risk-line">
              <span>Current Risk Level</span>
              <b>EXTREME</b>
            </div>
            <div className="bar"><span></span></div>

            <div className="mini-grid">
              <Mini title="Wind Speed" value="45 km/h NW" />
              <Mini title="Temperature" value="41°C" />
              <Mini title="Humidity" value="12%" />
              <Mini title="Evacuation Status" value="Active (7 zones)" />
            </div>

            <div className="slider">
              <button><ArrowLeft size={22} /></button>
              <div>
                <img
                  src="https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80"
                  alt="Home fire prevention"
                />
                <strong>Home fire prevention</strong>
              </div>
              <button><ArrowRight size={22} /></button>
            </div>
          </div>

          <div className="panel resources">
            <div className="panel-head">
              <h3>Resource Allocation</h3>
              <a>Manage</a>
            </div>

            <Resource icon={Truck} name="Fire Trucks" value="45 deployed / 23 available" percent="65%" status="orange" />
            <Resource icon={Users} name="Personnel" value="312 deployed / 156 available" percent="67%" status="orange" />
            <Resource icon={Droplets} name="Water Bombers" value="8 deployed / 3 available" percent="73%" status="red" />
            <Resource icon={Truck} name="Water Tankers" value="28 deployed / 15 available" percent="65%" status="green" />

            <div className="legend">
              <span><i className="green"></i>Optimal</span>
              <span><i className="orange"></i>Stretched</span>
              <span><i className="red"></i>Critical</span>
            </div>
          </div>
        </section>

        <section>
          <h3 className="advice-title">Emergency Advice</h3>
          <div className="advice-grid">
            {adviceCards.map((card) => (
              <article className="advice-card" key={card.title}>
                <img src={card.image} alt={card.title} />
                <div>
                  <h4>{card.title}</h4>
                  <p>{card.text}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <footer className="footer">
          <FooterCol
            title="About FireFusion"
            links={[
              "AI-driven bushfire forecasting and misinformation monitoring for safer, faster emergency decision-making in Victoria.",
              "Project Overview",
              "Mission & Vision",
              "Integrated Dashboard",
              "Research Direction",
            ]}
          />

          <FooterCol
            title="Core Features"
            links={[
              "Bushfire Forecasting",
              "Misinformation Detection",
              "Human Review Workflow",
              "Risk Visualisation",
            ]}
          />

          <FooterCol
            title="Data & Resources"
            links={[
              "Weather & Fire Data",
              "Historical Fire Cases",
              "Social Media Analysis",
              "Documentation",
            ]}
          />

          <FooterCol
            title="Connect With Us"
            links={["Email", "LinkedIn", "Teams / Project Updates"]}
          />
        </footer>
      </main>
    </div>
  );
}

function InfoBox({ icon: Icon, title, value }) {
  return (
    <div className="info-box">
      <p><Icon size={13} />{title}</p>
      <strong>{value}</strong>
    </div>
  );
}

function Stat({ title, value, note, danger, purple, blue }) {
  return (
    <div className="stat-card">
      <p>{title}</p>
      <h3 className={danger ? "danger" : purple ? "purple" : blue ? "blue" : ""}>
        {value}
      </h3>
      <span>{note}</span>
    </div>
  );
}

function UpdateCard({ agency, time, title, text, type, color }) {
  return (
    <article className={`update-card ${color}`}>
      <div>
        <strong>{agency}</strong>
        <span>{time}</span>
      </div>
      <h4>{title}</h4>
      <p>{text}</p>
      <b>{type}</b>
    </article>
  );
}

function Mini({ title, value }) {
  return (
    <div className="mini-card">
      <strong>{title}</strong>
      <p>{value}</p>
    </div>
  );
}

function Resource({ icon: Icon, name, value, percent, status }) {
  return (
    <div className="resource">
      <div>
        <span><Icon size={15} />{name}</span>
        <p>{value}</p>
      </div>
      <div className="resource-bar">
        <span className={status} style={{ width: percent }}></span>
      </div>
      <small>{percent} deployed</small>
    </div>
  );
}

function FooterCol({ title, links }) {
  return (
    <div>
      <h4>{title}</h4>
      {links.map((link) => (
        <p key={link}>{link}</p>
      ))}
    </div>
  );
}