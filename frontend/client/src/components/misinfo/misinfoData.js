/** Normalized shapes + Figma Screen 1 fallback content. */

export const FALLBACK_INCIDENTS = [
  {
    id: "inc_east_gippsland",
    title: "East Gippsland fire complex",
    flagCount: 7,
    criticalCount: 2,
    highCount: 3,
    mediumCount: 2,
    topThreat: "fake evacuation order spreading fast",
  },
  {
    id: "inc_grampians",
    title: "Grampians fire zone",
    flagCount: 3,
    criticalCount: 1,
    highCount: 2,
    mediumCount: 0,
    topThreat: "arson conspiracy narrative gaining traction",
  },
  {
    id: "inc_yarra",
    title: "Yarra Ranges watch zone",
    flagCount: 2,
    criticalCount: 0,
    highCount: 0,
    mediumCount: 2,
    topThreat: "unverified wind change claims",
  },
];

export const FALLBACK_NARRATIVES = [
  {
    id: "nar_001",
    severity: "critical",
    incidentId: "inc_east_gippsland",
    incidentName: "East Gippsland fire complex",
    headline: "False evacuation order for Bairnsdale CBD — posts claim a full CFA evacuation has been ordered when none exists.",
    postCount: 3,
    timeRangeLabel: "12–28 min ago",
    platformsLabel: "X / Twitter, Facebook",
    shares: 4200,
    spreadStatus: "spreading_fast",
    spreadLabel: "spreading fast",
    timestamp: new Date().toISOString(),
    reviewStatus: "needs_review",
    platform: "twitter",
    snippets: [
      {
        handle: "@bushfire_truther",
        text: "BREAKING: CFA has ordered FULL evacuation of Bairnsdale CBD. Get out NOW! They're not telling you the truth about how close the fire is!!!",
      },
      {
        handle: "@eastgipps_news",
        text: "My cousin in CFA says they've been told to keep quiet about the Bairnsdale situation. Full evac coming soon, mark my words.",
      },
    ],
  },
  {
    id: "nar_002",
    severity: "high",
    incidentId: "inc_east_gippsland",
    incidentName: "East Gippsland fire complex",
    headline:
      "Government containment cover-up — posts claim CFA has lost containment on the northern front and is hiding the true scale of damage.",
    postCount: 2,
    timeRangeLabel: "45–52 min ago",
    platformsLabel: "X / Twitter",
    shares: 1000,
    spreadStatus: "growing",
    spreadLabel: "growing",
    timestamp: new Date().toISOString(),
    reviewStatus: "needs_review",
    platform: "twitter",
    snippets: [
      {
        handle: "@firenews_aus",
        text: "Just heard from a mate in CFA — they've lost containment on the northern front. They're not reporting the real numbers.",
      },
      {
        handle: "@aussie_patriot",
        text: "Don't trust the CFA numbers. My uncle's property wasn't counted in the 'contained' area. Total cover-up.",
      },
    ],
  },
  {
    id: "nar_003",
    severity: "medium",
    incidentId: "inc_yarra",
    incidentName: "Yarra Ranges watch zone",
    headline: "Unverified wind change claims — posts allege a sudden 90° wind shift without BOM confirmation.",
    postCount: 1,
    timeRangeLabel: "1–2 hr ago",
    platformsLabel: "Facebook",
    shares: 210,
    spreadStatus: "steady",
    spreadLabel: "steady",
    timestamp: new Date().toISOString(),
    reviewStatus: "needs_review",
    platform: "facebook",
    snippets: [
      {
        handle: "@weather_watch_melb",
        text: "Heard from locals: wind just swung hard east. BOM hasn't updated yet but firies are repositioning. Stay alert.",
      },
      {
        handle: "@yarra_valley_chat",
        text: "Can anyone confirm the wind shift? Seeing smoke plume pics that don't match the official map.",
      },
    ],
  },
];

function normalizeSeverity(value) {
  const v = String(value || "").toLowerCase();
  if (v === "crit" || v === "critical") return "critical";
  if (v === "high") return "high";
  if (v === "med" || v === "medium") return "medium";
  return "medium";
}

export function normalizeIncident(raw) {
  if (!raw || typeof raw !== "object") return null;
  return {
    id: String(raw.id ?? raw.incident_id ?? raw.incidentId ?? ""),
    title: raw.title ?? raw.name ?? raw.incident_name ?? raw.incidentName ?? "Incident",
    flagCount: Number(raw.flagCount ?? raw.flag_count ?? 0) || 0,
    criticalCount: Number(raw.criticalCount ?? raw.critical_count ?? 0) || 0,
    highCount: Number(raw.highCount ?? raw.high_count ?? 0) || 0,
    mediumCount: Number(raw.mediumCount ?? raw.medium_count ?? 0) || 0,
    topThreat: raw.topThreat ?? raw.top_threat ?? "",
  };
}

function inferSpreadLabel(status, shares) {
  const s = String(status || "").toLowerCase();
  if (s.includes("fast") || s === "spreading_fast") return "spreading fast";
  if (s.includes("grow")) return "growing";
  if (s.includes("stable") || s.includes("steady")) return "steady";
  if (shares >= 2000) return "spreading fast";
  if (shares >= 600) return "growing";
  return "steady";
}

export function normalizeNarrative(raw) {
  if (!raw || typeof raw !== "object") return null;
  const id = String(raw.id ?? raw.cluster_id ?? raw.narrative_id ?? raw.post_id ?? "");
  const reviewRaw = raw.reviewStatus ?? raw.review_status ?? raw.status ?? "";
  const reviewStatus = String(reviewRaw).toLowerCase().replace(/\s+/g, "_");
  const content =
    raw.content ?? raw.text ?? raw.narrative_summary ?? raw.summary ?? "";
  const headline =
    raw.headline ??
    raw.title ??
    (content ? content.slice(0, 120) + (content.length > 120 ? "…" : "") : "");
  const shares =
    Number(raw.shares ?? raw.combined_shares ?? raw.share_count ?? raw.engagement ?? 0) || 0;
  const spreadStatus = String(raw.spreadStatus ?? raw.spread_status ?? "").toLowerCase();
  const spreadLabel = raw.spreadLabel ?? inferSpreadLabel(spreadStatus, shares);
  const postCount = Number(raw.postCount ?? raw.post_count ?? raw.posts?.length ?? 1) || 1;
  const timeRangeLabel =
    raw.timeRangeLabel ?? raw.time_range_label ?? raw.time_label ?? "";
  const platformsRaw = raw.platformsLabel ?? raw.platforms_label ?? raw.platforms;
  let platformsLabel = "";
  if (typeof platformsRaw === "string") platformsLabel = platformsRaw;
  else if (Array.isArray(platformsRaw)) {
    platformsLabel = platformsRaw
      .map((p) => (String(p).toLowerCase() === "twitter" ? "X / Twitter" : String(p)))
      .join(", ");
  } else {
    const p = String(raw.platform ?? "unknown").toLowerCase();
    platformsLabel = p === "twitter" ? "X / Twitter" : p === "facebook" ? "Facebook" : p === "instagram" ? "Instagram" : "Social";
  }
  let snippets = Array.isArray(raw.snippets) ? raw.snippets : null;
  if (!snippets || snippets.length === 0) {
    const author = raw.author ?? raw.author_name ?? "@user";
    snippets = [{ handle: author, text: content || headline }];
    if (raw.second_snippet || raw.snippet_2) {
      snippets.push({
        handle: raw.second_author ?? "@source",
        text: String(raw.second_snippet ?? raw.snippet_2),
      });
    } else if (content.length > 80) {
      snippets.push({ handle: author, text: content.slice(80, 200) });
    }
  }
  snippets = snippets.slice(0, 2).map((s) => ({
    handle: s.handle ?? s.author ?? "@user",
    text: s.text ?? s.content ?? "",
  }));

  return {
    id,
    severity: normalizeSeverity(raw.severity),
    incidentId: String(raw.incidentId ?? raw.incident_id ?? raw.incidentID ?? ""),
    incidentName:
      raw.incidentName ??
      raw.incident_name ??
      raw.location ??
      "Linked incident",
    headline,
    postCount,
    timeRangeLabel,
    platformsLabel,
    platform: String(raw.platform ?? "twitter").toLowerCase(),
    content,
    shares,
    spreadStatus,
    spreadLabel,
    timestamp: raw.timestamp ?? raw.timestamp_latest ?? raw.updated_at ?? "",
    reviewStatus: reviewStatus || "needs_review",
    snippets,
  };
}

export function normalizeList(mapper, rows) {
  if (!Array.isArray(rows)) return [];
  return rows.map(mapper).filter(Boolean);
}
