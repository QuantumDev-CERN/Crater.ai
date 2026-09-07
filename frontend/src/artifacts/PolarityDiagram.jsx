export function PolarityDiagram({ data }) {
  const negativeLabel = data.negative_label ?? 'Torch lead'
  const positiveLabel = data.positive_label ?? 'Ground clamp'
  const process = data.process ?? 'TIG'

  return (
    <div className="artifact-body">
      <svg viewBox="0 0 420 220" className="polarity-svg" role="img" aria-label={`${process} polarity diagram`}>
        <rect x="120" y="72" width="180" height="86" rx="18" className="machine-box" />
        <circle cx="170" cy="115" r="22" className="socket negative" />
        <circle cx="250" cy="115" r="22" className="socket positive" />
        <path d="M 48 72 C 88 72, 95 115, 148 115" className="cable negative" />
        <path d="M 368 156 C 326 156, 310 115, 272 115" className="cable positive" />
        <text x="210" y="100" textAnchor="middle" className="svg-label heading">{process} setup</text>
        <text x="170" y="120" textAnchor="middle" className="svg-label">-</text>
        <text x="250" y="120" textAnchor="middle" className="svg-label">+</text>
        <text x="45" y="60" className="svg-label">{negativeLabel}</text>
        <text x="300" y="176" className="svg-label">{positiveLabel}</text>
      </svg>
      <div className="callout-row">
        <div className="callout">
          <strong>Negative socket</strong>
          <p>{negativeLabel}</p>
        </div>
        <div className="callout">
          <strong>Positive socket</strong>
          <p>{positiveLabel}</p>
        </div>
      </div>
    </div>
  )
}
