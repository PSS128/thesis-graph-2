'use client'

import React, { useEffect, useMemo, useRef, useState } from 'react'

type NodeT = {
  id: string
  // New schema fields
  name?: string
  kind?: 'THESIS' | 'VARIABLE' | 'ASSUMPTION'
  definition?: string
  // Legacy fields (for backward compatibility)
  text?: string
  type?: 'THESIS' | 'CLAIM'
  x?: number
  y?: number
}

type EdgeT = {
  from_id: string
  to_id: string
  // New schema fields
  type?: 'CAUSES' | 'MODERATES' | 'MEDIATES' | 'CONTRADICTS'
  status?: 'PROPOSED' | 'ACCEPTED' | 'REJECTED'
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
    // Only start lasso if clicking on background (not edge mode)
    if (!edgeMode && e.target === e.currentTarget) {
      const p = ptFromEvent(e)
      setLassoStart(p)
      setLassoEnd(p)
    }
  }

  const onSvgMouseUp = () => {
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
  const getEdgeRelation = (e: EdgeT): string => {
    // Map new types to old relations
    if (e.type === 'CONTRADICTS') return 'CONTRADICTS'
    if (e.relation) return e.relation
    return 'SUPPORTS' // Default for CAUSES, MODERATES, MEDIATES
  }
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

  // Render helpers
  const NODE_R = 22
  const colorForType = (t: string) => (t === 'THESIS' ? '#164' : '#345')
  const colorForRel = (r: string) => (r === 'SUPPORTS' ? '#33a852' : '#c0392b')

  // Arrow marker ids
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
        boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
      }}
    >
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
          cursor: dragId.current ? 'grabbing' : lassoStart ? 'crosshair' : 'default'
        }}
      >
        {/* defs for arrowheads */}
        <defs>
          <marker id={markerIdSupport} markerWidth="10" markerHeight="10" refX="10" refY="5" orient="auto">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#33a852" />
          </marker>
          <marker id={markerIdContr} markerWidth="10" markerHeight="10" refX="10" refY="5" orient="auto">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#c0392b" />
          </marker>
        </defs>

        {/* edges */}
        {edges.map((e, idx) => {
          const from = renderedNodes.find((n) => n.id === e.from_id)
          const to = renderedNodes.find((n) => n.id === e.to_id)
          if (!from || !to) return null
          const relation = getEdgeRelation(e)
          const status = getEdgeStatus(e)
          const stroke = colorForRel(relation)
          const markerUrl = relation === 'SUPPORTS' ? `url(#${markerIdSupport})` : `url(#${markerIdContr})`
          // Proposed edges are dashed, accepted are solid
          const dashArray = status === 'PROPOSED' ? '5,5' : '0'
          const opacity = status === 'PROPOSED' ? 0.6 : 0.9
          const edgeId = `E${idx}`
          const hasWarnings = edgeWarnings[edgeId] || edgeWarnings[`e${idx}`]
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
                textAnchor="middle"
                style={{ pointerEvents: 'none' }}
              >
                {relation.toLowerCase()}
              </text>

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
          const fill = '#f6fbe9'
          const nodeType = getNodeType(n)
          const stroke = colorForType(nodeType)
          const hasWarnings = nodeWarnings[n.id]

          return (
            <g
              key={n.id}
              onMouseDown={(e) => onNodeMouseDown(e, n.id)}
              onMouseUp={(e) => onNodeMouseUp(e, n.id)}
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
              <circle
                cx={n.x}
                cy={n.y}
                r={NODE_R}
                fill={fill}
                stroke={stroke}
                strokeWidth={sel ? 3 : 1.5}
                opacity={isPending ? 0.8 : 1}
              />
              {/* node label */}
              <text
                x={n.x}
                y={n.y - NODE_R - 8}
                textAnchor="middle"
                fontSize={11}
                fill="#999"
                style={{ pointerEvents: 'none' }}
              >
                {nodeType}
              </text>
              <text
                x={n.x}
                y={n.y + 4}
                textAnchor="middle"
                fontSize={12}
                fill="#222"
                style={{ pointerEvents: 'none' }}
              >
                {truncate(getNodeText(n), 36)}
              </text>
              {/* a subtle dot below selected nodes */}
              {sel ? (
                <rect
                  x={n.x - 4}
                  y={n.y + NODE_R + 6}
                  width={8}
                  height={8}
                  rx={2}
                  fill={stroke}
                  opacity={0.7}
                />
              ) : null}

              {/* Warning badge */}
              {hasWarnings && (
                <g>
                  <circle
                    cx={n.x + NODE_R - 2}
                    cy={n.y - NODE_R + 2}
                    r={9}
                    fill="#ff4d4f"
                    stroke="#fff"
                    strokeWidth={2}
                  />
                  <text
                    x={n.x + NODE_R - 2}
                    y={n.y - NODE_R + 6}
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
      </svg>
    </div>
  )
}

function truncate(s: string, n: number) {
  return s.length > n ? s.slice(0, n - 1) + '…' : s
}
