import { useState } from 'react'
import { ChatComposer } from './components/ChatComposer'
import { MessageList } from './components/MessageList'
import { ArtifactPanel } from './components/ArtifactPanel'
import { SourcePanel } from './components/SourcePanel'
import { ImagePanel } from './components/ImagePanel'
import { ManualViewer } from './components/ManualViewer'
import { ToolActivityPanel } from './components/ToolActivityPanel'

const PROMPTS = [
  'How do I set up TIG welding?',
  'What duty cycle can I safely use at 150A?',
  'My weld has porosity. Help me troubleshoot.',
  'I am welding 3mm steel with MIG. What settings should I use?',
]

export default function App() {
  const [draft, setDraft] = useState(PROMPTS[0])
  const [messages, setMessages] = useState([])
  const [artifacts, setArtifacts] = useState([])
  const [images, setImages] = useState([])
  const [sources, setSources] = useState([])
  const [pages, setPages] = useState([])
  const [toolEvents, setToolEvents] = useState([])
  const [activePage, setActivePage] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function sendMessage(nextDraft) {
    const content = (nextDraft ?? draft).trim()
    if (!content || loading) return

    const nextHistory = [...messages, { role: 'user', content }]
    setDraft('')
    setLoading(true)
    setError('')
    setMessages(nextHistory)
    setArtifacts([])
    setImages([])
    setSources([])
    setPages([])
    setToolEvents([])

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content, history: nextHistory }),
      })

      if (!response.ok || !response.body) {
        throw new Error(`Chat request failed with status ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let assistantText = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const events = buffer.split('\n\n')
        buffer = events.pop() || ''

        for (const eventBlock of events) {
          const dataLine = eventBlock
            .split('\n')
            .find(line => line.startsWith('data: '))

          if (!dataLine) continue

          const event = JSON.parse(dataLine.slice(6))
          handleEvent(event, {
            appendAssistant(text) {
              assistantText += text
              setMessages(prev => upsertAssistant(prev, assistantText))
            },
            setError,
            setArtifacts,
            setImages,
            setSources,
            setPages,
            setToolEvents,
          })
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unexpected chat failure'
      setError(message)
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${message}` }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="shell">
      <div className="backdrop-grid" />
      <header className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Vulcan OmniPro 220 multimodal expert agent</p>
          <h1>Built like a shop-floor copilot, not a PDF chatbot.</h1>
          <p className="lede">
            The assistant can stream answers, surface diagrams, cite manual pages, and switch into
            tools when explanation alone is not enough.
          </p>
        </div>
        <div className="prompt-strip">
          {PROMPTS.map(prompt => (
            <button key={prompt} className="prompt-chip" onClick={() => sendMessage(prompt)} type="button">
              {prompt}
            </button>
          ))}
        </div>
      </header>

      <main className="layout">
        <section className="chat-panel">
          <div className="panel-head">
            <div>
              <p className="panel-label">Conversation</p>
              <h2>Technician chat</h2>
            </div>
            <div className={`status-pill ${loading ? 'busy' : 'idle'}`}>
              {loading ? 'Streaming' : 'Ready'}
            </div>
          </div>

          <MessageList messages={messages} loading={loading} error={error} />
          <ChatComposer
            draft={draft}
            setDraft={setDraft}
            onSend={() => sendMessage()}
            disabled={loading}
          />
        </section>

        <aside className="workspace">
          <ArtifactPanel artifacts={artifacts} />
          <ImagePanel images={images} />
          <SourcePanel sources={sources} onOpenPage={page => setActivePage(page)} />
          <ManualViewer pages={pages} activePage={activePage} onOpenPage={setActivePage} onClose={() => setActivePage(null)} />
          <ToolActivityPanel events={toolEvents} />
        </aside>
      </main>
    </div>
  )
}

function handleEvent(event, actions) {
  if (event.type === 'text_delta') {
    actions.appendAssistant(event.content)
    return
  }

  if (event.type === 'artifact') {
    actions.setArtifacts(prev => [...prev, event])
    return
  }

  if (event.type === 'tool_call') {
    actions.setToolEvents(prev => [
      ...prev,
      { kind: 'call', name: event.name, payload: event.input },
    ])
    return
  }

  if (event.type === 'tool_result') {
    actions.setToolEvents(prev => [
      ...prev,
      { kind: 'result', name: event.name, payload: event.result },
    ])
    hydratePanelsFromTool(event, actions)
    return
  }

  if (event.type === 'error') {
    actions.setError(event.message)
  }
}

function hydratePanelsFromTool(event, actions) {
  const results = event.result?.results

  if (event.name === 'search_manual' && Array.isArray(results)) {
    actions.setSources(dedupeByPage(results))
    return
  }

  if (event.name === 'find_diagram' && Array.isArray(results)) {
    actions.setImages(results)
    return
  }

  if (event.name === 'get_manual_page' && event.result?.page) {
    actions.setPages(prev => addUniquePage(prev, event.result.page))
  }
}

function upsertAssistant(messages, content) {
  const next = [...messages]
  const last = next[next.length - 1]
  if (last?.role === 'assistant') {
    next[next.length - 1] = { role: 'assistant', content }
    return next
  }
  next.push({ role: 'assistant', content })
  return next
}

function dedupeByPage(items) {
  const seen = new Set()
  return items.filter(item => {
    const key = `${item.page}-${item.section ?? ''}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

function addUniquePage(existing, page) {
  return existing.includes(page) ? existing : [...existing, page]
}
