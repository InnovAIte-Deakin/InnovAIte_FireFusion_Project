import { useState } from "react";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import Footer from "./Footer";

export default function Layout({ children, title = "Dashboard", showTopbar = true, showFooter = true }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="dashboard-shell">
      <Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed((v) => !v)} />

      <main className={`main${sidebarCollapsed ? " sidebar-collapsed" : ""}`}>
        {showTopbar && <Topbar title={title} />}

        {children}

        {showFooter && <Footer />}
      </main>
    </div>
  );
}