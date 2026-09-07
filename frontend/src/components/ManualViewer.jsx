export function ManualViewer({ pages, activePage, onOpenPage, onClose }) {
  return (
    <section className="panel">
      <div className="panel-head compact">
        <div>
          <p className="panel-label">Manual pages</p>
          <h2>Page viewer</h2>
        </div>
      </div>
      {pages.length ? (
        <div className="page-strip">
          {pages.map(page => (
            <button key={page} type="button" className="page-card" onClick={() => onOpenPage(page)}>
              <img alt={`Manual page ${page}`} src={`/api/page/${page}`} />
              <span>Page {page}</span>
            </button>
          ))}
        </div>
      ) : (
        <p className="muted">Retrieved page screenshots will collect here for quick citation review.</p>
      )}

      {activePage ? (
        <div className="modal-backdrop" onClick={onClose}>
          <div className="modal-card" onClick={event => event.stopPropagation()}>
            <div className="modal-head">
              <h3>Manual page {activePage}</h3>
              <button type="button" className="ghost-button" onClick={onClose}>
                Close
              </button>
            </div>
            <img alt={`Manual page ${activePage}`} className="modal-image" src={`/api/page/${activePage}`} />
          </div>
        </div>
      ) : null}
    </section>
  )
}
