export function MessageList({ messages, loading, error }) {
  return (
    <div className="messages">
      {messages.length === 0 ? (
        <div className="empty-state">
          <p className="panel-label">Try a guided question</p>
          <h3>Ask about setup, polarity, settings, or weld defects.</h3>
          <p className="muted">
            The workspace to the right will populate with artifacts, images, sources, and manual pages.
          </p>
        </div>
      ) : null}

      {messages.map((msg, index) => (
        <article key={`${msg.role}-${index}`} className={`bubble ${msg.role}`}>
          <p className="bubble-role">{msg.role === 'user' ? 'You' : 'Agent'}</p>
          <p>{msg.content}</p>
        </article>
      ))}

      {loading ? <div className="streaming-indicator">Streaming response...</div> : null}
      {error ? <div className="error-banner">{error}</div> : null}
    </div>
  )
}
