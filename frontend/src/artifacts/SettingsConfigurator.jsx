import { useState } from 'react'

export function SettingsConfigurator({ data }) {
  const [process, setProcess] = useState(data.process ?? 'MIG')
  const [material, setMaterial] = useState(data.material ?? 'Steel')
  const [thickness, setThickness] = useState(Number(data.thickness ?? 3))

  const recommendation = recommend(process, material, thickness, data)

  return (
    <div className="artifact-body">
      <div className="control-grid">
        <label>
          Process
          <select value={process} onChange={e => setProcess(e.target.value)}>
            <option>MIG</option>
            <option>TIG</option>
            <option>Stick</option>
            <option>Flux Core</option>
          </select>
        </label>
        <label>
          Material
          <select value={material} onChange={e => setMaterial(e.target.value)}>
            <option>Steel</option>
            <option>Stainless</option>
            <option>Aluminum</option>
          </select>
        </label>
        <label>
          Thickness (mm)
          <input type="number" min="1" max="12" step="0.5" value={thickness} onChange={e => setThickness(Number(e.target.value))} />
        </label>
      </div>

      <div className="recommendation-grid">
        <Metric title="Voltage" value={recommendation.voltage} />
        <Metric title="Wire feed" value={recommendation.wireFeed} />
        <Metric title="Polarity" value={recommendation.polarity} />
        <Metric title="Shielding gas" value={recommendation.gas} />
        <Metric title="Duty cycle" value={recommendation.dutyCycle} />
      </div>
    </div>
  )
}

function recommend(process, material, thickness, data) {
  const isAluminum = material === 'Aluminum'
  const baseVoltage = data.voltage ?? Math.round(17 + thickness * 1.6)
  const baseWireFeed = data.wire_feed ?? Math.round(180 + thickness * 35)

  return {
    voltage: `${baseVoltage} V`,
    wireFeed: `${baseWireFeed} ipm`,
    polarity: process === 'TIG' ? 'DCEN' : process === 'Flux Core' ? 'DCEN or per wire' : 'DCEP',
    gas: isAluminum ? '100% argon' : process === 'Flux Core' ? 'Self-shielded or 75/25' : '75/25 argon-CO2',
    dutyCycle: `${data.duty_cycle ?? (thickness >= 6 ? 40 : 60)}%`,
  }
}

function Metric({ title, value }) {
  return (
    <div className="metric-card">
      <span>{title}</span>
      <strong>{value}</strong>
    </div>
  )
}
