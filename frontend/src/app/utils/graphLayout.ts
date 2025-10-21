/**
 * Graph layout algorithms for automatic node positioning
 */

export type NodeT = any
export type EdgeT = any

type LayoutConfig = {
  horizontalSpacing: number
  verticalSpacing: number
  nodeWidth: number
  nodeHeight: number
}

const DEFAULT_CONFIG: LayoutConfig = {
  horizontalSpacing: 200,
  verticalSpacing: 150,
  nodeWidth: 180,
  nodeHeight: 80
}

/**
 * Hierarchical layout using topological sorting
 * Arranges nodes in layers based on their dependencies
 */
export function hierarchicalLayout(
  nodes: NodeT[],
  edges: EdgeT[],
  config: Partial<LayoutConfig> = {}
): NodeT[] {
  const cfg = { ...DEFAULT_CONFIG, ...config }

  if (nodes.length === 0) return []

  // Build adjacency list
  const adjacency = new Map<string, string[]>()
  const inDegree = new Map<string, number>()

  nodes.forEach(node => {
    adjacency.set(node.id, [])
    inDegree.set(node.id, 0)
  })

  edges.forEach(edge => {
    const sourceId = edge.from_id || edge.source
    const targetId = edge.to_id || edge.target
    const from = adjacency.get(sourceId)
    if (from) {
      from.push(targetId)
    }
    inDegree.set(targetId, (inDegree.get(targetId) || 0) + 1)
  })

  // Topological sort to determine layers
  const layers: string[][] = []
  const nodeLayer = new Map<string, number>()
  const queue: string[] = []

  // Start with nodes that have no incoming edges
  inDegree.forEach((degree, nodeId) => {
    if (degree === 0) {
      queue.push(nodeId)
      nodeLayer.set(nodeId, 0)
    }
  })

  // If no root nodes (circular graph), start with first node
  if (queue.length === 0 && nodes.length > 0) {
    queue.push(nodes[0].id)
    nodeLayer.set(nodes[0].id, 0)
  }

  // Process nodes level by level
  while (queue.length > 0) {
    const nodeId = queue.shift()!
    const layer = nodeLayer.get(nodeId) || 0

    if (!layers[layer]) {
      layers[layer] = []
    }
    layers[layer].push(nodeId)

    // Process children
    const children = adjacency.get(nodeId) || []
    children.forEach(childId => {
      const childInDegree = inDegree.get(childId) || 0
      inDegree.set(childId, childInDegree - 1)

      // Update child's layer to be one more than current
      const currentChildLayer = nodeLayer.get(childId) || 0
      nodeLayer.set(childId, Math.max(currentChildLayer, layer + 1))

      if (inDegree.get(childId) === 0 && !queue.includes(childId)) {
        queue.push(childId)
      }
    })
  }

  // Add any remaining nodes (disconnected components)
  const processedNodes = new Set(Array.from(nodeLayer.keys()))
  nodes.forEach(node => {
    if (!processedNodes.has(node.id)) {
      const lastLayer = layers.length
      if (!layers[lastLayer]) {
        layers[lastLayer] = []
      }
      layers[lastLayer].push(node.id)
      nodeLayer.set(node.id, lastLayer)
    }
  })

  // Position nodes based on layers
  const positionedNodes = nodes.map(node => {
    const layer = nodeLayer.get(node.id) || 0
    const nodesInLayer = layers[layer] || []
    const indexInLayer = nodesInLayer.indexOf(node.id)

    // Center the layer horizontally
    const layerWidth = nodesInLayer.length * (cfg.nodeWidth + cfg.horizontalSpacing)
    const startX = -layerWidth / 2

    const x = startX + indexInLayer * (cfg.nodeWidth + cfg.horizontalSpacing) + cfg.nodeWidth / 2
    const y = layer * cfg.verticalSpacing

    return {
      ...node,
      x,
      y
    }
  })

  // Center the entire graph in viewport (shift to positive coordinates with offset)
  const centerX = 400  // Center horizontally around 400px
  const centerY = 200  // Start from top with some offset

  return positionedNodes.map(node => ({
    ...node,
    x: (node.x || 0) + centerX,
    y: (node.y || 0) + centerY
  }))
}

/**
 * Force-directed layout (simple spring model)
 * Uses physics simulation to arrange nodes
 */
export function forceDirectedLayout(
  nodes: NodeT[],
  edges: EdgeT[],
  iterations: number = 50
): NodeT[] {
  if (nodes.length === 0) return []

  // Initialize with current positions or random
  const positions = nodes.map(node => ({
    id: node.id,
    x: node.x || Math.random() * 800,
    y: node.y || Math.random() * 600,
    vx: 0,
    vy: 0
  }))

  const k = 200 // Ideal spring length
  const c_rep = 50000 // Repulsion constant
  const c_spring = 0.1 // Spring constant
  const damping = 0.8

  for (let iter = 0; iter < iterations; iter++) {
    // Reset forces
    positions.forEach(p => {
      p.vx = 0
      p.vy = 0
    })

    // Repulsion between all pairs
    for (let i = 0; i < positions.length; i++) {
      for (let j = i + 1; j < positions.length; j++) {
        const dx = positions[j].x - positions[i].x
        const dy = positions[j].y - positions[i].y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1

        const force = c_rep / (dist * dist)
        const fx = (dx / dist) * force
        const fy = (dy / dist) * force

        positions[i].vx -= fx
        positions[i].vy -= fy
        positions[j].vx += fx
        positions[j].vy += fy
      }
    }

    // Attraction along edges
    edges.forEach(edge => {
      const sourceId = edge.from_id || edge.source
      const targetId = edge.to_id || edge.target
      const source = positions.find(p => p.id === sourceId)
      const target = positions.find(p => p.id === targetId)

      if (source && target) {
        const dx = target.x - source.x
        const dy = target.y - source.y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1

        const force = c_spring * (dist - k)
        const fx = (dx / dist) * force
        const fy = (dy / dist) * force

        source.vx += fx
        source.vy += fy
        target.vx -= fx
        target.vy -= fy
      }
    })

    // Update positions
    positions.forEach(p => {
      p.x += p.vx * damping
      p.y += p.vy * damping
    })
  }

  // Apply positions to nodes and center in viewport
  const result = nodes.map(node => {
    const pos = positions.find(p => p.id === node.id)
    return {
      ...node,
      x: pos ? pos.x : (node.x || 0),
      y: pos ? pos.y : (node.y || 0)
    }
  })

  // Calculate bounding box
  const xs = result.map(n => n.x || 0)
  const ys = result.map(n => n.y || 0)
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)

  // Calculate center offset to position graph in viewport
  const graphWidth = maxX - minX
  const graphHeight = maxY - minY
  const targetCenterX = 400
  const targetCenterY = 300
  const currentCenterX = minX + graphWidth / 2
  const currentCenterY = minY + graphHeight / 2
  const offsetX = targetCenterX - currentCenterX
  const offsetY = targetCenterY - currentCenterY

  // Apply centering offset
  return result.map(node => ({
    ...node,
    x: (node.x || 0) + offsetX,
    y: (node.y || 0) + offsetY
  }))
}

/**
 * Circular layout - arranges nodes in a circle
 */
export function circularLayout(
  nodes: NodeT[],
  radius: number = 300
): NodeT[] {
  if (nodes.length === 0) return []

  return nodes.map((node, index) => {
    const angle = (2 * Math.PI * index) / nodes.length
    const x = radius * Math.cos(angle) + 400  // Center at 400, 300
    const y = radius * Math.sin(angle) + 300

    return {
      ...node,
      x,
      y
    }
  })
}

/**
 * Grid layout - arranges nodes in a grid
 */
export function gridLayout(
  nodes: NodeT[],
  columns: number = 4,
  spacing: number = 200
): NodeT[] {
  if (nodes.length === 0) return []

  return nodes.map((node, index) => {
    const col = index % columns
    const row = Math.floor(index / columns)

    return {
      ...node,
      x: col * spacing + 200,  // Start at 200px from left
      y: row * spacing + 150   // Start at 150px from top
    }
  })
}

/**
 * Improve node positioning when creating new nodes
 * Places new node near selected node or in empty space
 */
export function getOptimalPositionForNewNode(
  existingNodes: NodeT[],
  referenceNode?: NodeT,
  offset: { x: number; y: number } = { x: 250, y: 0 }
): { x: number; y: number } {
  if (!referenceNode && existingNodes.length === 0) {
    return { x: 0, y: 0 }
  }

  if (referenceNode) {
    // Place near reference node with offset
    return {
      x: (referenceNode.x || 0) + offset.x,
      y: (referenceNode.y || 0) + offset.y
    }
  }

  // Find empty space in the graph
  // Calculate bounding box of existing nodes
  const xs = existingNodes.map(n => n.x || 0)
  const ys = existingNodes.map(n => n.y || 0)
  const maxX = Math.max(...xs, 0)
  const maxY = Math.max(...ys, 0)

  // Place to the right of the rightmost node
  return {
    x: maxX + 250,
    y: maxY / 2
  }
}
