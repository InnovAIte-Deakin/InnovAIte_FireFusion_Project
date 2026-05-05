export default function FactsBox({ facts }) {
  return (
    <div className="facts-box">
      {facts.map((fact, i) => (
        <div className="fact-item" key={i}>
          <div className="fact-source">{fact.source} — {fact.timestamp}</div>
          <div className="fact-text">{fact.content}</div>
        </div>
      ))}
    </div>
  );
}
