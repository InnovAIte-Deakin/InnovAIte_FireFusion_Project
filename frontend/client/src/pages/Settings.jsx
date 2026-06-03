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
          <div className="panel settings-panel settings-panel-narrow">
            <h3>About FireFusion</h3>
            <p className="settings-sub">System information and version details</p>
            {[["Application","FireFusion Emergency Operations Dashboard"],["Version","2.4.1"],["Last Sync","2 min ago"],["Environment","Production"],["Organisation","Emergency Management Victoria"],["Support","support@firefusion.gov.au"]].map(([k,v]) => (
              <div key={k} className="settings-about-row">
                <span className="settings-about-key">{k}</span>
                <span className="settings-about-val">{v}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
