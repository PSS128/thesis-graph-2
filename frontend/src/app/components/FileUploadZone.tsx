'use client'

import React, { useState, useCallback } from 'react'

type UploadedFile = {
  name: string
  file: File
  docId: string
  uploadedAt?: number
  size?: number
  pageCount?: number
}

type Props = {
  onUpload: (file: File) => Promise<void>
  uploadedFiles: UploadedFile[]
  onDelete?: (docId: string) => void
  busy?: boolean
}

export default function FileUploadZone({ onUpload, uploadedFiles, onDelete, busy = false }: Props) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<number | null>(null)

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setIsDragging(false)

      const files = Array.from(e.dataTransfer.files)
      const pdfOrTxt = files.filter((f) => f.name.toLowerCase().endsWith('.pdf') || f.name.toLowerCase().endsWith('.txt'))

      if (pdfOrTxt.length > 0 && !busy) {
        handleUpload(pdfOrTxt[0])
      }
    },
    [busy]
  )

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file && !busy) {
        handleUpload(file)
      }
      // Reset input so same file can be selected again
      e.target.value = ''
    },
    [busy]
  )

  const handleUpload = async (file: File) => {
    setUploadProgress(0)
    try {
      await onUpload(file)
      setUploadProgress(100)
      setTimeout(() => setUploadProgress(null), 1000)
    } catch (e) {
      setUploadProgress(null)
    }
  }

  const formatFileSize = (bytes?: number): string => {
    if (!bytes) return 'Unknown size'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const formatDate = (timestamp?: number): string => {
    if (!timestamp) return ''
    const date = new Date(timestamp)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      {/* Upload Zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        style={{
          border: `2px dashed ${isDragging ? '#1890ff' : '#d9d9d9'}`,
          borderRadius: 8,
          padding: 24,
          background: isDragging ? '#e6f7ff' : '#fafafa',
          textAlign: 'center',
          transition: 'all 0.2s ease',
          cursor: busy ? 'not-allowed' : 'pointer',
          opacity: busy ? 0.6 : 1
        }}
      >
        <div style={{ fontSize: 40, marginBottom: 8 }}>📄</div>
        <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4, color: '#262626' }}>
          {isDragging ? 'Drop file here' : 'Drag & drop PDF or TXT file'}
        </div>
        <div style={{ fontSize: 12, color: '#8c8c8c', marginBottom: 12 }}>
          or click to browse
        </div>
        <label
          style={{
            display: 'inline-block',
            padding: '8px 16px',
            background: busy ? '#d9d9d9' : '#1890ff',
            color: '#fff',
            borderRadius: 6,
            fontSize: 13,
            fontWeight: 600,
            cursor: busy ? 'not-allowed' : 'pointer',
            transition: 'background 0.2s'
          }}
        >
          {busy ? 'Uploading...' : 'Choose File'}
          <input
            type="file"
            accept=".pdf,.txt"
            onChange={handleFileInput}
            disabled={busy}
            style={{ display: 'none' }}
          />
        </label>

        {/* Upload Progress */}
        {uploadProgress !== null && (
          <div style={{ marginTop: 16 }}>
            <div
              style={{
                width: '100%',
                height: 6,
                background: '#f0f0f0',
                borderRadius: 3,
                overflow: 'hidden'
              }}
            >
              <div
                style={{
                  width: `${uploadProgress}%`,
                  height: '100%',
                  background: '#52c41a',
                  transition: 'width 0.3s ease'
                }}
              />
            </div>
            <div style={{ fontSize: 11, color: '#8c8c8c', marginTop: 4 }}>
              {uploadProgress === 100 ? 'Upload complete!' : `Uploading... ${uploadProgress}%`}
            </div>
          </div>
        )}
      </div>

      {/* Uploaded Files List */}
      {uploadedFiles.length > 0 && (
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: '#262626' }}>
            Uploaded Files ({uploadedFiles.length})
          </div>
          <div style={{ display: 'grid', gap: 8 }}>
            {uploadedFiles.map((f, idx) => (
              <div
                key={f.docId}
                style={{
                  border: '1px solid #e5e5e5',
                  borderRadius: 6,
                  padding: 12,
                  background: '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  transition: 'border-color 0.2s',
                  cursor: 'default'
                }}
                onMouseEnter={(e) => (e.currentTarget.style.borderColor = '#1890ff')}
                onMouseLeave={(e) => (e.currentTarget.style.borderColor = '#e5e5e5')}
              >
                {/* File Icon */}
                <div
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: 6,
                    background: '#fff1f0',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 18,
                    flexShrink: 0
                  }}
                >
                  📄
                </div>

                {/* File Info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      fontSize: 13,
                      fontWeight: 600,
                      color: '#262626',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    {f.name}
                  </div>
                  <div style={{ fontSize: 11, color: '#8c8c8c', marginTop: 2 }}>
                    {formatFileSize(f.size || f.file.size)}
                    {f.uploadedAt && ` • ${formatDate(f.uploadedAt)}`}
                    {f.pageCount && ` • ${f.pageCount} pages`}
                  </div>
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                  <button
                    onClick={() => {
                      const url = URL.createObjectURL(f.file)
                      const a = document.createElement('a')
                      a.href = url
                      a.download = f.name
                      a.click()
                      URL.revokeObjectURL(url)
                    }}
                    style={{
                      padding: '4px 8px',
                      border: '1px solid #d9d9d9',
                      background: '#fff',
                      borderRadius: 4,
                      fontSize: 11,
                      cursor: 'pointer',
                      color: '#595959'
                    }}
                    title="Download file"
                  >
                    ⬇
                  </button>
                  {onDelete && (
                    <button
                      onClick={() => {
                        if (confirm(`Delete "${f.name}"?`)) {
                          onDelete(f.docId)
                        }
                      }}
                      style={{
                        padding: '4px 8px',
                        border: '1px solid #ffccc7',
                        background: '#fff',
                        borderRadius: 4,
                        fontSize: 11,
                        cursor: 'pointer',
                        color: '#ff4d4f'
                      }}
                      title="Delete file"
                    >
                      🗑
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
