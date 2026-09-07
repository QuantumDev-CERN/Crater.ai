export function ImagePanel({ images }) {
  return (
    <section className="panel">
      <div className="panel-head compact">
        <div>
          <p className="panel-label">Images</p>
          <h2>Diagrams and photos</h2>
        </div>
      </div>
      {images.length ? (
        <div className="image-grid">
          {images.map((image, index) => (
            <article key={`${image.file_name ?? image.page ?? 'img'}-${index}`} className="image-card">
              {image.image_b64 ? (
                <img
                  alt={image.description || image.file_name || 'manual image'}
                  src={`data:image/png;base64,${image.image_b64}`}
                />
              ) : null}
              <div className="image-meta">
                <strong>{image.type || 'Manual image'}</strong>
                <p>{image.description || 'No description available.'}</p>
                <span>Page {image.page ?? 'Unknown'}</span>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p className="muted">Relevant photos, wiring diagrams, and weld examples will show up here.</p>
      )}
    </section>
  )
}
