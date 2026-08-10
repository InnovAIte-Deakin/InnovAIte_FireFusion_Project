export default function LoadingState({ label = "Loading monitor data…" }) {
  return (
    <div className="misinfo-state misinfo-state--loading" role="status">
      <div className="misinfo-state__spinner" aria-hidden />
      <p>{label}</p>
    </div>
  );
}
