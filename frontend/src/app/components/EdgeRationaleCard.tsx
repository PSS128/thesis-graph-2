'use client'

import { useState } from 'react'

type EdgeRationale = {
  mechanisms: string[]
  assumptions: string[]
  likely_confounders: string[]
  prior_evidence_types: string[]
}

type Props = {
  fromName: string
  toName: string
  edgeType: string
  rationale: EdgeRationale | null
  loading: boolean
  onAccept: () => void
  onReject: () => void
  onClose: () => void
}

export default function EdgeRationaleCard({
  fromName,
  toName,
  edgeType,
  rationale,
  loading,
  onAccept,
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
          Proposed Edge: {edgeType}
        </h3>
        <p style={{ margin: 0, fontSize: 14, color: '#666' }}>
          <strong>{fromName}</strong> → <strong>{toName}</strong>
        </p>
      </div>

      {/* Loading state */}
      {loading && (
        <div style={{ textAlign: 'center', padding: 24, color: '#666' }}>
          Analyzing causal relationship...
        </div>
      )}

      {/* Rationale content */}
      {!loading && rationale && (
        <div style={{ display: 'grid', gap: 16 }}>
          {/* Mechanisms */}
          {rationale.mechanisms.length > 0 && (
            <div>
              <h4 style={{ margin: 0, marginBottom: 8, fontSize: 14, color: '#237804' }}>
                Mechanisms (How does this work?)
              </h4>
              <ul style={{ margin: 0, paddingLeft: 20, fontSize: 13 }}>
                {rationale.mechanisms.map((m, i) => (
                  <li key={i} style={{ marginBottom: 4 }}>
                    {m}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Assumptions */}
          {rationale.assumptions.length > 0 && (
            <div>
              <h4 style={{ margin: 0, marginBottom: 8, fontSize: 14, color: '#0958d9' }}>
                Assumptions (What must be true?)
              </h4>
              <ul style={{ margin: 0, paddingLeft: 20, fontSize: 13 }}>
                {rationale.assumptions.map((a, i) => (
                  <li key={i} style={{ marginBottom: 4 }}>
                    {a}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Confounders */}
          {rationale.likely_confounders.length > 0 && (
            <div>
              <h4 style={{ margin: 0, marginBottom: 8, fontSize: 14, color: '#d48806' }}>
                Potential Confounders (What else could explain this?)
              </h4>
              <ul style={{ margin: 0, paddingLeft: 20, fontSize: 13 }}>
                {rationale.likely_confounders.map((c, i) => (
                  <li key={i} style={{ marginBottom: 4 }}>
                    {c}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Prior Evidence */}
          {rationale.prior_evidence_types.length > 0 && (
            <div>
              <h4 style={{ margin: 0, marginBottom: 8, fontSize: 14, color: '#722ed1' }}>
                Prior Evidence Types
              </h4>
              <div style={{ fontSize: 13, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {rationale.prior_evidence_types.map((e, i) => (
                  <span
                    key={i}
                    style={{
                      padding: '4px 10px',
                      background: '#f0f0f0',
                      borderRadius: 6,
                      fontSize: 12
                    }}
                  >
                    {e}
                  </span>
                ))}
              </div>
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
          Accept Edge
        </button>
      </div>
    </div>
  )
}
