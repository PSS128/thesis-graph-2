'use client'

type MissingPieces = {
  mediators: string[]
  moderators: string[]
  study_designs: string[]
}

type Props = {
  nodeName: string
  suggestions: MissingPieces | null
  loading: boolean
  onAcceptMediator?: (mediator: string) => void
  onAcceptModerator?: (moderator: string) => void
  onClose: () => void
}

export default function MissingPiecesModal({
  nodeName,
  suggestions,
  loading,
  onAcceptMediator,
  onAcceptModerator,
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
        maxWidth: 700,
        width: '90%',
        maxHeight: '80vh',
        overflow: 'auto',
        boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
        zIndex: 1000
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: 16 }}>
        <h3 style={{ margin: 0, marginBottom: 8 }}>
          Missing Pieces: {nodeName}
        </h3>
        <p style={{ margin: 0, fontSize: 13, color: '#666' }}>
          AI-suggested mediators, moderators, and study designs to strengthen your causal model.
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
          {suggestions.mediators.length > 0 && (
            <div>
              <h4 style={{ margin: 0, marginBottom: 10, fontSize: 14, color: '#1890ff' }}>
                Suggested Mediators (A → M → B)
              </h4>
              <div style={{ display: 'grid', gap: 8 }}>
                {suggestions.mediators.map((mediator, i) => (
                  <div
                    key={i}
                    style={{
                      padding: 12,
                      background: '#f0f5ff',
                      border: '1px solid #adc6ff',
                      borderRadius: 8,
                      fontSize: 13,
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                  >
                    <span style={{ color: '#0050b3' }}>{mediator}</span>
                    {onAcceptMediator && (
                      <button
                        onClick={() => onAcceptMediator(mediator)}
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
                ))}
              </div>
            </div>
          )}

          {/* Moderators */}
          {suggestions.moderators.length > 0 && (
            <div>
              <h4 style={{ margin: 0, marginBottom: 10, fontSize: 14, color: '#722ed1' }}>
                Suggested Moderators (Effect varies by...)
              </h4>
              <div style={{ display: 'grid', gap: 8 }}>
                {suggestions.moderators.map((moderator, i) => (
                  <div
                    key={i}
                    style={{
                      padding: 12,
                      background: '#f9f0ff',
                      border: '1px solid #d3adf7',
                      borderRadius: 8,
                      fontSize: 13,
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                  >
                    <span style={{ color: '#531dab' }}>{moderator}</span>
                    {onAcceptModerator && (
                      <button
                        onClick={() => onAcceptModerator(moderator)}
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
                ))}
              </div>
            </div>
          )}

          {/* Study Designs */}
          {suggestions.study_designs.length > 0 && (
            <div>
              <h4 style={{ margin: 0, marginBottom: 10, fontSize: 14, color: '#237804' }}>
                Suggested Study Designs
              </h4>
              <div style={{ display: 'grid', gap: 8 }}>
                {suggestions.study_designs.map((design, i) => (
                  <div
                    key={i}
                    style={{
                      padding: 12,
                      background: '#f6ffed',
                      border: '1px solid #b7eb8f',
                      borderRadius: 8,
                      fontSize: 13,
                      color: '#135200'
                    }}
                  >
                    {design}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Empty state */}
          {suggestions.mediators.length === 0 &&
            suggestions.moderators.length === 0 &&
            suggestions.study_designs.length === 0 && (
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
