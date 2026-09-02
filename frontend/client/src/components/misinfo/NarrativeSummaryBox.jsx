export default function NarrativeSummaryBox({ narrative }) {
  const summary = narrative?.headline || narrative?.narrative_summary || narrative?.content || "";
  const incidentName = narrative?.incidentName || narrative?.incident_name || "Linked incident";
  const postCount = narrative?.postCount ?? narrative?.post_count ?? 1;
  const shares = narrative?.shares ?? narrative?.combined_shares ?? 0;
  const sharesK = (shares / 1000).toFixed(1);
  const spreadStatus = (narrative?.spreadStatus || narrative?.spread_status || "steady").replace(/_/g, " ");
  const confidence = narrative?.confidenceLevel ?? narrative?.confidence_level ?? 85;
  const urgency = narrative?.urgency || (narrative?.severity === "critical" ? "Immediate" : "High");
  const reviewStatus = (narrative?.reviewStatus || narrative?.review_status || "needs_review").replace(/_/g, " ");

  return (
    <div className="narrative-summary-box">
      <div className="narrative-summary-title">
        <span className="ai-tag">AI narrative</span>
        {summary}
      </div>
      <div className="narrative-summary-incident">{incidentName}</div>
      <div className="narrative-summary-meta flex flex-wrap gap-2 mt-2 text-xs font-medium text-slate-600 dark:text-slate-300">
        <span className="rounded bg-blue-100 dark:bg-blue-900/30 px-2 py-0.5 text-blue-700 dark:text-blue-300">
          Confidence: {confidence}%
        </span>
        <span className="rounded bg-amber-100 dark:bg-amber-900/30 px-2 py-0.5 text-amber-700 dark:text-amber-300">
          Urgency: {urgency}
        </span>
        <span className="rounded bg-purple-100 dark:bg-purple-900/30 px-2 py-0.5 text-purple-700 dark:text-purple-300 capitalize">
          Status: {reviewStatus}
        </span>
        <span>{postCount} posts</span>
        <span>{sharesK}k shares</span>
        <span className="capitalize">{spreadStatus}</span>
      </div>
    </div>
  );
}
