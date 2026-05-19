import { useState } from "react";
import { useQuery } from '@tanstack/react-query';
import Layout from "../components/Layout";
import ReviewPanel from "../components/misinfo/ReviewPanel";
import "../components/misinfo/misinfo.css";
import narrativesApi, { postsApi } from "../apis/misinfo-api";

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

export default function MisinformationReview() {
  const [panelState, setPanelState] = useState("review");
  const [correctionText, setCorrectionText] = useState(draftCorrection);
  const [selectedChannels, setSelectedChannels] = useState(["social", "nms"]);
  const [selectedNarrativeId, setSelectedNarrativeId] = useState(
    new URLSearchParams(window.location.search).get("narrativeId")
  );

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
          onClose={() => window.location.assign("/misinfo")}
          correctionText={correctionText}
          onTextChange={setCorrectionText}
          selectedChannels={selectedChannels}
          onChannelToggle={handleChannelToggle}
          onSaveDraft={() => window.location.assign("/misinfo")}
          onPublish={() => window.location.assign("/misinfo")}
        />}
      </div>
    </Layout>
  );
}
