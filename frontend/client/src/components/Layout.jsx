import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import Footer from "./Footer";

export default function Layout({ children, title = "Dashboard", showTopbar = true }) {
  return (
    <div className="dashboard-shell">
      <Sidebar />

      <main className="main">
        {showTopbar && <Topbar title={title} />}

        {children}

        <Footer />
      </main>
    </div>
  );
}