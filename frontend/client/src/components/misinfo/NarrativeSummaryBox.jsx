export default function NarrativeSummaryBox({ narrative }) {
  return (
    <div className="narrative-summary-box">
      <div className="narrative-summary-title">
        <span className="ai-tag">AI narrative</span>
        {narrative.narrative_summary}
      </div>
      <div className="narrative-summary-incident">{narrative.incident_name}</div>
      <div className="narrative-summary-meta">
        <span>{narrative.post_count} posts clustered</span>
        <span>{(narrative.combined_shares / 1000).toFixed(1)}k combined shares</span>
        <span>{narrative.spread_status.replace(/_/g, " ")}</span>
      </div>
    </div>
  );
}
