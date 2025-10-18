'use client'

type EvidenceItem = {
  title?: string
  url?: string
  quote: string
  supports: 'supports' | 'contradicts'
  strength: number
}

type Props = {
  evidence: EvidenceItem[]
  loading: boolean
  onPin?: (item: EvidenceItem) => void
  onClose: () => void
}

export default function CitationPanel({ evidence, loading, onPin, onClose }: Props) {
  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        width: 400,
        height: '100vh',
        background: '#fff',
        borderLeft: '2px solid #ddd',
        boxShadow: '-4px 0 12px rgba(0,0,0,0.1)',
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto'
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
          position: 'sticky',
          top: 0,
          background: '#fff',
          zIndex: 1
        }}
      >
        <h3 style={{ margin: 0, fontSize: 16 }}>Evidence</h3>
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
          title="Close panel"
        >
          ×
        </button>
      </div>

      {/* Content */}
      <div style={{ padding: 16, flex: 1 }}>
        {loading && (
          <div style={{ textAlign: 'center', padding: 24, color: '#666' }}>
            Searching for evidence...
          </div>
        )}

        {!loading && evidence.length === 0 && (
          <div style={{ textAlign: 'center', padding: 24, color: '#999' }}>
            No evidence found. Upload documents to enable evidence retrieval.
          </div>
        )}

        {!loading && evidence.length > 0 && (
          <div style={{ display: 'grid', gap: 16 }}>
            {evidence.map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: 12,
                  border: '1px solid #e5e5e5',
                  borderRadius: 8,
                  background: '#fafafa'
                }}
              >
                {/* Support/Contradict badge */}
                <div style={{ marginBottom: 8 }}>
                  <span
                    style={{
                      display: 'inline-block',
                      padding: '2px 8px',
                      borderRadius: 4,
                      fontSize: 11,
                      fontWeight: 600,
                      background: item.supports === 'supports' ? '#e6ffed' : '#fff1f0',
                      color: item.supports === 'supports' ? '#237804' : '#a8071a',
                      border: `1px solid ${item.supports === 'supports' ? '#52c41a' : '#ff4d4f'}`
                    }}
                  >
                    {item.supports === 'supports' ? '✓ SUPPORTS' : '✗ CONTRADICTS'}
                  </span>
                  <span style={{ marginLeft: 8, fontSize: 11, color: '#999' }}>
                    strength: {item.strength.toFixed(3)}
                  </span>
                </div>

                {/* Source title */}
                {item.title && (
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6, color: '#333' }}>
                    {item.title}
                  </div>
                )}

                {/* Quote */}
                <div
                  style={{
                    fontSize: 13,
                    lineHeight: 1.5,
                    color: '#555',
                    marginBottom: 8,
                    fontStyle: 'italic'
                  }}
                >
                  "{item.quote}"
                </div>

                {/* URL */}
                {item.url && (
                  <div style={{ fontSize: 11, color: '#666', marginBottom: 8 }}>
                    <a href={item.url} target="_blank" rel="noopener noreferrer" style={{ color: '#1890ff' }}>
                      {item.url}
                    </a>
                  </div>
                )}

                {/* Pin button */}
                {onPin && (
                  <button
                    onClick={() => onPin(item)}
                    style={{
                      padding: '4px 10px',
                      fontSize: 11,
                      border: '1px solid #1890ff',
                      background: '#fff',
                      color: '#1890ff',
                      borderRadius: 4,
                      cursor: 'pointer'
                    }}
                    title="Pin this citation to the edge"
                  >
                    📌 Pin to Edge
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
