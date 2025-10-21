'use client'

import React from 'react'

type ProgressBarProps = {
  progress: number // 0-100
  message?: string
  variant?: 'determinate' | 'indeterminate'
  color?: string
}

export default function ProgressBar({
  progress,
  message,
  variant = 'determinate',
  color = '#1890ff'
}: ProgressBarProps) {
  const clampedProgress = Math.min(100, Math.max(0, progress))

  return (
    <div style={{ width: '100%', padding: '12px 0' }}>
      {message && (
        <div style={{
          fontSize: 14,
          color: '#666',
          marginBottom: 8,
          fontWeight: 500
        }}>
          {message}
        </div>
      )}

      <div
        style={{
          width: '100%',
          height: 8,
          background: '#f0f0f0',
          borderRadius: 4,
          overflow: 'hidden',
          position: 'relative'
        }}
      >
        {variant === 'determinate' ? (
          <div
            style={{
              height: '100%',
              width: `${clampedProgress}%`,
              background: color,
              borderRadius: 4,
              transition: 'width 0.3s ease'
            }}
          />
        ) : (
          <div
            style={{
              height: '100%',
              width: '30%',
              background: color,
              borderRadius: 4,
              animation: 'indeterminate 1.5s infinite'
            }}
          />
        )}
      </div>

      {variant === 'determinate' && (
        <div style={{
          fontSize: 12,
          color: '#999',
          marginTop: 4,
          textAlign: 'right'
        }}>
          {Math.round(clampedProgress)}%
        </div>
      )}

      <style jsx>{`
        @keyframes indeterminate {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(400%);
          }
        }
      `}</style>
    </div>
  )
}
