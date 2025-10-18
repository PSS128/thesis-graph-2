'use client'

import React, { useState, useCallback } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import './pdf-styles.css'

// Configure worker - use dynamic import to avoid SSR issues
if (typeof window !== 'undefined') {
  pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`
}

type Props = {
  /** PDF file URL or File object */
  file: string | File
  /** Called when user selects text and clicks "Make Node" */
  onExtractNode?: (text: string, sourceRef: { docId?: string; page: number; span?: [number, number] }) => void
  /** Optional document ID for citation tracking */
  docId?: string
}

/**
 * PDF Viewer with text selection → node extraction
 * Users can highlight text and click a floating button to create a node
 */
export default function PDFViewer({ file, onExtractNode, docId }: Props) {
  const [numPages, setNumPages] = useState<number | null>(null)
  const [pageNumber, setPageNumber] = useState(1)
  const [selectedText, setSelectedText] = useState('')
  const [buttonPosition, setButtonPosition] = useState<{ x: number; y: number } | null>(null)

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages)
  }

  // Handle text selection
  const handleTextSelection = useCallback(() => {
    const selection = window.getSelection()
    const text = selection?.toString().trim()

    if (text && text.length > 5) {
      setSelectedText(text)

      // Position the button near the selection
      const range = selection?.getRangeAt(0)
      if (range) {
        const rect = range.getBoundingClientRect()
        setButtonPosition({
          x: rect.left + rect.width / 2,
          y: rect.top - 40
        })
      }
    } else {
      setSelectedText('')
      setButtonPosition(null)
    }
  }, [])

  const handleMakeNode = () => {
    if (selectedText && onExtractNode) {
      // Call the extraction handler with source metadata
      onExtractNode(selectedText, {
        docId,
        page: pageNumber,
        // Note: precise character spans would require more advanced PDF parsing
        // For now, we just track page number
      })

      // Clear selection
      setSelectedText('')
      setButtonPosition(null)
      window.getSelection()?.removeAllRanges()
    }
  }

  const handleDocumentClick = () => {
    // Hide button when clicking outside selection
    if (buttonPosition) {
      setTimeout(() => {
        const selection = window.getSelection()
        if (!selection || selection.toString().trim().length === 0) {
          setButtonPosition(null)
          setSelectedText('')
        }
      }, 100)
    }
  }

  return (
    <div
      style={{
        border: '1px solid #e5e5e5',
        borderRadius: 8,
        background: '#f9f9f9',
        padding: 16,
        position: 'relative'
      }}
      onMouseUp={handleTextSelection}
      onClick={handleDocumentClick}
    >
      {/* Page controls */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 12,
          padding: '8px 12px',
          background: '#fff',
          borderRadius: 6,
          border: '1px solid #ddd'
        }}
      >
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button
            onClick={() => setPageNumber((p) => Math.max(1, p - 1))}
            disabled={pageNumber <= 1}
            style={{
              padding: '4px 12px',
              border: '1px solid #333',
              borderRadius: 4,
              background: pageNumber <= 1 ? '#f5f5f5' : '#fff',
              cursor: pageNumber <= 1 ? 'not-allowed' : 'pointer'
            }}
          >
            ← Prev
          </button>
          <span style={{ fontSize: 14 }}>
            Page {pageNumber} of {numPages || '?'}
          </span>
          <button
            onClick={() => setPageNumber((p) => Math.min(numPages || p, p + 1))}
            disabled={!numPages || pageNumber >= numPages}
            style={{
              padding: '4px 12px',
              border: '1px solid #333',
              borderRadius: 4,
              background: !numPages || pageNumber >= numPages ? '#f5f5f5' : '#fff',
              cursor: !numPages || pageNumber >= numPages ? 'not-allowed' : 'pointer'
            }}
          >
            Next →
          </button>
        </div>
        <div style={{ fontSize: 12, color: '#666' }}>
          {docId ? `Document: ${docId}` : 'PDF Preview'}
        </div>
      </div>

      {/* PDF Document */}
      <div style={{ background: '#fff', border: '1px solid #ddd', borderRadius: 6, overflow: 'auto' }}>
        <Document
          file={file}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={
            <div style={{ padding: 40, textAlign: 'center', color: '#999' }}>Loading PDF...</div>
          }
          error={
            <div style={{ padding: 40, textAlign: 'center', color: '#c00' }}>
              Failed to load PDF. Please check the file.
            </div>
          }
        >
          <Page
            pageNumber={pageNumber}
            renderTextLayer={true}
            renderAnnotationLayer={true}
            width={800}
          />
        </Document>
      </div>

      {/* Floating "Make Node" button */}
      {buttonPosition && selectedText && (
        <div
          style={{
            position: 'fixed',
            left: buttonPosition.x,
            top: buttonPosition.y,
            transform: 'translateX(-50%)',
            zIndex: 1000,
            pointerEvents: 'auto'
          }}
        >
          <button
            onClick={handleMakeNode}
            onMouseDown={(e) => e.preventDefault()} // Prevent text deselection
            style={{
              padding: '8px 16px',
              background: '#1890ff',
              color: '#fff',
              border: 'none',
              borderRadius: 6,
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer',
              boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
              whiteSpace: 'nowrap'
            }}
          >
            Make Node
          </button>
        </div>
      )}
    </div>
  )
}
