import { useState } from 'react'

const DEFAULT_PARTS = [
  {
    id: 'spool',
    label: 'Spool',
    description: 'Stores filler wire and should unwind smoothly without excess drag.',
  },
  {
    id: 'roller',
    label: 'Drive roller',
    description: 'Pushes wire forward. Groove size must match the wire diameter.',
  },
  {
    id: 'tensioner',
    label: 'Tensioner',
    description: 'Applies pressure so the drive roller feeds consistently without crushing wire.',
  },
  {
    id: 'liner',
    label: 'Liner',
    description: 'Guides wire through the torch. Replace if feeding becomes rough or contaminated.',
  },
]

export function WireFeedExplainer({ data }) {
  const parts = data.parts ?? DEFAULT_PARTS
  const [selected, setSelected] = useState(parts[0])

  return (
    <div className="artifact-body wirefeed">
      <div className="wirefeed-visual">
        {parts.map(part => (
          <button
            key={part.id}
            type="button"
            className={`wire-node ${selected.id === part.id ? 'selected' : ''}`}
            onClick={() => setSelected(part)}
          >
            {part.label}
          </button>
        ))}
      </div>
      <div className="callout">
        <strong>{selected.label}</strong>
        <p>{selected.description}</p>
      </div>
    </div>
  )
}
