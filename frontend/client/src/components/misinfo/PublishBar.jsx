export default function PublishBar({ onSaveDraft, onPublish }) {
  return (
    <div className="publish-bar">
      <button className="save-draft-btn" onClick={onSaveDraft}>
        Save draft
      </button>
      <button className="publish-btn" onClick={onPublish}>
        Publish correction
      </button>
    </div>
  );
}
