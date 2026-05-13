import { useState } from "react";
import Layout from "../components/Layout";
import "./Settings.css";

const TABS = ["Profile", "Notifications", "Security", "Display", "Data & Sync", "About"];

function Toggle({ enabled, onChange }) {
  return (
    <button onClick={() => onChange(!enabled)} className={"settings-toggle " + (enabled ? "on" : "off")}>
      <span className="settings-toggle-knob" />
    </button>
  );
}

function Field({ label, value, onChange, type = "text" }) {
  return (
    <div className="settings-field">
      <label>{label}</label>
      <input type={type} value={value} onChange={e => onChange && onChange(e.target.value)} />
    </div>
  );
}

function SelectField({ label, value, onChange, options }) {
  return (
    <div className="settings-field">
      <label>{label}</label>
      <select value={value} onChange={e => onChange(e.target.value)}>
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );
}

function NotifRow({ label, desc, enabled, onChange }) {
  return (
    <div className="settings-notif-row">
      <div>
        <strong>{label}</strong>
        <p>{desc}</p>
      </div>
      <Toggle enabled={enabled} onChange={onChange} />
    </div>
  );
}

function SaveBtn({ saved, onClick }) {
  return (
    <div className="settings-save-row">
      <button className="settings-save-btn" onClick={onClick}>
        {saved ? "Saved ✓" : "Save Changes"}
      </button>
    </div>
  );
}

export default function Settings() {
  const [tab, setTab] = useState("Profile");
  const [saved, setSaved] = useState(false);
  const [name, setName] = useState("Tarun Tej Saka");
  const [role, setRole] = useState("Emergency Manager");
  const [email, setEmail] = useState("tarun.tej@firefusion.gov.au");
  const [notifs, setNotifs] = useState({ emergencyAlerts: true, misinfoAlerts: true, weatherUpdates: false, systemNotifs: true });
  const [region, setRegion] = useState("Australia");
  const [timezone, setTimezone] = useState("AEST (UTC+10)");
  const [mapView, setMapView] = useState("East Gippsland, VIC");
  const [dateFormat, setDateFormat] = useState("DD MMM YYYY, HH:mm");
  const [units, setUnits] = useState("Metric (km, °C)");
  const [twoFactor, setTwoFactor] = useState(true);
  const [loginAlerts, setLoginAlerts] = useState(true);
  const [sessionTimeout, setSessionTimeout] = useState("30 minutes");
  const [autoSync, setAutoSync] = useState(true);
  const [offlineMode, setOfflineMode] = useState(false);
  const [dataRetention, setDataRetention] = useState("90 days");

  function handleSave() { setSaved(true); setTimeout(() => setSaved(false), 2500); }

  const initials = name.split(" ").map(w => w[0]).join("").slice(0,2).toUpperCase();

  return (
    <Layout title="Settings">
      <div className="settings-page">
        <div className="settings-tabs">
          {TABS.map(t => (
            <button key={t} onClick={() => setTab(t)} className={"settings-tab " + (tab === t ? "active" : "")}>{t}</button>
          ))}
        </div>

        {tab === "Profile" && (
          <>
            <div className="panel settings-panel">
              <h3>Profile Information</h3>
              <p className="settings-sub">Update your personal details and role</p>
              <div className="settings-avatar-row">
                <div className="settings-avatar">{initials}</div>
                <button className="settings-photo-btn">Change Photo</button>
                <button className="settings-remove-btn">Remove</button>
              </div>
              <div className="settings-fields-grid">
                <Field label="Full Name" value={name} onChange={setName} />
                <Field label="Role" value={role} onChange={setRole} />
                <Field label="Email Address" value={email} onChange={setEmail} type="email" />
              </div>
              <SaveBtn saved={saved} onClick={handleSave} />
            </div>
            <div className="settings-two-col">
              <div className="panel settings-panel settings-panel-highlight">
                <h3>Notification Preferences</h3>
                <NotifRow label="Emergency Alerts" desc="Critical fire & evacuation notifications" enabled={notifs.emergencyAlerts} onChange={v => setNotifs(p => ({ ...p, emergencyAlerts: v }))} />
                <NotifRow label="Misinformation Alerts" desc="New claims flagged for review" enabled={notifs.misinfoAlerts} onChange={v => setNotifs(p => ({ ...p, misinfoAlerts: v }))} />
                <NotifRow label="Weather Updates" desc="Wind, temperature & humidity changes" enabled={notifs.weatherUpdates} onChange={v => setNotifs(p => ({ ...p, weatherUpdates: v }))} />
                <NotifRow label="System Notifications" desc="Sync status & app updates" enabled={notifs.systemNotifs} onChange={v => setNotifs(p => ({ ...p, systemNotifs: v }))} />
              </div>
              <div className="panel settings-panel">
                <h3>Display & Region</h3>
                <div className="settings-fields-grid2">
                  <Field label="Region" value={region} onChange={setRegion} />
                  <Field label="Timezone" value={timezone} onChange={setTimezone} />
                  <div className="settings-full-col"><Field label="Map Default View" value={mapView} onChange={setMapView} /></div>
                  <Field label="Date Format" value={dateFormat} onChange={setDateFormat} />
                  <Field label="Units" value={units} onChange={setUnits} />
                </div>
              </div>
            </div>
            <div className="settings-two-col">
              <div className="panel settings-panel">
                <h3>Security</h3>
                <NotifRow label="Two-Factor Authentication" desc="Add extra security to your account" enabled={twoFactor} onChange={setTwoFactor} />
                <NotifRow label="Login Alerts" desc="Get notified of new sign-ins" enabled={loginAlerts} onChange={setLoginAlerts} />
                <div className="settings-field-single"><SelectField label="Session Timeout" value={sessionTimeout} onChange={setSessionTimeout} options={["15 minutes", "30 minutes", "1 hour", "Never"]} /></div>
              </div>
              <div className="panel settings-panel">
                <h3>Data & Sync</h3>
                <NotifRow label="Auto-Sync" desc="Sync data every 2 minutes" enabled={autoSync} onChange={setAutoSync} />
                <NotifRow label="Offline Mode" desc="Cache data for offline access" enabled={offlineMode} onChange={setOfflineMode} />
                <div className="settings-field-single"><SelectField label="Data Retention" value={dataRetention} onChange={setDataRetention} options={["30 days", "60 days", "90 days", "1 year"]} /></div>
              </div>
            </div>
          </>
        )}

        {tab === "Notifications" && (
          <div className="panel settings-panel settings-panel-narrow">
            <h3>Notification Preferences</h3>
            <p className="settings-sub">Choose what alerts and updates you receive</p>
            <NotifRow label="Emergency Alerts" desc="Critical fire & evacuation notifications" enabled={notifs.emergencyAlerts} onChange={v => setNotifs(p => ({ ...p, emergencyAlerts: v }))} />
            <NotifRow label="Misinformation Alerts" desc="New claims flagged for review" enabled={notifs.misinfoAlerts} onChange={v => setNotifs(p => ({ ...p, misinfoAlerts: v }))} />
            <NotifRow label="Weather Updates" desc="Wind, temperature & humidity changes" enabled={notifs.weatherUpdates} onChange={v => setNotifs(p => ({ ...p, weatherUpdates: v }))} />
            <NotifRow label="System Notifications" desc="Sync status & app updates" enabled={notifs.systemNotifs} onChange={v => setNotifs(p => ({ ...p, systemNotifs: v }))} />
            <SaveBtn saved={saved} onClick={handleSave} />
          </div>
        )}

        {tab === "Security" && (
          <div className="panel settings-panel settings-panel-narrow">
            <h3>Security</h3>
            <p className="settings-sub">Manage your account security settings</p>
            <NotifRow label="Two-Factor Authentication" desc="Add extra security to your account" enabled={twoFactor} onChange={setTwoFactor} />
            <NotifRow label="Login Alerts" desc="Get notified of new sign-ins" enabled={loginAlerts} onChange={setLoginAlerts} />
            <div className="settings-fields-grid2" style={{ marginTop: "16px" }}>
              <SelectField label="Session Timeout" value={sessionTimeout} onChange={setSessionTimeout} options={["15 minutes", "30 minutes", "1 hour", "Never"]} />
            </div>
            <div className="settings-divider" />
            <h4>Change Password</h4>
            <div className="settings-fields-stack">
              <Field label="Current Password" value="" type="password" />
              <Field label="New Password" value="" type="password" />
              <Field label="Confirm New Password" value="" type="password" />
            </div>
            <SaveBtn saved={saved} onClick={handleSave} />
          </div>
        )}

        {tab === "Display" && (
          <div className="panel settings-panel settings-panel-narrow">
            <h3>Display & Region</h3>
            <p className="settings-sub">Customise how data is displayed</p>
            <div className="settings-fields-grid2">
              <Field label="Region" value={region} onChange={setRegion} />
              <Field label="Timezone" value={timezone} onChange={setTimezone} />
              <div className="settings-full-col"><Field label="Map Default View" value={mapView} onChange={setMapView} /></div>
              <Field label="Date Format" value={dateFormat} onChange={setDateFormat} />
              <SelectField label="Units" value={units} onChange={setUnits} options={["Metric (km, °C)", "Imperial (mi, °F)"]} />
            </div>
            <SaveBtn saved={saved} onClick={handleSave} />
          </div>
        )}

        {tab === "Data & Sync" && (
          <div className="panel settings-panel settings-panel-narrow">
            <h3>Data & Sync</h3>
            <p className="settings-sub">Control how data is synced and stored</p>
            <NotifRow label="Auto-Sync" desc="Sync data every 2 minutes" enabled={autoSync} onChange={setAutoSync} />
            <NotifRow label="Offline Mode" desc="Cache data for offline access" enabled={offlineMode} onChange={setOfflineMode} />
            <div className="settings-fields-grid2" style={{ marginTop: "16px" }}>
              <SelectField label="Data Retention Period" value={dataRetention} onChange={setDataRetention} options={["30 days", "60 days", "90 days", "1 year"]} />
            </div>
            <SaveBtn saved={saved} onClick={handleSave} />
          </div>
        )}

        {tab === "About" && (
          <div className="panel settings-panel settings-panel-about">
            <div className="about-hero">
              <div className="about-hero-text">
                <span className="about-label">About FireFusion</span>
                <h3>AI-driven bushfire forecasting and misinformation defence system</h3>
                <p>FireFusion is an AI-powered bushfire management platform designed for Victoria, Australia. It provides real-time fire risk forecasting, emergency alerts, and misinformation detection to support authorities and communities in making informed decisions during bushfire events.</p>
                <div className="about-summary-grid">
                  <div>
                    <span>Application Name</span>
                    <strong>FireFusion – AI-Driven Bushfire Forecasting System</strong>
                  </div>
                  <div>
                    <span>Version</span>
                    <strong>v1.0.0 (Beta)</strong>
                  </div>
                  <div>
                    <span>Developed By</span>
                    <strong>FireFusion Team / InnovAIte</strong>
                  </div>
                </div>
              </div>

              <div className="about-hero-side">
                <div className="about-brand-card">
                  <div className="about-brand-logo">FF</div>
                  <div>
                    <h4>FireFusion</h4>
                    <p>Emergency Operations</p>
                  </div>
                </div>
                <div className="about-stat-grid">
                  <div className="about-stat-card">
                    <span>Vision</span>
                    <strong>Smart, safe and resilient communities.</strong>
                  </div>
                  <div className="about-stat-card">
                    <span>Mission</span>
                    <strong>Deliver trusted risk insights for fast action.</strong>
                  </div>
                </div>
              </div>
            </div>

            <div className="about-feature-grid">
              <div className="about-card">
                <h4>Vision</h4>
                <p>Enable early and accurate bushfire prediction using advanced AI models that analyze environmental, weather, and historical data to identify high-risk zones and support timely preventive actions.</p>
              </div>
              <div className="about-card">
                <h4>Mission</h4>
                <p>Provide real-time bushfire risk forecasts and alerts by continuously analyzing environmental, weather, and sensor data to support proactive decision-making and improve community preparedness.</p>
              </div>
            </div>

            <div className="about-contact-grid">
              <div className="about-contact-card">
                <span>Email</span>
                <strong>support@firefusion.ai</strong>
              </div>
              <div className="about-contact-card">
                <span>Emergency Contact</span>
                <strong>Victoria Fire Services</strong>
                <p>00 61 2 1234 5678</p>
              </div>
              <div className="about-contact-card">
                <span>Website</span>
                <strong>www.innovalte.ai</strong>
              </div>
              <div className="about-contact-card">
                <span>Location</span>
                <strong>Victoria, Australia</strong>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
