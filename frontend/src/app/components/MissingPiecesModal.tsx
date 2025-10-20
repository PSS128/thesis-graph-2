'use client'

type MediatorDetail = {
  name: string
  definition: string
  rationale: string
}

type ModeratorDetail = {
  name: string
  definition: string
  rationale: string
}

type MeasurementIdea = {
  approach: string
  description: string
  pros: string[]
  cons: string[]
}

type ConfounderDetail = {
  name: string
  definition: string
  rationale: string
}

type MissingPieces = {
  mediators: MediatorDetail[]
  moderators: ModeratorDetail[]
  measurements: MeasurementIdea[]
  confounders: ConfounderDetail[]
}

type Props = {
  nodeName: string
  suggestions: MissingPieces | null
  loading: boolean
  onAcceptMediator?: (mediator: MediatorDetail) => void
  onAcceptModerator?: (moderator: ModeratorDetail) => void
  onAcceptConfounder?: (confounder: ConfounderDetail) => void
  onClose: () => void
}

export default function MissingPiecesModal({
  nodeName,
  suggestions,
  loading,
  onAcceptMediator,
  onAcceptModerator,
  onAcceptConfounder,
  onClose
}: Props) {
  return (
    <div
      style={{
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        background: '#fff',
        border: '2px solid #333',
        borderRadius: 12,
        padding: 24,
        maxWidth: 800,
        width: '90%',
        maxHeight: '85vh',
        overflow: 'auto',
        boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
        zIndex: 1000
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: 16 }}>
        <h3 style={{ margin: 0, marginBottom: 8 }}>
          🔍 Missing Pieces: {nodeName}
        </h3>
        <p style={{ margin: 0, fontSize: 13, color: '#666' }}>
          AI-suggested mediators, moderators, measurements, and confounders to strengthen your causal model.
        </p>
      </div>

      {/* Loading state */}
      {loading && (
        <div style={{ textAlign: 'center', padding: 24, color: '#666' }}>
          Analyzing graph structure for missing pieces...
        </div>
      )}

      {/* Suggestions content */}
      {!loading && suggestions && (
        <div style={{ display: 'grid', gap: 20 }}>
          {/* Mediators */}
          {suggestions.mediators?.length > 0 && (
            <div>
              <h4 style={{ margin: 0, marginBottom: 12, fontSize: 15, color: '#1890ff', fontWeight: 600 }}>
                📍 Mediating Variables
              </h4>
              <p style={{ margin: '0 0 10px 0', fontSize: 12, color: '#666' }}>
                Variables that might sit on causal paths (A → M → B)
              </p>
              <div style={{ display: 'grid', gap: 10 }}>
                {suggestions.mediators.map((med, i) => (
                  <div
                    key={i}
                    style={{
                      padding: 14,
                      background: '#f0f5ff',
                      border: '1px solid #adc6ff',
                      borderRadius: 8
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 8 }}>
                      <strong style={{ color: '#0050b3', fontSize: 14 }}>{med.name}</strong>
                      {onAcceptMediator && (
                        <button
                          onClick={() => onAcceptMediator(med)}
                          style={{
                            padding: '4px 12px',
                            fontSize: 11,
                            border: '1px solid #1890ff',
                            background: '#fff',
                            color: '#1890ff',
                            borderRadius: 4,
                            cursor: 'pointer',
                            fontWeight: 600
                          }}
                        >
                          + Add
                        </button>
                      )}
                    </div>
                    <p style={{ margin: '0 0 6px 0', fontSize: 12, color: '#262626' }}>{med.definition}</p>
                    <p style={{ margin: 0, fontSize: 11, color: '#666', fontStyle: 'italic' }}>
                      Why: {med.rationale}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Moderators */}
          {suggestions.moderators?.length > 0 && (
            <div>
              <h4 style={{ margin: 0, marginBottom: 12, fontSize: 15, color: '#722ed1', fontWeight: 600 }}>
                ⚙️ Moderating Conditions
              </h4>
              <p style={{ margin: '0 0 10px 0', fontSize: 12, color: '#666' }}>
                Conditions that might strengthen or weaken effects
              </p>
              <div style={{ display: 'grid', gap: 10 }}>
                {suggestions.moderators.map((mod, i) => (
                  <div
                    key={i}
                    style={{
                      padding: 14,
                      background: '#f9f0ff',
                      border: '1px solid #d3adf7',
                      borderRadius: 8
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 8 }}>
                      <strong style={{ color: '#531dab', fontSize: 14 }}>{mod.name}</strong>
                      {onAcceptModerator && (
                        <button
                          onClick={() => onAcceptModerator(mod)}
                          style={{
                            padding: '4px 12px',
                            fontSize: 11,
                            border: '1px solid #722ed1',
                            background: '#fff',
                            color: '#722ed1',
                            borderRadius: 4,
                            cursor: 'pointer',
                            fontWeight: 600
                          }}
                        >
                          + Add
                        </button>
                      )}
                    </div>
                    <p style={{ margin: '0 0 6px 0', fontSize: 12, color: '#262626' }}>{mod.definition}</p>
                    <p style={{ margin: 0, fontSize: 11, color: '#666', fontStyle: 'italic' }}>
                      How: {mod.rationale}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Measurements */}
          {suggestions.measurements?.length > 0 && (
            <div>
              <h4 style={{ margin: 0, marginBottom: 12, fontSize: 15, color: '#13c2c2', fontWeight: 600 }}>
                📊 Measurement Approaches
              </h4>
              <p style={{ margin: '0 0 10px 0', fontSize: 12, color: '#666' }}>
                Concrete ways to operationalize and measure this variable
              </p>
              <div style={{ display: 'grid', gap: 10 }}>
                {suggestions.measurements.map((meas, i) => (
                  <div
                    key={i}
                    style={{
                      padding: 14,
                      background: '#e6fffb',
                      border: '1px solid #87e8de',
                      borderRadius: 8
                    }}
                  >
                    <strong style={{ color: '#006d75', fontSize: 14, display: 'block', marginBottom: 6 }}>{meas.approach}</strong>
                    <p style={{ margin: '0 0 8px 0', fontSize: 12, color: '#262626' }}>{meas.description}</p>
                    {meas.pros.length > 0 && (
                      <div style={{ marginBottom: 6 }}>
                        <span style={{ fontSize: 11, color: '#237804', fontWeight: 600 }}>Pros: </span>
                        <span style={{ fontSize: 11, color: '#595959' }}>{meas.pros.join(', ')}</span>
                      </div>
                    )}
                    {meas.cons.length > 0 && (
                      <div>
                        <span style={{ fontSize: 11, color: '#cf1322', fontWeight: 600 }}>Cons: </span>
                        <span style={{ fontSize: 11, color: '#595959' }}>{meas.cons.join(', ')}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Confounders */}
          {suggestions.confounders?.length > 0 && (
            <div>
              <h4 style={{ margin: 0, marginBottom: 12, fontSize: 15, color: '#fa8c16', fontWeight: 600 }}>
                ⚠️ Potential Confounders
              </h4>
              <p style={{ margin: '0 0 10px 0', fontSize: 12, color: '#666' }}>
                Variables that might bias the relationships if not accounted for
              </p>
              <div style={{ display: 'grid', gap: 10 }}>
                {suggestions.confounders.map((conf, i) => (
                  <div
                    key={i}
                    style={{
                      padding: 14,
                      background: '#fff7e6',
                      border: '1px solid #ffd591',
                      borderRadius: 8
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 8 }}>
                      <strong style={{ color: '#d46b08', fontSize: 14 }}>{conf.name}</strong>
                      {onAcceptConfounder && (
                        <button
                          onClick={() => onAcceptConfounder(conf)}
                          style={{
                            padding: '4px 12px',
                            fontSize: 11,
                            border: '1px solid #fa8c16',
                            background: '#fff',
                            color: '#fa8c16',
                            borderRadius: 4,
                            cursor: 'pointer',
                            fontWeight: 600
                          }}
                        >
                          + Add
                        </button>
                      )}
                    </div>
                    <p style={{ margin: '0 0 6px 0', fontSize: 12, color: '#262626' }}>{conf.definition}</p>
                    <p style={{ margin: 0, fontSize: 11, color: '#666', fontStyle: 'italic' }}>
                      Risk: {conf.rationale}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Empty state */}
          {(!suggestions.mediators || suggestions.mediators.length === 0) &&
            (!suggestions.moderators || suggestions.moderators.length === 0) &&
            (!suggestions.measurements || suggestions.measurements.length === 0) &&
            (!suggestions.confounders || suggestions.confounders.length === 0) && (
              <div style={{ textAlign: 'center', padding: 24, color: '#999' }}>
                No suggestions found for this context.
              </div>
            )}
        </div>
      )}

      {/* Close button */}
      <div
        style={{
          marginTop: 24,
          display: 'flex',
          justifyContent: 'flex-end',
          borderTop: '1px solid #e5e5e5',
          paddingTop: 16
        }}
      >
        <button
          onClick={onClose}
          disabled={loading}
          style={{
            padding: '8px 20px',
            border: '1px solid #d9d9d9',
            color: '#262626',
            background: '#fff',
            borderRadius: 8,
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1,
            fontWeight: 600
          }}
        >
          Close
        </button>
      </div>
    </div>
  )
}
