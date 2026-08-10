/**
 * Screen 1 page title + LIVE (Figma). Used when Layout topbar is off to avoid duplicate chrome.
 */
export default function MisinfoHeader() {
  return (
    <div className="misinfo-figma-title-block">
      <h1 className="misinfo-figma-h1">
        Misinformation monitor{" "}
        <span className="misinfo-figma-live">
          <span className="misinfo-figma-live-dot" aria-hidden />
          • LIVE
        </span>
      </h1>
    </div>
  );
}
