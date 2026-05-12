import { Menu, Search, User } from "lucide-react";
import { useSidebarCollapse } from "./SidebarCollapseContext";

export default function Topbar({ title = "Dashboard" }) {
  const { toggle } = useSidebarCollapse();

  return (
    <header className="topbar">
      <button
        type="button"
        className="topbar-sidebar-toggle"
        onClick={toggle}
        aria-label="Toggle sidebar"
        title="Toggle sidebar"
      >
        <Menu size={20} />
      </button>

      <h2>{title}</h2>

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

      <button type="button" className="user-btn">
        <User size={20} />
      </button>
    </header>
  );
}
