'use client'

type Props = {
  nodeId: string
  nodeName: string
  x: number
  y: number
  onFindMissingPieces: () => void
  onDelete?: () => void
  onClose: () => void
}

export default function NodeContextMenu({
  nodeId,
  nodeName,
  x,
  y,
  onFindMissingPieces,
  onDelete,
  onClose
}: Props) {
  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          zIndex: 999
        }}
      />

      {/* Menu */}
      <div
        style={{
          position: 'fixed',
          top: y,
          left: x,
          background: '#fff',
          border: '1px solid #d9d9d9',
          borderRadius: 8,
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          minWidth: 220,
          zIndex: 1000,
          overflow: 'hidden'
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '8px 12px',
            borderBottom: '1px solid #f0f0f0',
            fontSize: 12,
            color: '#999',
            fontWeight: 600
          }}
        >
          {nodeName}
        </div>

        {/* Menu items */}
        <div>
          <button
            onClick={() => {
              onFindMissingPieces()
              onClose()
            }}
            style={{
              width: '100%',
              padding: '10px 12px',
              border: 'none',
              background: 'transparent',
              textAlign: 'left',
              fontSize: 13,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              color: '#262626'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#f5f5f5'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent'
            }}
          >
            <span style={{ fontSize: 16 }}>🔍</span>
            <span>Find Missing Pieces</span>
          </button>

          {onDelete && (
            <button
              onClick={() => {
                onDelete()
                onClose()
              }}
              style={{
                width: '100%',
                padding: '10px 12px',
                border: 'none',
                background: 'transparent',
                textAlign: 'left',
                fontSize: 13,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                color: '#ff4d4f',
                borderTop: '1px solid #f0f0f0'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#fff1f0'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'transparent'
              }}
            >
              <span style={{ fontSize: 16 }}>🗑️</span>
              <span>Delete Node</span>
            </button>
          )}
        </div>
      </div>
    </>
  )
}
