import { useState } from 'react'

export function DutyCycleCalculator({ data }) {
  const [current, setCurrent] = useState(Number(data.current ?? 150))
  const [voltage, setVoltage] = useState(Number(data.voltage ?? 24))
  const [process, setProcess] = useState(data.process ?? 'MIG')

  const dutyCycle = Number(data.duty_cycle ?? estimateDutyCycle(current))
  const weldMinutes = Number(((dutyCycle / 100) * 10).toFixed(1))
  const cooldownMinutes = Number((10 - weldMinutes).toFixed(1))

  return (
    <div className="artifact-body">
      <div className="control-grid">
        <label>
          Current
          <input type="range" min="40" max="220" value={current} onChange={e => setCurrent(Number(e.target.value))} />
          <span>{current} A</span>
        </label>
        <label>
          Voltage
          <input type="number" min="10" max="40" value={voltage} onChange={e => setVoltage(Number(e.target.value))} />
          <span>{voltage} V</span>
        </label>
        <label>
          Process
          <select value={process} onChange={e => setProcess(e.target.value)}>
            <option>MIG</option>
            <option>TIG</option>
            <option>Stick</option>
            <option>Flux Core</option>
          </select>
        </label>
      </div>

      <div className="metric-row">
        <MetricCard label="Duty cycle" value={`${dutyCycle}%`} />
        <MetricCard label="Safe weld window" value={`${weldMinutes} min`} />
        <MetricCard label="Cooldown window" value={`${cooldownMinutes} min`} />
      </div>

      <p className="muted">
        Estimated {process} operating window at {current}A and {voltage}V over a 10-minute cycle.
      </p>
    </div>
  )
}

function estimateDutyCycle(current) {
  if (current >= 200) return 30
  if (current >= 170) return 40
  if (current >= 140) return 50
  if (current >= 110) return 60
  return 80
}

function MetricCard({ label, value }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}
