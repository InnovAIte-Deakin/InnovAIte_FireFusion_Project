import { Search } from "lucide-react";

export default function SearchAndToolbar({
  query,
  onQueryChange,
  placeholder = "Search incidents, narratives, authors…",
}) {
  return (
    <div className="fusion-search-bar misinfo-monitor-search">
      <Search className="fusion-search-svg" size={18} aria-hidden />
      <input
        className="fusion-search-input"
        type="search"
        value={query}
        onChange={(event) => onQueryChange(event.target.value)}
        placeholder={placeholder}
        aria-label="Search misinformation monitor"
      />
    </div>
  );
}
