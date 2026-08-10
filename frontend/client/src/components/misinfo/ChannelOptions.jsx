const CHANNELS = [
  {
    id: "social",
    name: "Social media counter-post",
    desc: "Publish on X/Twitter and Facebook via official agency accounts",
  },
  {
    id: "nms",
    name: "National Messaging System (NMS)",
    desc: "Cell broadcast to all mobile devices in the affected area",
  },
];

const CheckIcon = () => (
  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
    <path d="M2.5 6L5 8.5L9.5 3.5" stroke="#FFF" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export default function ChannelOptions({ selectedChannels, onToggle }) {
  return (
    <div className="channel-options">
      {CHANNELS.map((ch) => {
        const selected = selectedChannels.includes(ch.id);
        return (
          <div
            key={ch.id}
            className={`channel-option${selected ? " selected" : ""}`}
            onClick={() => onToggle(ch.id)}
          >
            <div className="channel-checkbox">
              {selected && <CheckIcon />}
            </div>
            <div>
              <div className="channel-name">{ch.name}</div>
              <div className="channel-desc">{ch.desc}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
