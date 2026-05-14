import ActiveIncidentCard from "./ActiveIncidentCard";

export default function ActiveIncidents({ incidents }) {
  const row = incidents.slice(0, 3);

  return (
    <section className="misinfo-active-incidents-figma" aria-labelledby="misinfo-active-incidents-label">
      <h2 id="misinfo-active-incidents-label" className="misinfo-active-incidents-figma__label">
        Active incidents
      </h2>
      <div className="misinfo-active-incidents-figma__row">
        {row.map((inc) => (
          <ActiveIncidentCard key={inc.id} incident={inc} />
        ))}
      </div>
    </section>
  );
}
