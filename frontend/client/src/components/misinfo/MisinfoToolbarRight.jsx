import { Mail, User } from "lucide-react";

export default function MisinfoToolbarRight() {
  return (
    <div className="misinfo-toolbar-right">
      <button type="button" className="misinfo-icon-btn" aria-label="Messages">
        <Mail size={20} strokeWidth={1.75} />
      </button>
      <span className="misinfo-updated-label">Updated 2 min ago</span>
      <button type="button" className="misinfo-user-avatar" aria-label="Account">
        <User size={20} strokeWidth={1.75} />
      </button>
    </div>
  );
}
