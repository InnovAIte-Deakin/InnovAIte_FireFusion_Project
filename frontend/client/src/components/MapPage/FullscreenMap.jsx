import { useState } from "react";
import { Maximize2, Minimize2 } from "lucide-react";

export default function FullscreenMap({ children }) {
  const [fullscreen, setFullscreen] = useState(false);

  return (
    <>
      <div className={fullscreen ? "fsmap-overlay" : "map-container"}>
        {children}
        <button
          className="fsmap-btn"
          onClick={() => setFullscreen((p) => !p)}
          title={fullscreen ? "Exit fullscreen" : "View fullscreen map"}
        >
          {fullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
        </button>
      </div>

      {/* Block scroll when fullscreen */}
      {fullscreen && (
        <style>{`body { overflow: hidden; }`}</style>
      )}
    </>
  );
}
