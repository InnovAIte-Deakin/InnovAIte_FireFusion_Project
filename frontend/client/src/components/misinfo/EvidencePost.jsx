function relativeTime(isoString) {
  const diffMs = Date.now() - new Date(isoString).getTime();
  const mins = Math.round(diffMs / 60000);
  if (mins < 60) return `${mins} min ago`;
  return `${Math.round(mins / 60)} hr ago`;
}

function formatPlatform(platform) {
  if (platform === "twitter") return "X / Twitter";
  if (platform === "facebook") return "Facebook";
  return platform;
}

export default function EvidencePost({ post }) {
  return (
    <div className="evidence-post">
      <div className="evidence-post-header">
        <span className="evidence-post-author">{post.author_name}</span>
        <span className="evidence-post-platform">
          {formatPlatform(post.platform)} · {relativeTime(post.timestamp)}
        </span>
      </div>
      <div className="evidence-post-text">"{post.content}"</div>
      <div className="evidence-post-meta">
        {(post.share_count / 1000).toFixed(1)}k shares ·{" "}
        {post.misinfo_risk_score >= 0.85 ? "spreading fast" : "growing"}
      </div>
    </div>
  );
}
