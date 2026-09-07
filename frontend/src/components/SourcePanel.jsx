export function SourcePanel({ sources, onOpenPage }) {
  return (
    <section className="panel">
      <div className="panel-head compact">
        <div>
          <p className="panel-label">Sources</p>
          <h2>Manual citations</h2>
        </div>
      </div>
      {sources.length ? (
        <div className="source-list">
          {sources.map((source, index) => (
            <article key={`${source.page}-${index}`} className="source-card">
              <div className="source-topline">
                <span className="page-pill">Page {source.page ?? '?'}</span>
                <button type="button" className="ghost-button" onClick={() => onOpenPage(source.page)}>
                  Open page
                </button>
              </div>
              <h3>{source.section || 'Manual section'}</h3>
              <p>{source.content}</p>
            </article>
          ))}
        </div>
      ) : (
        <p className="muted">Text citations appear here whenever the agent retrieves manual sections.</p>
      )}
    </section>
  )
}
