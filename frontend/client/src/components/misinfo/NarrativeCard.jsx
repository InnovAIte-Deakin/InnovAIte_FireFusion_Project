import { AlertTriangle } from "lucide-react";

function severityBarClass(severity) {
  if (severity === "critical") return "misinfo-narrative-card-figma--critical";
  if (severity === "high") return "misinfo-narrative-card-figma--high";
  return "misinfo-narrative-card-figma--medium";
}

function severityPillClass(severity) {
  if (severity === "critical") return "misinfo-sev-pill misinfo-sev-pill--critical";
  if (severity === "high") return "misinfo-sev-pill misinfo-sev-pill--high";
  return "misinfo-sev-pill misinfo-sev-pill--medium";
}

function severityLabel(severity) {
  const s = String(severity || "").toLowerCase();
  if (s === "critical") return "Critical";
  if (s === "high") return "High";
  return "Medium";
}

function showTrendWarning(spreadLabel) {
  const t = String(spreadLabel || "").toLowerCase();
  return t.includes("grow") || t.includes("spread") || t.includes("fast");
}

export default function NarrativeCard({ narrative, onReviewNarrative }) {
  const {
    id,
    severity,
    incidentName,
    headline,
    postCount,
    timeRangeLabel,
    platformsLabel,
    shares,
    spreadLabel,
    snippets,
  } = narrative;

  const s1 = snippets?.[0];
  const s2 = snippets?.[1];
  const trendWarn = showTrendWarning(spreadLabel);
  const sharesK =
    shares >= 1000 ? `${(shares / 1000).toFixed(1).replace(/\.0$/, "")}k` : String(shares);

  return (
    <article className={`misinfo-narrative-card-figma ${severityBarClass(severity)}`}>
      <div className="misinfo-narrative-card-figma__inner">
        <div className="misinfo-narrative-card-figma__top">
          <span className={severityPillClass(severity)}>{severityLabel(severity)}</span>
          <span className="misinfo-narrative-card-figma__incident">{incidentName}</span>
          <div className="misinfo-narrative-card-figma__top-right">
            <span className="misinfo-narrative-card-figma__posts">{postCount} posts</span>
            <span className="misinfo-narrative-card-figma__time">{timeRangeLabel || "—"}</span>
          </div>
        </div>

        <div className="misinfo-narrative-card-figma__headline-row">
          <span className="misinfo-ai-tag misinfo-ai-tag--with-title">AI narrative</span>
          <h3 className="misinfo-narrative-card-figma__headline">{headline}</h3>
        </div>

        <div className="misinfo-narrative-card-figma__snippets">
          {s1 ? (
            <div className="misinfo-snippet">
              <span className="misinfo-snippet__handle">{s1.handle}:</span>{" "}
              <span className="misinfo-snippet__q">&ldquo;{s1.text}&rdquo;</span>
            </div>
          ) : null}
          {s2 ? (
            <div className="misinfo-snippet">
              <span className="misinfo-snippet__handle">{s2.handle}:</span>{" "}
              <span className="misinfo-snippet__q">&ldquo;{s2.text}&rdquo;</span>
            </div>
          ) : null}
        </div>

        <div className="misinfo-narrative-card-figma__footer">
          <div className="misinfo-narrative-card-figma__metrics">
            <span className="misinfo-narrative-card-figma__platforms">{platformsLabel}</span>
            <span className="misinfo-narrative-card-figma__shares">
              {trendWarn ? (
                <AlertTriangle
                  className="misinfo-narrative-card-figma__warn-ico"
                  size={16}
                  aria-hidden
                />
              ) : null}
              <span>
                {sharesK} combined shares ·{" "}
                <span
                  className={
                    trendWarn ? "misinfo-trend misinfo-trend--hot" : "misinfo-trend misinfo-trend--muted"
                  }
                >
                  {spreadLabel}
                </span>
              </span>
            </span>
          </div>
          <button
            type="button"
            className="misinfo-btn-review-narrative"
            onClick={() => onReviewNarrative(id)}
          >
            Review narrative
          </button>
        </div>
      </div>
    </article>
  );
}
