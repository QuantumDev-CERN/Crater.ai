export function DutyCycleVisualizer({ data }) {
  const dutyCycle = Number(data.duty_cycle ?? 40)
  const weldMinutes = Number(((dutyCycle / 100) * 10).toFixed(1))
  const cooldownMinutes = Number((10 - weldMinutes).toFixed(1))

  return (
    <div className="artifact-body">
      <div className="bar-track">
        <div className="bar-fill" style={{ width: `${dutyCycle}%` }} />
      </div>
      <div className="metric-row">
        <Metric label="Duty cycle" value={`${dutyCycle}%`} />
        <Metric label="Weld" value={`${weldMinutes} min`} />
        <Metric label="Cool" value={`${cooldownMinutes} min`} />
      </div>
      <p className="muted">A 10-minute reference cycle makes the safe weld and cooldown rhythm easy to visualize.</p>
    </div>
  )
}

function Metric({ label, value }) {
  return (
    <div className="metric-card compact">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}
