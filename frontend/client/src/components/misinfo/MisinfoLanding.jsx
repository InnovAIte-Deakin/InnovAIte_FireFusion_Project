import { useCallback, useEffect, useMemo, useState } from "react";
import Layout from "../Layout";
import "../../App.css";
import "../auth/styles.css";
import "./misinfo.css";
import "./misinfo-monitor.css";
import narrativesApi, { incidentsApi } from "../../apis/misinfo-api";
import {
  FALLBACK_INCIDENTS,
  FALLBACK_NARRATIVES,
  normalizeIncident,
  normalizeList,
  normalizeNarrative,
} from "./misinfoData";
import MisinfoHeader from "./MisinfoHeader";
import SearchAndToolbar from "./SearchAndToolbar";
import MisinfoToolbarRight from "./MisinfoToolbarRight";
import KPIStats from "./KPIStats";
import ActiveIncidents from "./ActiveIncidents";
import NarrativeFilterRow from "./NarrativeFilterRow";
import NarrativeCard from "./NarrativeCard";
import LoadingState from "./LoadingState";

function goToMisinformationReview(narrativeId) {
  const q = narrativeId
    ? `?narrativeId=${encodeURIComponent(String(narrativeId))}`
    : "";
  window.location.assign(`/misinfo-review${q}`);
}

function isNeedsReview(status) {
  const s = String(status || "").toLowerCase();
  return s.includes("need") || s === "pending";
}

function matchesPlatform(narrative, platform) {
  if (platform === "all") return true;
  const label = (narrative.platformsLabel || "").toLowerCase();
  const p = String(narrative.platform || "").toLowerCase();
  if (platform === "twitter") {
    return p === "twitter" || label.includes("twitter");
  }
  if (platform === "facebook") {
    return p === "facebook" || label.includes("facebook");
  }
  if (platform === "instagram") {
    return p === "instagram" || label.includes("instagram");
  }
  return true;
}

export default function MisinfoLanding() {
  const [narratives, setNarratives] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);

  const [query, setQuery] = useState("");
  const [platform, setPlatform] = useState("all");
  const [view, setView] = useState("needs_review");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [nData, iData] = await Promise.all([
        narrativesApi.getAll(),
        incidentsApi.getAll(),
      ]);

      let nextNarratives = normalizeList(normalizeNarrative, Array.isArray(nData) ? nData : []);
      let nextIncidents = normalizeList(normalizeIncident, Array.isArray(iData) ? iData : []);

      if (nextNarratives.length === 0) {
        nextNarratives = FALLBACK_NARRATIVES.map((n) => normalizeNarrative(n));
      }
      if (nextIncidents.length === 0) {
        nextIncidents = FALLBACK_INCIDENTS.map((i) => normalizeIncident(i));
      }

      setNarratives(nextNarratives);
      setIncidents(nextIncidents);
    } catch {
      setNarratives(FALLBACK_NARRATIVES.map((n) => normalizeNarrative(n)));
      setIncidents(FALLBACK_INCIDENTS.map((i) => normalizeIncident(i)));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const displayIncidents = useMemo(() => {
    if (incidents.length >= 3) return incidents.slice(0, 3);
    return FALLBACK_INCIDENTS.map((i) => normalizeIncident(i)).slice(0, 3);
  }, [incidents]);

  const filteredNarratives = useMemo(() => {
    const severityWeight = { critical: 3, high: 2, medium: 1 };

    return narratives
      .filter((n) => (view === "all" ? true : isNeedsReview(n.reviewStatus)))
      .filter((n) => matchesPlatform(n, platform))
      .filter((n) => {
        const q = query.trim().toLowerCase();
        if (!q) return true;
        return `${n.incidentName} ${n.headline} ${n.content} ${n.platformsLabel}`
          .toLowerCase()
          .includes(q);
      })
      .sort((a, b) => severityWeight[b.severity] - severityWeight[a.severity]);
  }, [narratives, view, platform, query]);

  return (
    <Layout title="Misinformation monitor" showTopbar={true} showFooter={false}>
      <div className="misinfo-monitor-root misinfo-monitor-root--figma misinfo-screen1-type">
        <header className="misinfo-figma-page-header">
          <MisinfoHeader />
          <SearchAndToolbar
            query={query}
            onQueryChange={setQuery}
            placeholder="Search flagged posts, incidents, authors..."
          />
          <MisinfoToolbarRight />
        </header>

        <KPIStats />

        <ActiveIncidents incidents={displayIncidents} />

        <div className="misinfo-narrative-feed-figma">
          <NarrativeFilterRow
            platform={platform}
            onPlatformChange={setPlatform}
            view={view}
            onViewChange={setView}
          />

          {loading ? (
            <LoadingState />
          ) : (
            <div className="misinfo-narrative-list-figma">
              {filteredNarratives.length === 0 ? (
                <div className="feed-empty-card">
                  <div className="feed-empty-icon">FF</div>
                  <h3>No matching narratives</h3>
                  <p className="muted">Try another filter or search.</p>
                </div>
              ) : (
                filteredNarratives.map((n) => (
                  <NarrativeCard
                    key={n.id}
                    narrative={n}
                    onReviewNarrative={goToMisinformationReview}
                  />
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
