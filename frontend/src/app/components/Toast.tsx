'use client'

import React, { useEffect } from 'react'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export type ToastMessage = {
  id: string
  type: ToastType
  message: string
  duration?: number
}

type Props = {
  toasts: ToastMessage[]
  onRemove: (id: string) => void
}

export default function Toast({ toasts, onRemove }: Props) {
  useEffect(() => {
    // Auto-remove toasts after their duration
    toasts.forEach((toast) => {
      const duration = toast.duration || 4000
      const timer = setTimeout(() => {
        onRemove(toast.id)
      }, duration)

      return () => clearTimeout(timer)
    })
  }, [toasts, onRemove])

  const getToastStyles = (type: ToastType) => {
    switch (type) {
      case 'success':
        return {
          bg: '#f6ffed',
          border: '#52c41a',
          text: '#389e0d',
          icon: '✓'
        }
      case 'error':
        return {
          bg: '#fff2f0',
          border: '#ff4d4f',
          text: '#cf1322',
          icon: '✕'
        }
      case 'warning':
        return {
          bg: '#fffbe6',
          border: '#faad14',
          text: '#d46b08',
          icon: '⚠'
        }
      case 'info':
        return {
          bg: '#e6f7ff',
          border: '#1890ff',
          text: '#0050b3',
          icon: 'ℹ'
        }
    }
  }

  if (toasts.length === 0) return null

  return (
    <div
      style={{
        position: 'fixed',
        top: 20,
        right: 20,
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
        maxWidth: 400
      }}
    >
      {toasts.map((toast) => {
        const styles = getToastStyles(toast.type)
        return (
          <div
            key={toast.id}
            style={{
              background: styles.bg,
              border: `2px solid ${styles.border}`,
              borderRadius: 8,
              padding: '12px 16px',
              boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              minWidth: 300,
              animation: 'slideIn 0.3s ease-out',
              position: 'relative'
            }}
          >
            {/* Icon */}
            <div
              style={{
                width: 24,
                height: 24,
                borderRadius: '50%',
                background: styles.border,
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 14,
                fontWeight: 'bold',
                flexShrink: 0
              }}
            >
              {styles.icon}
            </div>

            {/* Message */}
            <div style={{ flex: 1, fontSize: 14, color: styles.text, fontWeight: 500 }}>
              {toast.message}
            </div>

            {/* Close button */}
            <button
              onClick={() => onRemove(toast.id)}
              style={{
                background: 'transparent',
                border: 'none',
                color: styles.text,
                cursor: 'pointer',
                fontSize: 18,
                padding: 0,
                width: 20,
                height: 20,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                opacity: 0.6,
                flexShrink: 0
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = '1')}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = '0.6')}
            >
              ×
            </button>
          </div>
        )
      })}

      {/* Animation styles */}
      <style jsx global>{`
        @keyframes slideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  )
}
