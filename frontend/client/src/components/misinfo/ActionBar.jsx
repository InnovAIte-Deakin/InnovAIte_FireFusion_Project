export default function ActionBar({ onDismiss, onConfirm }) {
  return (
    <div className="action-bar">
      <button className="action-btn dismiss" onClick={onDismiss}>
        Dismiss all
      </button>
      <button className="action-btn confirm" onClick={onConfirm}>
        Confirm as misinformation
      </button>
    </div>
  );
}
