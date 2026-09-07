export function ToolActivityPanel({ events }) {
  return (
    <section className="panel">
      <div className="panel-head compact">
        <div>
          <p className="panel-label">Tool activity</p>
          <h2>Reasoning trace</h2>
        </div>
      </div>
      {events.length ? (
        <div className="trace-list">
          {events.map((event, index) => (
            <article key={`${event.kind}-${event.name}-${index}`} className="trace-card">
              <div className="trace-topline">
                <span className={`trace-pill ${event.kind}`}>{event.kind}</span>
                <strong>{event.name}</strong>
              </div>
              <pre>{JSON.stringify(event.payload, null, 2)}</pre>
            </article>
          ))}
        </div>
      ) : (
        <p className="muted">Tool calls and returned payloads stream here while the agent works.</p>
      )}
    </section>
  )
}
