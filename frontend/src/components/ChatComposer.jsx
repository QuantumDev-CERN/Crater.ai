export function ChatComposer({ draft, setDraft, onSend, disabled }) {
  return (
    <div className="composer">
      <textarea
        value={draft}
        onChange={event => setDraft(event.target.value)}
        rows={4}
        placeholder="Ask about setup, duty cycle, troubleshooting, or machine configuration."
        onKeyDown={event => {
          if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
            event.preventDefault()
            onSend()
          }
        }}
      />
      <div className="composer-row">
        <p className="composer-hint">Press Ctrl+Enter to send</p>
        <button disabled={disabled || !draft.trim()} onClick={onSend} type="button">
          {disabled ? 'Working...' : 'Ask the agent'}
        </button>
      </div>
    </div>
  )
}
