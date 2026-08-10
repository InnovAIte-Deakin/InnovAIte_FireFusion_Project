/** Figma: NARRATIVE OVERVIEW + KPI cards */
export default function KPIStats() {
  return (
    <section className="misinfo-narrative-overview" aria-labelledby="misinfo-narrative-overview-h">
      <h2 id="misinfo-narrative-overview-h" className="misinfo-narrative-overview__label">
        Narrative overview
      </h2>
      <div className="misinfo-kpi-row">
        <article className="misinfo-kpi-card">
          <span className="misinfo-kpi-card__label">Needs review</span>
          <strong className="misinfo-kpi-card__num">12</strong>
        </article>
        <article className="misinfo-kpi-card">
          <span className="misinfo-kpi-card__label">Critical</span>
          <strong className="misinfo-kpi-card__num misinfo-kpi-card__num--critical">3</strong>
        </article>
        <article className="misinfo-kpi-card">
          <span className="misinfo-kpi-card__label">High</span>
          <strong className="misinfo-kpi-card__num misinfo-kpi-card__num--high">5</strong>
        </article>
        <article className="misinfo-kpi-card">
          <span className="misinfo-kpi-card__label">Resolved today</span>
          <strong className="misinfo-kpi-card__num misinfo-kpi-card__num--resolved">8</strong>
        </article>
      </div>
    </section>
  );
}
