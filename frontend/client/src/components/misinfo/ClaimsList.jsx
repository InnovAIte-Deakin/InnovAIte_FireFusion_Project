export default function ClaimsList({ claims }) {
  return (
    <div className="claims-list">
      {claims.map((claim, i) => (
        <div className="claim-item" key={i}>
          <span className="claim-number">{i + 1}</span>
          <span className="claim-text">{claim}</span>
        </div>
      ))}
    </div>
  );
}
