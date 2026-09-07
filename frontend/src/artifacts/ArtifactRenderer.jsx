import { DutyCycleCalculator } from './DutyCycleCalculator'
import { DutyCycleVisualizer } from './DutyCycleVisualizer'
import { PolarityDiagram } from './PolarityDiagram'
import { SettingsConfigurator } from './SettingsConfigurator'
import { TroubleshootingWizard } from './TroubleshootingWizard'
import { WireFeedExplainer } from './WireFeedExplainer'

const LABELS = {
  duty_cycle_calculator: 'Duty cycle calculator',
  duty_cycle_visualizer: 'Duty cycle visualizer',
  polarity_diagram: 'Polarity diagram',
  settings_configurator: 'Settings configurator',
  troubleshooting_wizard: 'Troubleshooting wizard',
  wire_feed_explainer: 'Wire feed explainer',
}

export function ArtifactRenderer({ artifact }) {
  const title = artifact.title || LABELS[artifact.artifact_type] || artifact.artifact_type

  return (
    <article className="artifact-card">
      <div className="artifact-head">
        <p className="panel-label">Artifact</p>
        <h3>{title}</h3>
      </div>
      {renderArtifact(artifact)}
    </article>
  )
}

function renderArtifact(artifact) {
  switch (artifact.artifact_type) {
    case 'duty_cycle_calculator':
      return <DutyCycleCalculator data={artifact.data} />
    case 'duty_cycle_visualizer':
      return <DutyCycleVisualizer data={artifact.data} />
    case 'polarity_diagram':
      return <PolarityDiagram data={artifact.data} />
    case 'settings_configurator':
      return <SettingsConfigurator data={artifact.data} />
    case 'troubleshooting_wizard':
      return <TroubleshootingWizard data={artifact.data} />
    case 'wire_feed_explainer':
      return <WireFeedExplainer data={artifact.data} />
    default:
      return <pre>{JSON.stringify(artifact.data, null, 2)}</pre>
  }
}
