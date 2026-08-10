export default function CollapsedReview({ narrative }) {
  return (
    <div className="collapsed-review">
      <div className="collapsed-review-left">
        <span className="confirmed-badge">Confirmed misinfo</span>
        <span className="collapsed-review-title">{narrative.narrative_summary}</span>
      </div>
      <div className="collapsed-review-meta">
        {narrative.post_count} posts · {narrative.incident_name}
      </div>
    </div>
  );
}
