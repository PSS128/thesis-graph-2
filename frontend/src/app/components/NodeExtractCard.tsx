'use client'

type NodeExtraction = {
  name: string
  definition: string
  synonyms: string[]
  measurement_ideas: string[]
  merge_hint?: {
    existing_name: string
    similarity: number
    action: string
  }
}

type Props = {
  extraction: NodeExtraction | null
  loading: boolean
  onAccept: () => void
  onMerge?: () => void
  onReject: () => void
  onClose: () => void
}

export default function NodeExtractCard({
  extraction,
  loading,
  onAccept,
  onMerge,
  onReject,
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
        maxWidth: 600,
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
          Extract Variable from Text
        </h3>
        <p style={{ margin: 0, fontSize: 13, color: '#666' }}>
          Review the AI-extracted variable and decide whether to add it to your graph.
        </p>
      </div>

      {/* Loading state */}
      {loading && (
        <div style={{ textAlign: 'center', padding: 24, color: '#666' }}>
          Extracting variable from highlighted text...
        </div>
      )}

      {/* Extraction content */}
      {!loading && extraction && (
        <div style={{ display: 'grid', gap: 16 }}>
          {/* Merge hint banner */}
          {extraction.merge_hint && (
            <div
              style={{
                padding: 12,
                background: '#fff7e6',
                border: '1px solid #ffa940',
                borderRadius: 8,
                fontSize: 13
              }}
            >
              <strong style={{ color: '#d48806' }}>Merge Suggestion:</strong>
              <div style={{ marginTop: 4 }}>
                This variable appears similar to existing node{' '}
                <strong>&quot;{extraction.merge_hint.existing_name}&quot;</strong>{' '}
                (similarity: {(extraction.merge_hint.similarity * 100).toFixed(0)}%).
              </div>
            </div>
          )}

          {/* Variable Name */}
          <div>
            <h4 style={{ margin: 0, marginBottom: 8, fontSize: 14, color: '#1890ff' }}>
              Variable Name
            </h4>
            <div
              style={{
                padding: 12,
                background: '#f0f5ff',
                borderRadius: 6,
                fontSize: 15,
                fontWeight: 600,
                color: '#0050b3'
              }}
            >
              {extraction.name}
            </div>
          </div>

          {/* Definition */}
          <div>
            <h4 style={{ margin: 0, marginBottom: 8, fontSize: 14, color: '#237804' }}>
              Definition
            </h4>
            <div
              style={{
                padding: 12,
                background: '#f6ffed',
                borderRadius: 6,
                fontSize: 13,
                lineHeight: 1.6,
                color: '#135200'
              }}
            >
              {extraction.definition}
            </div>
          </div>

          {/* Synonyms */}
          {extraction.synonyms.length > 0 && (
            <div>
              <h4 style={{ margin: 0, marginBottom: 8, fontSize: 14, color: '#722ed1' }}>
                Synonyms & Related Terms
              </h4>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {extraction.synonyms.map((syn, i) => (
                  <span
                    key={i}
                    style={{
                      padding: '4px 10px',
                      background: '#f9f0ff',
                      border: '1px solid #d3adf7',
                      borderRadius: 6,
                      fontSize: 12,
                      color: '#531dab'
                    }}
                  >
                    {syn}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Measurement Ideas */}
          {extraction.measurement_ideas.length > 0 && (
            <div>
              <h4 style={{ margin: 0, marginBottom: 8, fontSize: 14, color: '#0958d9' }}>
                Measurement Ideas
              </h4>
              <ul style={{ margin: 0, paddingLeft: 20, fontSize: 13 }}>
                {extraction.measurement_ideas.map((idea, i) => (
                  <li key={i} style={{ marginBottom: 4, color: '#003a8c' }}>
                    {idea}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Action buttons */}
      <div
        style={{
          marginTop: 24,
          display: 'flex',
          gap: 12,
          justifyContent: 'flex-end',
          borderTop: '1px solid #e5e5e5',
          paddingTop: 16
        }}
      >
        <button
          onClick={onReject}
          disabled={loading}
          style={{
            padding: '8px 16px',
            border: '1px solid #ff4d4f',
            color: '#ff4d4f',
            background: '#fff',
            borderRadius: 8,
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1
          }}
        >
          Reject
        </button>
        <button
          onClick={onClose}
          disabled={loading}
          style={{
            padding: '8px 16px',
            border: '1px solid #999',
            color: '#666',
            background: '#fff',
            borderRadius: 8,
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1
          }}
        >
          Cancel
        </button>
        {extraction?.merge_hint && onMerge && (
          <button
            onClick={onMerge}
            disabled={loading}
            style={{
              padding: '8px 16px',
              border: 'none',
              color: '#fff',
              background: loading ? '#999' : '#fa8c16',
              borderRadius: 8,
              cursor: loading ? 'not-allowed' : 'pointer',
              fontWeight: 600
            }}
          >
            Merge with Existing
          </button>
        )}
        <button
          onClick={onAccept}
          disabled={loading}
          style={{
            padding: '8px 16px',
            border: 'none',
            color: '#fff',
            background: loading ? '#999' : '#52c41a',
            borderRadius: 8,
            cursor: loading ? 'not-allowed' : 'pointer',
            fontWeight: 600
          }}
        >
          Add as New Node
        </button>
      </div>
    </div>
  )
}
