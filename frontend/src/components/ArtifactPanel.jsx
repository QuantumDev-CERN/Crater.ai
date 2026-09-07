import { ArtifactRenderer } from '../artifacts/ArtifactRenderer'

export function ArtifactPanel({ artifacts }) {
  return (
    <section className="panel">
      <div className="panel-head compact">
        <div>
          <p className="panel-label">Artifacts</p>
          <h2>Interactive helpers</h2>
        </div>
      </div>
      {artifacts.length ? (
        <div className="artifact-stack">
          {artifacts.map((artifact, index) => (
            <ArtifactRenderer key={`${artifact.artifact_type}-${index}`} artifact={artifact} />
          ))}
        </div>
      ) : (
        <p className="muted">Widgets appear here when the agent decides a tool is more helpful than a paragraph.</p>
      )}
    </section>
  )
}
