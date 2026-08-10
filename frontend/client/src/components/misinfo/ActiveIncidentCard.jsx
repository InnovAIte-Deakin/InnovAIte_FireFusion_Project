export default function ActiveIncidentCard({ incident }) {
  const { title, flagCount, criticalCount, highCount, mediumCount, topThreat } = incident;

  return (
    <div className="misinfo-incident-card-figma">
      <h3 className="misinfo-incident-card-figma__title">{title}</h3>
      <p className="misinfo-incident-card-figma__flags">{flagCount} flags</p>
      <p className="misinfo-incident-card-figma__breakdown">
        <span className="misinfo-incident-card-figma__crit">{criticalCount} critical</span>
        <span className="misinfo-incident-card-figma__sep">, </span>
        <span className="misinfo-incident-card-figma__high">{highCount} high</span>
        <span className="misinfo-incident-card-figma__sep">, </span>
        <span className="misinfo-incident-card-figma__med">{mediumCount} med</span>
      </p>
      {topThreat ? (
        <p className="misinfo-incident-card-figma__threat">Top threat: {topThreat}</p>
      ) : null}
    </div>
  );
}
