'use client'

type Warning = {
  node_or_edge_id: string
  label: string
  fix_suggestion: string
}

type Props = {
  warnings: Warning[]
  loading: boolean
  onClose: () => void
}

export default function GraphCritiquePanel({ warnings, loading, onClose }: Props) {
  return (
    <div
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        maxHeight: '40vh',
        background: '#fff',
        borderTop: '2px solid #ddd',
        boxShadow: '0 -4px 12px rgba(0,0,0,0.1)',
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: 16,
          borderBottom: '1px solid #e5e5e5',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: '#fafafa'
        }}
      >
        <div>
          <h3 style={{ margin: 0, fontSize: 16 }}>
            Graph Critique
          </h3>
          <p style={{ margin: 0, fontSize: 12, color: '#666', marginTop: 4 }}>
            DAG validation warnings and suggestions
          </p>
        </div>
        <button
          onClick={onClose}
          style={{
            border: 'none',
            background: 'transparent',
            fontSize: 20,
            cursor: 'pointer',
            padding: '4px 8px',
            color: '#666'
          }}
          title="Close critique panel"
        >
          ×
        </button>
      </div>

      {/* Content */}
      <div style={{ padding: 16, flex: 1, overflowY: 'auto' }}>
        {loading && (
          <div style={{ textAlign: 'center', padding: 24, color: '#666' }}>
            Analyzing graph structure...
          </div>
        )}

        {!loading && warnings.length === 0 && (
          <div
            style={{
              textAlign: 'center',
              padding: 24,
              color: '#52c41a',
              fontSize: 14
            }}
          >
            ✓ No issues found! Your graph structure looks good.
          </div>
        )}

        {!loading && warnings.length > 0 && (
          <div style={{ display: 'grid', gap: 12 }}>
            {warnings.map((warning, idx) => (
              <div
                key={idx}
                style={{
                  padding: 14,
                  border: '1px solid #ffccc7',
                  borderLeft: '4px solid #ff4d4f',
                  borderRadius: 8,
                  background: '#fff2f0'
                }}
              >
                {/* Warning header */}
                <div style={{ marginBottom: 8 }}>
                  <span
                    style={{
                      display: 'inline-block',
                      padding: '2px 8px',
                      borderRadius: 4,
                      fontSize: 11,
                      fontWeight: 600,
                      background: '#ffa39e',
                      color: '#820014',
                      marginRight: 8
                    }}
                  >
                    {warning.node_or_edge_id}
                  </span>
                  <span style={{ fontSize: 13, fontWeight: 600, color: '#cf1322' }}>
                    {warning.label}
                  </span>
                </div>

                {/* Fix suggestion */}
                <div style={{ fontSize: 13, color: '#595959', lineHeight: 1.5 }}>
                  <strong style={{ color: '#262626' }}>Fix:</strong> {warning.fix_suggestion}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
