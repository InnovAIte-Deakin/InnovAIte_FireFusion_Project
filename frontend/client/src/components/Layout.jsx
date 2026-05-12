import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import Footer from "./Footer";
import {
  SidebarCollapseProvider,
  useSidebarCollapse,
} from "./SidebarCollapseContext";

function LayoutShell({ children, title, showTopbar, showFooter }) {
  const { collapsed } = useSidebarCollapse();

  return (
    <div
      className={`dashboard-shell${collapsed ? " dashboard-shell--sidebar-collapsed" : ""}`}
    >
      <Sidebar />

      <main className="main">
        {showTopbar && <Topbar title={title} />}

        {children}

        {showFooter && <Footer />}
      </main>
    </div>
  );
}

export default function Layout({
  children,
  title = "Dashboard",
  showTopbar = true,
  showFooter = true,
}) {
  return (
    <SidebarCollapseProvider>
      <LayoutShell title={title} showTopbar={showTopbar} showFooter={showFooter}>
        {children}
      </LayoutShell>
    </SidebarCollapseProvider>
  );
}
