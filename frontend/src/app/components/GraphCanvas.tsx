'use client'

import React, { useEffect, useMemo, useRef, useState } from 'react'

type NodeCitation = {
  doc: string
  span: [number, number]
}

type NodeT = {
  id: string
  // New schema fields
  name?: string
  kind?: 'THESIS' | 'VARIABLE' | 'ASSUMPTION'
  definition?: string
  synonyms?: string[]
  measurement_ideas?: string[]
  citations?: NodeCitation[]
  // Legacy fields (for backward compatibility)
  text?: string
  type?: 'THESIS' | 'CLAIM'
  x?: number
  y?: number
}

type EdgeCitation = {
  doc: string
  span: [number, number]
  support: 'supports' | 'contradicts'
  strength: number
}

type EdgeT = {
  from_id: string
  to_id: string
  // New schema fields
  type?: 'CAUSES' | 'MODERATES' | 'MEDIATES' | 'CONTRADICTS'
  status?: 'PROPOSED' | 'ACCEPTED' | 'REJECTED'
  citations?: EdgeCitation[]
  mechanisms?: string[]
  // Legacy fields (for backward compatibility)
  relation?: 'SUPPORTS' | 'CONTRADICTS'
  rationale?: string
  confidence?: number
}

type Warning = {
  node_or_edge_id: string
  label: string
  fix_suggestion: string
}

type Props = {
  /** Nodes to render */
  nodes: NodeT[]
  /** Edges to render */
  edges: EdgeT[]

  /** Called when node positions change after drag */
  onNodesPosChange?: (pos: { id: string; x: number; y: number }[]) => void

  /** If true, clicking two nodes creates an edge */
  edgeMode?: boolean

  /** Called when an edge is requested by clicking two nodes in edgeMode */
  onCreateEdge?: (from_id: string, to_id: string) => void

  /** Selected node ids, used to render selection outline */
  selectedIds?: Record<string, boolean>

  /** Toggle selection state of a node */
  onToggleSelect?: (id: string) => void

  /** Critique warnings to display inline */
  warnings?: Warning[]

  /** Optional width/height; otherwise fills parent */
  width?: number | string
  height?: number | string
}

/**
 * Simple SVG-based graph canvas with draggable nodes and arrow edges.
 * No external lib required; coordinates live in component state, then bubbled up.
 */
export default function GraphCanvas({
  nodes,
  edges,
  onNodesPosChange,
  edgeMode = false,
  onCreateEdge,
  selectedIds = {},
  onToggleSelect,
  warnings = [],
  width = '100%',
  height = 520
}: Props) {
  // --- Internal positioning state (derived from nodes, preserved across updates)
  const [pos, setPos] = useState<Record<string, { x: number; y: number }>>({})
  const [pendingFrom, setPendingFrom] = useState<string | null>(null)

  // Drag refs
  const dragId = useRef<string | null>(null)
  const dragOffset = useRef<{ dx: number; dy: number }>({ dx: 0, dy: 0 })
  const dragStart = useRef<{ x: number; y: number } | null>(null)
  const hasDragged = useRef<boolean>(false)
  const svgRef = useRef<SVGSVGElement | null>(null)

  // Edge drawing state
  const [edgeDragFrom, setEdgeDragFrom] = useState<string | null>(null)
  const [edgeDragPos, setEdgeDragPos] = useState<{ x: number; y: number } | null>(null)

  // Lasso selection state
  const [lassoStart, setLassoStart] = useState<{ x: number; y: number } | null>(null)
  const [lassoEnd, setLassoEnd] = useState<{ x: number; y: number } | null>(null)

  // Tooltip state
  const [hoveredNode, setHoveredNode] = useState<{ node: NodeT; x: number; y: number } | null>(null)
  const hoverTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Zoom and pan state
  const [zoom, setZoom] = useState<number>(1)
  const [panX, setPanX] = useState<number>(0)
  const [panY, setPanY] = useState<number>(0)
  const isPanning = useRef<boolean>(false)
  const panStart = useRef<{ x: number; y: number } | null>(null)

  // Initialize positions when nodes change (keep old positions if present)
  useEffect(() => {
    setPos((prev) => {
      const next = { ...prev }
      // Center defaults for nodes without a position
      let idx = 0
      nodes.forEach((n) => {
        if (!next[n.id]) {
          next[n.id] = {
            x: n.x ?? 160 + (idx % 5) * 180,
            y: n.y ?? 120 + Math.floor(idx / 5) * 140
          }
          idx++
        } else {
          // Sync if incoming props carry explicit x/y (e.g., load project)
          if (typeof n.x === 'number' && typeof n.y === 'number') {
            next[n.id] = { x: n.x, y: n.y }
          }
        }
      })
      // Remove positions for nodes that no longer exist
      Object.keys(next).forEach((id) => {
        if (!nodes.find((n) => n.id === id)) delete next[id]
      })
      return next
    })
  }, [nodes])

  // Throttled bubble-up of new positions (after drag end)
  const commitPositions = (ids?: string[]) => {
    if (!onNodesPosChange) return
    const payload = (ids && ids.length ? ids : Object.keys(pos)).map((id) => ({
      id,
      x: pos[id].x,
      y: pos[id].y
    }))
    onNodesPosChange(payload)
  }

  // Mouse helpers
  const ptFromEvent = (e: React.MouseEvent) => {
    const svg = svgRef.current
    if (!svg) return { x: e.clientX, y: e.clientY }
    const pt = svg.createSVGPoint()
    pt.x = e.clientX
    pt.y = e.clientY
    const ctm = svg.getScreenCTM()
    if (!ctm) return { x: e.clientX, y: e.clientY }
    const p = pt.matrixTransform(ctm.inverse())
    return { x: p.x, y: p.y }
  }

  const onNodeMouseDown = (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    const p = ptFromEvent(e)
    const cur = pos[id] || { x: 0, y: 0 }

    // edge creation mode - support both click and drag
    if (edgeMode) {
      // Check if shift key is held for drag-to-connect
      if (e.shiftKey) {
        setEdgeDragFrom(id)
        setEdgeDragPos(cur)
        return
      }

      // Otherwise use click mode
      if (pendingFrom === null) {
        setPendingFrom(id)
      } else if (pendingFrom !== id) {
        if (onCreateEdge) {
          onCreateEdge(pendingFrom, id)
        }
        setPendingFrom(null)
      }
      return
    }

    dragId.current = id
    dragOffset.current = { dx: p.x - cur.x, dy: p.y - cur.y }
    dragStart.current = p
    hasDragged.current = false
  }

  const onSvgMouseMove = (e: React.MouseEvent) => {
    // Handle canvas panning
    if (isPanning.current && panStart.current) {
      setPanX(e.clientX - panStart.current.x)
      setPanY(e.clientY - panStart.current.y)
      return
    }

    const p = ptFromEvent(e)

    // Handle lasso selection
    if (lassoStart) {
      setLassoEnd(p)
      return
    }

    // Handle edge drag drawing
    if (edgeDragFrom) {
      setEdgeDragPos(p)
      return
    }

    // Handle node drag
    if (!dragId.current) return
    const id = dragId.current
    const { dx, dy } = dragOffset.current

    // Only consider it a drag if moved more than 5 pixels
    if (dragStart.current) {
      const distance = Math.sqrt(
        Math.pow(p.x - dragStart.current.x, 2) + Math.pow(p.y - dragStart.current.y, 2)
      )
      if (distance > 5) {
        hasDragged.current = true
      }
    }

    setPos((prev) => ({
      ...prev,
      [id!]: { x: p.x - dx, y: p.y - dy }
    }))
  }

  const onSvgMouseDown = (e: React.MouseEvent) => {
    // If middle mouse button or shift key, start panning
    if (e.button === 1 || e.shiftKey) {
      e.preventDefault()
      isPanning.current = true
      panStart.current = { x: e.clientX - panX, y: e.clientY - panY }
      return
    }

    // Only start lasso if clicking on background (not edge mode)
    if (!edgeMode && e.target === e.currentTarget) {
      const p = ptFromEvent(e)
      setLassoStart(p)
      setLassoEnd(p)
    }
  }

  const onSvgMouseUp = () => {
    // Stop panning
    if (isPanning.current) {
      isPanning.current = false
      panStart.current = null
      return
    }

    // Complete lasso selection
    if (lassoStart && lassoEnd && onToggleSelect) {
      const minX = Math.min(lassoStart.x, lassoEnd.x)
      const maxX = Math.max(lassoStart.x, lassoEnd.x)
      const minY = Math.min(lassoStart.y, lassoEnd.y)
      const maxY = Math.max(lassoStart.y, lassoEnd.y)

      // Select all nodes within the lasso bounds
      renderedNodes.forEach((n) => {
        if (n.x >= minX && n.x <= maxX && n.y >= minY && n.y <= maxY) {
          onToggleSelect(n.id)
        }
      })

      setLassoStart(null)
      setLassoEnd(null)
      return
    }

    // Complete edge drag if active
    if (edgeDragFrom) {
      setEdgeDragFrom(null)
      setEdgeDragPos(null)
      return
    }

    if (dragId.current) {
      const id = dragId.current
      dragId.current = null
      commitPositions([id])
    }
  }

  const onNodeMouseUp = (e: React.MouseEvent, id: string) => {
    e.stopPropagation()

    // If we're dragging an edge, complete the connection
    if (edgeDragFrom && edgeDragFrom !== id) {
      if (onCreateEdge) {
        onCreateEdge(edgeDragFrom, id)
      }
      setEdgeDragFrom(null)
      setEdgeDragPos(null)
      return
    }

    // If we were dragging a node, commit the position and clear drag state
    if (dragId.current) {
      const draggedId = dragId.current
      dragId.current = null
      if (hasDragged.current) {
        commitPositions([draggedId])
      }
    }
  }

  const onSvgClick = () => {
    // Clicking background cancels edge-mode selection or edge drag
    if (edgeMode && pendingFrom) setPendingFrom(null)
    if (edgeDragFrom) {
      setEdgeDragFrom(null)
      setEdgeDragPos(null)
    }
  }

  // Derived arrays for rendering
  const renderedNodes = useMemo(
    () =>
      nodes.map((n) => ({
        ...n,
        x: pos[n.id]?.x ?? 0,
        y: pos[n.id]?.y ?? 0
      })),
    [nodes, pos]
  )

  // Helper functions for backward compatibility
  const getNodeText = (n: NodeT): string => n.name || n.text || 'Untitled'
  const getNodeType = (n: NodeT): string => n.kind || n.type || 'VARIABLE'
  const getEdgeStatus = (e: EdgeT): string => e.status || 'ACCEPTED'

  // Warning helpers
  const getWarningEmoji = (label: string): string => {
    const lower = label.toLowerCase()
    if (lower.includes('confound')) return '🔀'
    if (lower.includes('collider')) return '⚠️'
    if (lower.includes('mediator')) return '🚫'
    if (lower.includes('evidence')) return '📚'
    if (lower.includes('cycle')) return '🔄'
    return '⚠️'
  }

  // Create maps for quick warning lookup
  const nodeWarnings = useMemo(() => {
    const map: Record<string, Warning[]> = {}
    warnings.forEach((w) => {
      if (w.node_or_edge_id.startsWith('n') || w.node_or_edge_id.startsWith('N')) {
        if (!map[w.node_or_edge_id]) map[w.node_or_edge_id] = []
        map[w.node_or_edge_id].push(w)
      }
    })
    return map
  }, [warnings])

  const edgeWarnings = useMemo(() => {
    const map: Record<string, Warning[]> = {}
    warnings.forEach((w) => {
      if (w.node_or_edge_id.startsWith('E') || w.node_or_edge_id.startsWith('e')) {
        if (!map[w.node_or_edge_id]) map[w.node_or_edge_id] = []
        map[w.node_or_edge_id].push(w)
      }
    })
    return map
  }, [warnings])

  // Render helpers - Node sizing and colors
  const NODE_MIN_WIDTH = 140
  const NODE_MIN_HEIGHT = 60
  const NODE_PADDING = 12

  // Enhanced color themes for node types
  const getNodeTheme = (type: string): { bg: string; border: string; gradient: string; text: string } => {
    switch (type) {
      case 'THESIS':
        return {
          bg: '#fff7e6',
          border: '#fa8c16',
          gradient: 'linear-gradient(135deg, #fff7e6 0%, #ffe7ba 100%)',
          text: '#ad4e00'
        }
      case 'VARIABLE':
        return {
          bg: '#e6f7ff',
          border: '#1890ff',
          gradient: 'linear-gradient(135deg, #e6f7ff 0%, #bae7ff 100%)',
          text: '#0050b3'
        }
      case 'ASSUMPTION':
        return {
          bg: '#f9f0ff',
          border: '#722ed1',
          gradient: 'linear-gradient(135deg, #f9f0ff 0%, #efdbff 100%)',
          text: '#531dab'
        }
      default:
        return {
          bg: '#f6ffed',
          border: '#52c41a',
          gradient: 'linear-gradient(135deg, #f6ffed 0%, #d9f7be 100%)',
          text: '#389e0d'
        }
    }
  }

  // Helper to calculate node dimensions based on text
  const getNodeDimensions = (text: string): { width: number; height: number } => {
    // Rough estimation: ~7 pixels per character, max 20 chars per line
    const maxCharsPerLine = 18
    const lines = Math.ceil(text.length / maxCharsPerLine)
    const lineHeight = 16

    const width = Math.max(NODE_MIN_WIDTH, Math.min(text.length * 7, maxCharsPerLine * 7) + NODE_PADDING * 2)
    const height = Math.max(NODE_MIN_HEIGHT, lines * lineHeight + NODE_PADDING * 2 + 20) // +20 for type label

    return { width, height }
  }

  // Helper to wrap text into multiple lines
  const wrapText = (text: string, maxCharsPerLine: number = 18): string[] => {
    const words = text.split(' ')
    const lines: string[] = []
    let currentLine = ''

    words.forEach(word => {
      if ((currentLine + word).length <= maxCharsPerLine) {
        currentLine += (currentLine ? ' ' : '') + word
      } else {
        if (currentLine) lines.push(currentLine)
        currentLine = word
      }
    })
    if (currentLine) lines.push(currentLine)

    return lines
  }

  // Color mapping for edge types
  const getEdgeColor = (e: EdgeT): string => {
    const edgeType = e.type || e.relation
    switch (edgeType) {
      case 'CAUSES': return '#1890ff'        // Blue
      case 'MODERATES': return '#722ed1'     // Purple
      case 'MEDIATES': return '#13c2c2'      // Teal
      case 'CONTRADICTS': return '#ff4d4f'   // Red
      case 'SUPPORTS': return '#52c41a'      // Green (legacy)
      default: return '#1890ff'              // Default blue
    }
  }

  // Get edge type label
  const getEdgeTypeLabel = (e: EdgeT): string => {
    const edgeType = e.type || e.relation
    if (!edgeType) return 'causes'
    return edgeType.toLowerCase()
  }

  // Arrow marker ids for different edge types
  const markerIdCauses = 'arrow-causes'
  const markerIdModerates = 'arrow-moderates'
  const markerIdMediates = 'arrow-mediates'
  const markerIdContradicts = 'arrow-contradicts'
  const markerIdSupport = 'arrow-support'
  const markerIdContr = 'arrow-contr'

  return (
    <div
      style={{
        width,
        height,
        border: '1px solid #e5e5e5',
        borderRadius: 10,
        background: '#fff',
        boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
        position: 'relative'
      }}
    >
      {/* Instructions panel at top */}
      <div style={{
        position: 'absolute',
        top: 12,
        left: 12,
        background: 'rgba(255, 255, 255, 0.95)',
        padding: '8px 12px',
        borderRadius: 6,
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        fontSize: 11,
        color: '#595959',
        zIndex: 10,
        lineHeight: '1.6',
        border: '1px solid #e8e8e8'
      }}>
        <div style={{ fontWeight: 600, marginBottom: 4, color: '#262626' }}>Canvas Controls:</div>
        <div><strong>Click</strong> node to select/deselect</div>
        <div><strong>Drag</strong> node to move it</div>
        <div><strong>Shift + Drag</strong> canvas to pan</div>
        <div><strong>Zoom controls</strong> in bottom-right corner</div>
      </div>

      <svg
        ref={svgRef}
        width="100%"
        height="100%"
        onMouseDown={onSvgMouseDown}
        onMouseMove={onSvgMouseMove}
        onMouseUp={onSvgMouseUp}
        onClick={onSvgClick}
        style={{
          userSelect: 'none',
          cursor: isPanning.current ? 'grabbing' : dragId.current ? 'grabbing' : lassoStart ? 'crosshair' : 'default'
        }}
      >
        {/* defs for arrowheads */}
        <defs>
          {/* New edge type markers */}
          <marker id={markerIdCauses} markerWidth="10" markerHeight="10" refX="10" refY="5" orient="auto">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#1890ff" />
          </marker>
          <marker id={markerIdModerates} markerWidth="10" markerHeight="10" refX="10" refY="5" orient="auto">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#722ed1" />
          </marker>
          <marker id={markerIdMediates} markerWidth="10" markerHeight="10" refX="10" refY="5" orient="auto">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#13c2c2" />
          </marker>
          <marker id={markerIdContradicts} markerWidth="10" markerHeight="10" refX="10" refY="5" orient="auto">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#ff4d4f" />
          </marker>
          {/* Legacy markers */}
          <marker id={markerIdSupport} markerWidth="10" markerHeight="10" refX="10" refY="5" orient="auto">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#52c41a" />
          </marker>
          <marker id={markerIdContr} markerWidth="10" markerHeight="10" refX="10" refY="5" orient="auto">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#c0392b" />
          </marker>
        </defs>

        {/* Main group with zoom and pan transform */}
        <g transform={`translate(${panX}, ${panY}) scale(${zoom})`}>
        {/* edges */}
        {edges.map((e, idx) => {
          const from = renderedNodes.find((n) => n.id === e.from_id)
          const to = renderedNodes.find((n) => n.id === e.to_id)
          if (!from || !to) return null

          const edgeType = e.type || e.relation || 'CAUSES'
          const status = getEdgeStatus(e)
          const stroke = getEdgeColor(e)
          const typeLabel = getEdgeTypeLabel(e)

          // Select appropriate marker based on type
          let markerUrl = `url(#${markerIdCauses})`
          if (edgeType === 'MODERATES') markerUrl = `url(#${markerIdModerates})`
          else if (edgeType === 'MEDIATES') markerUrl = `url(#${markerIdMediates})`
          else if (edgeType === 'CONTRADICTS') markerUrl = `url(#${markerIdContradicts})`
          else if (edgeType === 'SUPPORTS') markerUrl = `url(#${markerIdSupport})`

          // Proposed edges are dashed, accepted are solid
          const dashArray = status === 'PROPOSED' ? '5,5' : '0'
          const opacity = status === 'PROPOSED' ? 0.6 : 0.9

          const edgeId = `E${idx}`
          const hasWarnings = edgeWarnings[edgeId] || edgeWarnings[`e${idx}`]
          const citationCount = e.citations?.length || 0

          const midX = (from.x + to.x) / 2
          const midY = (from.y + to.y) / 2

          return (
            <g key={`E-${idx}`}>
              <line
                x1={from.x}
                y1={from.y}
                x2={to.x}
                y2={to.y}
                stroke={stroke}
                strokeWidth={2.5}
                strokeDasharray={dashArray}
                markerEnd={markerUrl}
                opacity={opacity}
              />
              {/* relation label at mid-point */}
              <text
                x={midX}
                y={midY - 6}
                fill={stroke}
                fontSize={11}
                fontWeight={600}
                textAnchor="middle"
                style={{ pointerEvents: 'none' }}
              >
                {typeLabel}
              </text>

              {/* Citation count badge */}
              {citationCount > 0 && (
                <g>
                  <title>{citationCount} citation{citationCount > 1 ? 's' : ''}</title>
                  <circle
                    cx={midX + 30}
                    cy={midY - 6}
                    r={9}
                    fill="#52c41a"
                    stroke="#fff"
                    strokeWidth={1.5}
                  />
                  <text
                    x={midX + 30}
                    y={midY - 2}
                    fill="#fff"
                    fontSize={10}
                    fontWeight={700}
                    textAnchor="middle"
                    style={{ pointerEvents: 'none', userSelect: 'none' }}
                  >
                    {citationCount}
                  </text>
                </g>
              )}

              {/* Warning badge */}
              {hasWarnings && (
                <g>
                  <title>
                    {hasWarnings.map((w) => `${w.label}: ${w.fix_suggestion}`).join('\n')}
                  </title>
                  <circle
                    cx={midX}
                    cy={midY + 12}
                    r={10}
                    fill="#ff4d4f"
                    stroke="#fff"
                    strokeWidth={2}
                  />
                  <text
                    x={midX}
                    y={midY + 16}
                    fill="#fff"
                    fontSize={12}
                    textAnchor="middle"
                    style={{ pointerEvents: 'none', userSelect: 'none' }}
                  >
                    {getWarningEmoji(hasWarnings[0].label)}
                  </text>
                </g>
              )}
            </g>
          )
        })}

        {/* temporary edge during drag */}
        {edgeDragFrom && edgeDragPos && (() => {
          const fromNode = renderedNodes.find((n) => n.id === edgeDragFrom)
          if (!fromNode) return null
          return (
            <line
              x1={fromNode.x}
              y1={fromNode.y}
              x2={edgeDragPos.x}
              y2={edgeDragPos.y}
              stroke="#1890ff"
              strokeWidth={2}
              strokeDasharray="5,5"
              opacity={0.6}
              style={{ pointerEvents: 'none' }}
            />
          )
        })()}

        {/* lasso selection rectangle */}
        {lassoStart && lassoEnd && (() => {
          const x = Math.min(lassoStart.x, lassoEnd.x)
          const y = Math.min(lassoStart.y, lassoEnd.y)
          const width = Math.abs(lassoEnd.x - lassoStart.x)
          const height = Math.abs(lassoEnd.y - lassoStart.y)
          return (
            <rect
              x={x}
              y={y}
              width={width}
              height={height}
              fill="rgba(24, 144, 255, 0.1)"
              stroke="#1890ff"
              strokeWidth={1}
              strokeDasharray="4,4"
              style={{ pointerEvents: 'none' }}
            />
          )
        })()}

        {/* nodes */}
        {renderedNodes.map((n) => {
          const sel = !!selectedIds[n.id]
          const isPending = edgeMode && pendingFrom === n.id
          const nodeType = getNodeType(n)
          const theme = getNodeTheme(nodeType)
          const hasWarnings = nodeWarnings[n.id]
          const nodeText = getNodeText(n)
          const dimensions = getNodeDimensions(nodeText)
          const textLines = wrapText(nodeText)

          const handleMouseEnter = () => {
            // Clear any existing timeout
            if (hoverTimeoutRef.current) {
              clearTimeout(hoverTimeoutRef.current)
            }
            // Set tooltip after short delay
            hoverTimeoutRef.current = setTimeout(() => {
              if (n.definition || n.synonyms?.length || n.citations?.length) {
                setHoveredNode({ node: n, x: n.x, y: n.y })
              }
            }, 300) // 300ms delay before showing tooltip
          }

          const handleMouseLeave = () => {
            if (hoverTimeoutRef.current) {
              clearTimeout(hoverTimeoutRef.current)
            }
            setHoveredNode(null)
          }

          return (
            <g
              key={n.id}
              onMouseDown={(e) => onNodeMouseDown(e, n.id)}
              onMouseUp={(e) => onNodeMouseUp(e, n.id)}
              onMouseEnter={handleMouseEnter}
              onMouseLeave={handleMouseLeave}
              onClick={(e) => {
                e.stopPropagation()
                // Only toggle selection on click, not after drag or edge operations
                // Allow deselection even in edge mode if not creating an edge
                if (onToggleSelect && !hasDragged.current && !edgeDragFrom && !pendingFrom) {
                  onToggleSelect(n.id)
                }
              }}
              style={{ cursor: edgeMode ? 'crosshair' : (sel ? 'pointer' : 'grab') }}
            >
              {/* Tooltip for warnings */}
              {hasWarnings && (
                <title>
                  {hasWarnings.map((w) => `${w.label}: ${w.fix_suggestion}`).join('\n')}
                </title>
              )}

              {/* Drop shadow filter */}
              <defs>
                <filter id={`shadow-${n.id}`} x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur in="SourceAlpha" stdDeviation="2" />
                  <feOffset dx="0" dy="2" result="offsetblur" />
                  <feComponentTransfer>
                    <feFuncA type="linear" slope="0.2" />
                  </feComponentTransfer>
                  <feMerge>
                    <feMergeNode />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
                <linearGradient id={`grad-${n.id}`} x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style={{ stopColor: theme.bg, stopOpacity: 1 }} />
                  <stop offset="100%" style={{ stopColor: theme.border, stopOpacity: 0.15 }} />
                </linearGradient>
              </defs>

              {/* Main node rectangle with rounded corners */}
              <rect
                x={n.x - dimensions.width / 2}
                y={n.y - dimensions.height / 2}
                width={dimensions.width}
                height={dimensions.height}
                rx={12}
                ry={12}
                fill={`url(#grad-${n.id})`}
                stroke={theme.border}
                strokeWidth={sel ? 3 : 2}
                opacity={isPending ? 0.8 : 1}
                filter={`url(#shadow-${n.id})`}
              />

              {/* Type label badge at top */}
              <rect
                x={n.x - dimensions.width / 2 + 8}
                y={n.y - dimensions.height / 2 + 8}
                width={nodeType.length * 6 + 12}
                height={18}
                rx={4}
                ry={4}
                fill={theme.border}
                opacity={0.2}
              />
              <text
                x={n.x - dimensions.width / 2 + 14}
                y={n.y - dimensions.height / 2 + 20}
                fontSize={10}
                fontWeight="600"
                fill={theme.text}
                style={{ pointerEvents: 'none' }}
              >
                {nodeType}
              </text>

              {/* Node text - wrapped into multiple lines */}
              {textLines.map((line, i) => (
                <text
                  key={i}
                  x={n.x}
                  y={n.y - dimensions.height / 2 + 38 + i * 16}
                  textAnchor="middle"
                  fontSize={13}
                  fontWeight="500"
                  fill={theme.text}
                  style={{ pointerEvents: 'none' }}
                >
                  {line}
                </text>
              ))}

              {/* Selection indicator */}
              {sel && (
                <rect
                  x={n.x - dimensions.width / 2}
                  y={n.y - dimensions.height / 2}
                  width={dimensions.width}
                  height={dimensions.height}
                  rx={12}
                  ry={12}
                  fill="none"
                  stroke={theme.border}
                  strokeWidth={2}
                  strokeDasharray="5,5"
                  opacity={0.6}
                  style={{ pointerEvents: 'none' }}
                />
              )}

              {/* Warning badge */}
              {hasWarnings && (
                <g>
                  <circle
                    cx={n.x + dimensions.width / 2 - 12}
                    cy={n.y - dimensions.height / 2 + 12}
                    r={10}
                    fill="#ff4d4f"
                    stroke="#fff"
                    strokeWidth={2}
                  />
                  <text
                    x={n.x + dimensions.width / 2 - 12}
                    y={n.y - dimensions.height / 2 + 17}
                    fill="#fff"
                    fontSize={11}
                    textAnchor="middle"
                    style={{ pointerEvents: 'none', userSelect: 'none' }}
                  >
                    {getWarningEmoji(hasWarnings[0].label)}
                  </text>
                </g>
              )}
            </g>
          )
        })}
        </g>
      </svg>

      {/* Zoom controls */}
      <div style={{
        position: 'absolute',
        bottom: 16,
        right: 16,
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        background: 'white',
        padding: '8px',
        borderRadius: 8,
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        zIndex: 10
      }}>
        <button
          onClick={() => setZoom(z => Math.min(z * 1.2, 3))}
          title="Zoom In"
          style={{
            padding: '6px 12px',
            border: '1px solid #d9d9d9',
            borderRadius: 4,
            background: 'white',
            cursor: 'pointer',
            fontSize: 16,
            fontWeight: 'bold'
          }}
        >
          +
        </button>
        <button
          onClick={() => setZoom(z => Math.max(z / 1.2, 0.1))}
          title="Zoom Out"
          style={{
            padding: '6px 12px',
            border: '1px solid #d9d9d9',
            borderRadius: 4,
            background: 'white',
            cursor: 'pointer',
            fontSize: 16,
            fontWeight: 'bold'
          }}
        >
          −
        </button>
        <button
          onClick={() => { setZoom(1); setPanX(0); setPanY(0) }}
          title="Reset View"
          style={{
            padding: '6px 12px',
            border: '1px solid #d9d9d9',
            borderRadius: 4,
            background: 'white',
            cursor: 'pointer',
            fontSize: 12
          }}
        >
          ↺
        </button>
        <div style={{
          fontSize: 11,
          color: '#666',
          textAlign: 'center',
          padding: '4px 0',
          borderTop: '1px solid #e8e8e8',
          marginTop: 4
        }}>
          {Math.round(zoom * 100)}%
        </div>
      </div>

      {/* Tooltip - rendered outside SVG as HTML */}
      {hoveredNode && (
        <div
          style={{
            position: 'absolute',
            left: hoveredNode.x + 30,
            top: hoveredNode.y - 20,
            background: '#fff',
            border: '2px solid #1890ff',
            borderRadius: 8,
            padding: 12,
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            maxWidth: 300,
            zIndex: 1000,
            pointerEvents: 'none',
            fontSize: 12
          }}
        >
          <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 6, color: '#1890ff' }}>
            {getNodeText(hoveredNode.node)}
          </div>

          {hoveredNode.node.definition && (
            <div style={{ marginBottom: 8, color: '#262626', lineHeight: '1.4' }}>
              {hoveredNode.node.definition}
            </div>
          )}

          {hoveredNode.node.synonyms && hoveredNode.node.synonyms.length > 0 && (
            <div style={{ marginBottom: 6 }}>
              <span style={{ fontWeight: 600, color: '#595959' }}>Synonyms: </span>
              <span style={{ color: '#8c8c8c', fontSize: 11 }}>
                {hoveredNode.node.synonyms.join(', ')}
              </span>
            </div>
          )}

          {hoveredNode.node.citations && hoveredNode.node.citations.length > 0 && (
            <div style={{ marginBottom: 4 }}>
              <span style={{ fontWeight: 600, color: '#595959' }}>Citations: </span>
              <span style={{ color: '#52c41a', fontSize: 11, fontWeight: 600 }}>
                {hoveredNode.node.citations.length}
              </span>
            </div>
          )}

          {hoveredNode.node.measurement_ideas && hoveredNode.node.measurement_ideas.length > 0 && (
            <div style={{ marginTop: 6, paddingTop: 6, borderTop: '1px solid #f0f0f0' }}>
              <span style={{ fontWeight: 600, color: '#595959', fontSize: 11 }}>
                Measurement ideas: {hoveredNode.node.measurement_ideas.length}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function truncate(s: string, n: number) {
  return s.length > n ? s.slice(0, n - 1) + '…' : s
}
