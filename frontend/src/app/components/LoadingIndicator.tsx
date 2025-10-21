'use client'

import React from 'react'

type LoadingIndicatorProps = {
  message?: string
  size?: 'small' | 'medium' | 'large'
  variant?: 'spinner' | 'skeleton' | 'dots'
}

export default function LoadingIndicator({
  message = 'Loading...',
  size = 'medium',
  variant = 'spinner'
}: LoadingIndicatorProps) {
  const sizeMap = {
    small: 16,
    medium: 32,
    large: 48
  }

  const spinnerSize = sizeMap[size]

  if (variant === 'spinner') {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 12,
        padding: 16
      }}>
        <div
          style={{
            width: spinnerSize,
            height: spinnerSize,
            border: `${Math.max(2, spinnerSize / 16)}px solid #e6f7ff`,
            borderTop: `${Math.max(2, spinnerSize / 16)}px solid #1890ff`,
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }}
        />
        {message && (
          <div style={{
            fontSize: size === 'small' ? 12 : size === 'medium' ? 14 : 16,
            color: '#666',
            fontWeight: 500
          }}>
            {message}
          </div>
        )}
        <style jsx>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    )
  }

  if (variant === 'dots') {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: 16
      }}>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              style={{
                width: size === 'small' ? 6 : size === 'medium' ? 8 : 10,
                height: size === 'small' ? 6 : size === 'medium' ? 8 : 10,
                borderRadius: '50%',
                background: '#1890ff',
                animation: `bounce 1.4s infinite ease-in-out ${i * 0.16}s`
              }}
            />
          ))}
        </div>
        {message && (
          <div style={{
            fontSize: size === 'small' ? 12 : size === 'medium' ? 14 : 16,
            color: '#666',
            fontWeight: 500,
            marginLeft: 8
          }}>
            {message}
          </div>
        )}
        <style jsx>{`
          @keyframes bounce {
            0%, 80%, 100% {
              transform: scale(0.8);
              opacity: 0.5;
            }
            40% {
              transform: scale(1);
              opacity: 1;
            }
          }
        `}</style>
      </div>
    )
  }

  // Skeleton variant
  return (
    <div style={{ padding: 16 }}>
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          style={{
            height: size === 'small' ? 16 : size === 'medium' ? 24 : 32,
            background: 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
            backgroundSize: '200% 100%',
            animation: 'shimmer 1.5s infinite',
            borderRadius: 4,
            marginBottom: 8
          }}
        />
      ))}
      <style jsx>{`
        @keyframes shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>
    </div>
  )
}

type LoadingOverlayProps = {
  show: boolean
  message?: string
}

export function LoadingOverlay({ show, message = 'Processing...' }: LoadingOverlayProps) {
  if (!show) return null

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 10000,
        backdropFilter: 'blur(4px)'
      }}
    >
      <div
        style={{
          background: 'white',
          borderRadius: 12,
          padding: 32,
          boxShadow: '0 8px 32px rgba(0,0,0,0.2)',
          minWidth: 300,
          textAlign: 'center'
        }}
      >
        <LoadingIndicator message={message} size="large" variant="spinner" />
      </div>
    </div>
  )
}
