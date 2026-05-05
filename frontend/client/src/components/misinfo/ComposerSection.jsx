import ChannelOptions from "./ChannelOptions";

export default function ComposerSection({ correctionText, onTextChange, selectedChannels, onChannelToggle }) {
  return (
    <>
      <div className="composer-section">
        <div className="composer-label">
          <span className="ai-tag">AI draft</span>
          Official correction
        </div>
        <textarea
          className="composer-textarea"
          value={correctionText}
          onChange={(e) => onTextChange(e.target.value)}
        />
      </div>
      <div className="composer-section">
        <div className="composer-label">Distribute via</div>
        <ChannelOptions selectedChannels={selectedChannels} onToggle={onChannelToggle} />
      </div>
    </>
  );
}
