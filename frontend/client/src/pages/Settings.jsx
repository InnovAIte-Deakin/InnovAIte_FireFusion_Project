import Layout from "../components/Layout";

export default function Settings() {
  return (
    <Layout title="Settings">
      <section className="settings-page">
        <div className="panel settings-panel">
          <h2>Application Settings</h2>
          <p>Configure FireFusion preferences and notification behaviour.</p>

          <div className="settings-group">
            <h3>Account</h3>
            <label>
              <span>Full name</span>
              <input type="text" placeholder="Gaveesha Nuwansara" />
            </label>
            <label>
              <span>Email address</span>
              <input type="email" placeholder="user@example.com" />
            </label>
          </div>

          <div className="settings-group">
            <h3>Alerts</h3>
            <label>
              <span>Notify on new warnings</span>
              <input type="checkbox" defaultChecked />
            </label>
            <label>
              <span>Send emergency SMS alerts</span>
              <input type="checkbox" />
            </label>
          </div>

          <div className="settings-group">
            <h3>Display</h3>
            <label>
              <span>Time range</span>
              <select>
                <option>Last 24 hours</option>
                <option>Last 48 hours</option>
                <option>Last 7 days</option>
              </select>
            </label>
            <label>
              <span>Theme mode</span>
              <select>
                <option>Auto</option>
                <option>Light</option>
                <option>Dark</option>
              </select>
            </label>
          </div>

          <button className="primary-btn">Save changes</button>
        </div>
      </section>
    </Layout>
  );
}
