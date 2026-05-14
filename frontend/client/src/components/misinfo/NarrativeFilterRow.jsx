export default function NarrativeFilterRow({
  platform,
  onPlatformChange,
  view,
  onViewChange,
}) {
  return (
    <div className="misinfo-feed-toolbar-figma">
      <div className="misinfo-tabs-figma" role="tablist" aria-label="Narrative filters">
        <button
          type="button"
          role="tab"
          aria-selected={view === "needs_review"}
          className={`misinfo-tab-figma ${view === "needs_review" ? "misinfo-tab-figma--on" : ""}`}
          onClick={() => onViewChange("needs_review")}
        >
          Needs review
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={view === "all"}
          className={`misinfo-tab-figma ${view === "all" ? "misinfo-tab-figma--on" : ""}`}
          onClick={() => onViewChange("all")}
        >
          All
        </button>
      </div>

      <div className="misinfo-feed-toolbar-figma__mid">
        <label className="misinfo-sr-only" htmlFor="misinfo-platform-select">
          Platform
        </label>
        <select
          id="misinfo-platform-select"
          className="misinfo-platform-select-figma"
          value={platform}
          onChange={(e) => onPlatformChange(e.target.value)}
        >
          <option value="all">All platforms</option>
          <option value="facebook">Facebook</option>
          <option value="twitter">X / Twitter</option>
          <option value="instagram">Instagram</option>
        </select>
      </div>

      <span className="misinfo-sort-figma">Sorted by: most severe first</span>
    </div>
  );
}
