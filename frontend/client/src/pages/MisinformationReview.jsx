import { useState } from "react";
import { useQuery } from '@tanstack/react-query';
import Layout from "../components/Layout";
import ReviewPanel from "../components/misinfo/ReviewPanel";
import "../components/misinfo/misinfo.css";
import narrativesApi, { postsApi } from "../apis/misinfo-api";

const sampleNarrative = {
  cluster_id: "nar_001",
  narrative_summary: "False evacuation order for Bairnsdale CBD",
  incident_id: "inc_east_gippsland",
  incident_name: "East Gippsland fire complex",
  severity: "critical",
  post_count: 3,
  combined_shares: 4200,
  spread_status: "spreading_fast",
  key_claims: [
    "CFA has ordered a full evacuation of Bairnsdale CBD",
    "Lakes Entrance road is open for evacuation",
    "Authorities are withholding information about fire proximity",
  ],
  timestamp_earliest: "2025-02-15T14:08:00Z",
  timestamp_latest: "2025-02-15T14:28:00Z",
  platforms: ["twitter", "facebook"],
  review_status: "needs_review",
};

const samplePosts = [
  {
    post_id: "post_001",
    author_name: "@bushfire_truther",
    platform: "twitter",
    content:
      "BREAKING: CFA has ordered FULL evacuation of Bairnsdale CBD. Get out NOW! They're not telling you the truth about how close the fire is!!!",
    timestamp: "2025-02-15T14:28:00Z",
    share_count: 2400,
    severity: "critical",
    misinfo_risk_score: 0.92,
  },
  {
    post_id: "post_002",
    author_name: "Gippsland Community Alerts",
    platform: "facebook",
    content:
      "CONFIRMED: Lakes Entrance road is now OPEN for evacuation. Just drove it myself, all clear.",
    timestamp: "2025-02-15T14:12:00Z",
    share_count: 1800,
    severity: "critical",
    misinfo_risk_score: 0.87,
  },
  {
    post_id: "post_003",
    author_name: "@eastgipps_news",
    platform: "twitter",
    content:
      "My cousin in CFA says they've been told to keep quiet about the Bairnsdale situation. Full evac coming soon, mark my words.",
    timestamp: "2025-02-15T14:08:00Z",
    share_count: 680,
    severity: "high",
    misinfo_risk_score: 0.72,
  },
];

const officialFacts = [
  {
    source: "CFA Official Bulletin",
    timestamp: "14:32 today",
    content:
      "No evacuation order has been issued for Bairnsdale CBD. Current status: Watch and Act for surrounding areas. Residents should monitor VicEmergency for updates.",
  },
  {
    source: "VicRoads",
    timestamp: "14:15 today",
    content:
      "Lakes Entrance road (Princes Highway east of Bairnsdale) remains CLOSED due to active fire operations. Do not attempt to use this route.",
  },
];

const draftCorrection = `OFFICIAL UPDATE — East Gippsland Fire Complex

No evacuation order has been issued for Bairnsdale CBD.

Posts circulating on social media claiming a "full evacuation" of Bairnsdale are FALSE. The current warning level for surrounding areas is Watch and Act.

Additionally, Lakes Entrance road (Princes Highway east of Bairnsdale) remains CLOSED per VicRoads. Do not attempt to use this route for evacuation.

For verified updates:
- VicEmergency app and website
- CFA official channels
- Emergency: call 000

Stay informed. Trust official sources only.

— CFA / Emergency Management Victoria`;

const FEED_CARDS = [
  { severity: "crit", label: "Critical · East Gippsland", text: "False evacuation order — 3 posts, 4.2k shares" },
  { severity: "crit", label: "Critical · Grampians", text: "Arson conspiracy & CFA cover-up — 2 posts" },
  { severity: "high", label: "High · East Gippsland", text: "Containment cover-up — 2 posts" },
  { severity: "med", label: "Medium · Yarra Ranges", text: "Unverified weather claims — 2 posts" },
];

export default function MisinformationReview() {
  const [panelState, setPanelState] = useState("review");
  const [correctionText, setCorrectionText] = useState(draftCorrection);
  const [selectedChannels, setSelectedChannels] = useState(["social", "nms"]);
  const [selectedNarrativeId, setSelectedNarrativeId] = useState("nar_001");

  // Fetch all narratives
  const { data: narratives } = useQuery({
    queryKey: ['narratives'],
    queryFn: narrativesApi.getAll,
    keepPreviousData: true}
  );

  // Fetch narrative by id
  const { data: narrative } = useQuery({
    queryKey: ['narrative', selectedNarrativeId],
    queryFn: () => narrativesApi.getOne(selectedNarrativeId),
    enabled: !!selectedNarrativeId,
  });

  console.log(narrative);

  // fetch all posts
  const { data: posts } = useQuery({
    queryKey: ['posts'],
    queryFn: postsApi.getAll,
  }); 

  function handleChannelToggle(id) {
    setSelectedChannels((prev) =>
      prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id]
    );
  }

  return (
    <Layout title="Misinformation Review" showTopbar={false} showFooter={false}>
      <div className="misinfo-content-area">
        <div className={`feed-placeholder${panelState === "compose" ? " dimmed" : ""}`}>
          <div className="feed-placeholder-header">Misinformation feed</div>
          {narratives?.map((card) => {
            const label = `${card.severity} - ${card.incident_name}`
            const text = `${card.narrative_summary} - ${card.post_count} posts, ${card.combined_shares} shares`
            return (
              <button
                key={card.narrative_id}
                type="button"
                className={`feed-bg-card${card.severity.toLowerCase() === "high" ? " high" : card.severity.toLowerCase() === "medium" ? " med" : ""}${selectedNarrativeId === card.narrative_id ? " selected" : ""}`}
                onClick={() => setSelectedNarrativeId(card.narrative_id)}
              >
                <div className="feed-bg-card-title">{label}</div>
                <div className="feed-bg-card-text">{text}</div>
              </button>
            );
          })}
        </div>

        <div className="panel-divider" />

        {narrative && <ReviewPanel
          narrative={narrative ?? null}
          posts={posts ?? []}
          officialFacts={narrative?.matched_facts}
          panelState={panelState}
          onConfirm={() => setPanelState("compose")}
          onClose={() => setPanelState("review")}
          correctionText={correctionText}
          onTextChange={setCorrectionText}
          selectedChannels={selectedChannels}
          onChannelToggle={handleChannelToggle}
          onSaveDraft={() => alert("Draft saved.")}
          onPublish={() => alert("Correction published.")}
        />}
      </div>
    </Layout>
  );
}
