import { useState, useRef, useEffect } from "react";
import { Search, X, MapPin, Locate, Loader } from "lucide-react";

export default function SearchLocation({ onSelect }) {
  const [query, setQuery]         = useState("");
  const [locating, setLocating]   = useState(false);
  const [locError, setLocError]   = useState("");
  const [detected, setDetected]   = useState(null);
  const inputRef = useRef(null);

  function handleLocate() {
    if (!navigator.geolocation) {
      setLocError("Geolocation is not supported by your browser.");
      return;
    }
    setLocating(true);
    setLocError("");
    setDetected(null);

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords;
        try {
          const res = await fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json`
          );
          const data = await res.json();
          const label =
            data.address?.city ||
            data.address?.town ||
            data.address?.village ||
            data.address?.county ||
            `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;
          const full = data.display_name || label;
          setDetected({ label, full, lat: latitude, lon: longitude });
          setQuery(label);
          onSelect?.({ label, full, lat: latitude, lon: longitude });
        } catch {
          setLocError("Could not reverse-geocode your location.");
        } finally {
          setLocating(false);
        }
      },
      (err) => {
        setLocating(false);
        if (err.code === 1) setLocError("Location access denied. Please allow it in your browser.");
        else setLocError("Unable to retrieve your location.");
      },
      { timeout: 10000 }
    );
  }

  function handleClear() {
    setQuery("");
    setDetected(null);
    setLocError("");
    inputRef.current?.focus();
  }

  function handleSearch(e) {
    e.preventDefault();
    if (query.trim()) onSelect?.({ label: query.trim() });
  }

  return (
    <div className="sl-wrap">
      <form className={`sl-bar ${locating ? "sl-bar--loading" : ""}`} onSubmit={handleSearch}>
        <Search size={16} className="sl-bar__search-icon" />

        <input
          ref={inputRef}
          className="sl-bar__input"
          placeholder="Search or use location…"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setDetected(null); setLocError(""); }}
          aria-label="Search location"
        />

        {query && (
          <button type="button" className="sl-bar__clear" onClick={handleClear} aria-label="Clear">
            <X size={14} />
          </button>
        )}

        <button
          type="button"
          className="sl-bar__locate"
          onClick={handleLocate}
          disabled={locating}
          title="Use my current location"
          aria-label="Use my location"
        >
          {locating ? <Loader size={15} className="sl-spin" /> : <Locate size={15} />}
        </button>
      </form>

      {locError && (
        <div className="sl-feedback sl-feedback--error">
          <MapPin size={13} /> {locError}
        </div>
      )}

      {detected && !locError && (
        <div className="sl-feedback sl-feedback--success">
          <MapPin size={13} /> Located: <strong>{detected.label}</strong>
        </div>
      )}
    </div>
  );
}
