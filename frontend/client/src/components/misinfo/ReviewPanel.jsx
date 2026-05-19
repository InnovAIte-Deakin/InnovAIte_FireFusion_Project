import NarrativeSummaryBox from "./NarrativeSummaryBox";
import ClaimsList from "./ClaimsList";
import FactsBox from "./FactsBox";
import EvidencePost from "./EvidencePost";
import ActionBar from "./ActionBar";
import CollapsedReview from "./CollapsedReview";
import ComposerSection from "./ComposerSection";
import PublishBar from "./PublishBar";

export default function ReviewPanel({
  narrative,
  posts,
  officialFacts,
  panelState,
  onConfirm,
  onClose,
  correctionText,
  onTextChange,
  selectedChannels,
  onChannelToggle,
  onSaveDraft,
  onPublish,
}) {
  const isReview = panelState === "review";

  return (
    <div className="review-panel">
      <div className="panel-header">
        <div className="panel-header-left">
          <span className="panel-title">
            {isReview ? "Review narrative" : "Compose correction"}
          </span>
          <span className="sev-pill crit">Critical</span>
        </div>
        <button className="panel-close" onClick={onClose}>&times;</button>
      </div>

      <div className="panel-body">
        {isReview ? (
          <>
            <div className="panel-section-title">AI-synthesized narrative</div>
            <NarrativeSummaryBox narrative={narrative} />

            <div className="panel-section-title">Key claims identified</div>
            <ClaimsList claims={narrative.key_claims} />

            <div className="panel-section-title">Official facts (auto-matched)</div>
            <FactsBox facts={officialFacts} />

            <div className="panel-section-title">Evidence posts ({posts.length})</div>
            {posts?.map((post) => (
              <EvidencePost key={post.post_id} post={post} />
            ))}
          </>
        ) : (
          <>
            <CollapsedReview narrative={narrative} />
            <ComposerSection
              correctionText={correctionText}
              onTextChange={onTextChange}
              selectedChannels={selectedChannels}
              onChannelToggle={onChannelToggle}
            />
          </>
        )}
      </div>

      {isReview ? (
        <ActionBar onDismiss={onClose} onConfirm={onConfirm} />
      ) : (
        <PublishBar onSaveDraft={onSaveDraft} onPublish={onPublish} />
      )}
    </div>
  );
}
