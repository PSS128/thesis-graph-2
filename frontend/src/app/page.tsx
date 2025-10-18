'use client'

import { useEffect, useMemo, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import GraphCanvas from './components/GraphCanvas'
import EdgeRationaleCard from './components/EdgeRationaleCard'
import CitationPanel from './components/CitationPanel'
import NodeExtractCard from './components/NodeExtractCard'
import NodeContextMenu from './components/NodeContextMenu'
import MissingPiecesModal from './components/MissingPiecesModal'
import GraphCritiquePanel from './components/GraphCritiquePanel'

// ---------- Types ----------
type CitationRef = {
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
  citations?: CitationRef[]
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
  mechanisms?: string[]
  assumptions?: string[]
  confounders?: string[]
  citations?: EdgeCitation[]
  // Legacy fields (for backward compatibility)
  relation?: 'SUPPORTS' | 'CONTRADICTS'
  rationale?: string
  confidence?: number
}

type Citation = {
  rank: number
  score: number
  chunk_id: string
  text: string
  doc: { id: string; title?: string; source?: string }
}

type ProjectMeta = { id: number; title: string }
type Busy = 'idle' | 'extract' | 'suggest' | 'upload' | 'cite' | 'save' | 'compose'
type Tone = 'neutral' | 'critical' | 'persuasive' | 'explanatory' | 'skeptical'

// ---------- Normalizers (accept array OR {nodes/edges}) ----------
type NodesResponse = { nodes: NodeT[] } | NodeT[]
type EdgesResponse = { edges: EdgeT[] } | EdgeT[]

function normalizeNodes(d: any): NodeT[] {
  return Array.isArray(d) ? d : d?.nodes ?? []
}
function normalizeEdges(d: any): EdgeT[] {
  return Array.isArray(d) ? d : d?.edges ?? []
}

// ---------- Schema helpers ----------
function getNodeText(n: NodeT): string {
  return n.name || n.text || 'Untitled'
}

function getNodeKind(n: NodeT): string {
  return n.kind || n.type || 'VARIABLE'
}

function getEdgeType(e: EdgeT): string {
  return e.type || e.relation || 'CAUSES'
}

function getEdgeStatus(e: EdgeT): string {
  return e.status || 'ACCEPTED'
}

// ================================================================
export default function Home() {
  const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  // health + form
  const [msg, setMsg] = useState('loading...')
  const [thesis, setThesis] = useState('')
  const [input, setInput] = useState(
    'Technology broadens access to educational resources. Interactive tools deepen engagement and retention. Data-driven feedback accelerates skill development. Personalization fosters equity and efficiency. Responsible implementation is essential.'
  )

  // graph state
  const [nodes, setNodes] = useState<NodeT[]>([])
  const [edges, setEdges] = useState<EdgeT[]>([])
  const [citations, setCitations] = useState<Record<string, Citation[]>>({})

  // ui state
  const [busy, setBusy] = useState<Busy>('idle')

  // projects
  const [projectId, setProjectId] = useState<number | null>(null)
  const [projectTitle, setProjectTitle] = useState<string>('')
  const [projects, setProjects] = useState<ProjectMeta[]>([])

  // selection + compose results + LLM badge
  const [selected, setSelected] = useState<Record<string, boolean>>({})
  const [outline, setOutline] = useState<{ heading: string; points: string[] }[]>([])
  const [essay, setEssay] = useState<string>('')
  const [llmUsed, setLlmUsed] = useState<boolean | null>(null)

  // Autosave
  const [autosave, setAutosave] = useState<boolean>(true)
  const [lastSaved, setLastSaved] = useState<number | null>(null)
  const [dirty, setDirty] = useState<boolean>(false)

  // Compose controls
  const [audience, setAudience] = useState<string>('academic')
  const [words, setWords] = useState<number>(700)
  const [tone, setTone] = useState<Tone>('neutral')

  // Cite mode (front-end orchestration)
  const [citeMode, setCiteMode] = useState<boolean>(false)
  const [references, setReferences] = useState<Citation[]>([])

  // interactive graph editing
  const [edgeMode, setEdgeMode] = useState<boolean>(false)
  const [newEdgeRelation, setNewEdgeRelation] = useState<'SUPPORTS' | 'CONTRADICTS'>('SUPPORTS')

  // edge rationale modal state
  type PendingEdge = {
    from_id: string
    to_id: string
    type: string
  }
  const [pendingEdge, setPendingEdge] = useState<PendingEdge | null>(null)
  const [edgeRationale, setEdgeRationale] = useState<{
    mechanisms: string[]
    assumptions: string[]
    likely_confounders: string[]
    prior_evidence_types: string[]
  } | null>(null)
  const [fetchingRationale, setFetchingRationale] = useState(false)

  // citation panel state
  type EvidenceItem = {
    title?: string
    url?: string
    quote: string
    supports: 'supports' | 'contradicts'
    strength: number
  }
  const [showCitationPanel, setShowCitationPanel] = useState(false)
  const [currentEvidence, setCurrentEvidence] = useState<EvidenceItem[]>([])
  const [fetchingEvidence, setFetchingEvidence] = useState(false)
  const [currentEdgeIndex, setCurrentEdgeIndex] = useState<number | null>(null)

  // Phase 4: text highlight → node extraction
  const [highlightedText, setHighlightedText] = useState('')
  const [showNodeExtractCard, setShowNodeExtractCard] = useState(false)
  const [nodeExtraction, setNodeExtraction] = useState<{
    name: string
    definition: string
    synonyms: string[]
    measurement_ideas: string[]
    merge_hint?: { existing_name: string; similarity: number; action: string }
  } | null>(null)
  const [fetchingExtraction, setFetchingExtraction] = useState(false)

  // Phase 4: node context menu
  const [contextMenu, setContextMenu] = useState<{
    nodeId: string
    nodeName: string
    x: number
    y: number
  } | null>(null)

  // Phase 4: missing pieces modal
  const [showMissingPieces, setShowMissingPieces] = useState(false)
  const [missingPieces, setMissingPieces] = useState<{
    mediators: string[]
    moderators: string[]
    study_designs: string[]
  } | null>(null)
  const [fetchingMissingPieces, setFetchingMissingPieces] = useState(false)
  const [focusNodeId, setFocusNodeId] = useState<string | null>(null)

  // Phase 4: graph critique
  const [showCritique, setShowCritique] = useState(false)
  const [critiqueWarnings, setCritiqueWarnings] = useState<
    { node_or_edge_id: string; label: string; fix_suggestion: string }[]
  >([])
  const [fetchingCritique, setFetchingCritique] = useState(false)

  // ---------------- Effects ----------------
  useEffect(() => {
    fetch(`${API}/`)
      .then((r) => r.json())
      .then((d) => setMsg(d.message))
      .catch(() => setMsg('failed to reach backend'))
  }, [API])

  useEffect(() => {
    refreshProjects().catch(() => {})
  }, [])

  useEffect(() => {
    if (!projectId) return
    setDirty(true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(nodes), JSON.stringify(edges), thesis])

  useEffect(() => {
    if (!autosave || !projectId || !dirty) return
    if (!nodes.length) return
    const t = setTimeout(async () => {
      try {
        await saveProjectSilent()
        setLastSaved(Date.now())
        setDirty(false)
      } catch {}
    }, 2000)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autosave, projectId, dirty, JSON.stringify(nodes), JSON.stringify(edges), thesis])

  // ---------------- Backend calls ----------------
  const extract = async () => {
    setBusy('extract')
    setEdges([])
    setCitations({})
    setSelected({})
    setOutline([])
    setEssay('')
    setReferences([])
    try {
      const res = await fetch(`${API}/extract/nodes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: input, thesis: thesis || null })
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`)
      const data: NodesResponse = await res.json()
      const next = normalizeNodes(data)
      setNodes(next)
      if (!next.length) {
        console.warn('Extract returned an empty list.')
        alert('Extract returned no nodes.')
      }
    } catch (e: any) {
      alert(`Failed to extract nodes:\n${e.message || e}`)
    } finally {
      setBusy('idle')
    }
  }

  const suggest = async () => {
    if (!nodes.length) return alert('Run Extract first.')
    setBusy('suggest')
    try {
      const res = await fetch(`${API}/edges/suggest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nodes })
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`)
      const data: EdgesResponse = await res.json()
      const next = normalizeEdges(data)
      setEdges(next)
      if (!next.length) {
        console.warn('Suggest returned an empty list.')
        alert('No links suggested.')
      }
    } catch (e: any) {
      alert(`Failed to suggest edges:\n${e.message || e}`)
    } finally {
      setBusy('idle')
    }
  }

  const upload = async (file: File) => {
    setBusy('upload')
    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('title', file.name)
      const r = await fetch(`${API}/ingest/upload`, { method: 'POST', body: fd })
      if (!r.ok) throw new Error(await r.text())
      await r.json()
      alert('File indexed ✅')
    } catch (e: any) {
      alert(`Upload failed:\n${e.message || e}`)
    } finally {
      setBusy('idle')
    }
  }

  const citeNode = async (n: NodeT) => {
    setBusy('cite')
    try {
      const r = await fetch(`${API}/retrieve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: getNodeText(n), top_k: 3 })
      })
      if (!r.ok) throw new Error(await r.text())
      const data: Citation[] = await r.json()
      setCitations((prev) => ({ ...prev, [n.id]: data }))
    } catch (e: any) {
      alert(`Citations failed:\n${e.message || e}`)
    } finally {
      setBusy('idle')
    }
  }

  // ---------------- Projects: list / create / save / load / rename / delete ----------------
  async function refreshProjects() {
    const r = await fetch(`${API}/projects`)
    if (r.ok) {
      const data: ProjectMeta[] = await r.json()
      setProjects(data)
    }
  }

  async function newProject() {
    const r = await fetch(
      `${API}/projects?title=${encodeURIComponent(projectTitle || 'Untitled Project')}`,
      { method: 'POST' }
    )
    if (!r.ok) return alert('Failed to create project')
    const p: ProjectMeta = await r.json()
    setProjectId(p.id)
    await refreshProjects()
    alert(`Created project #${p.id}`)
  }

  async function renameProject() {
    if (!projectId) return alert('No project selected.')
    const r = await fetch(`${API}/projects/${projectId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: projectTitle || 'Untitled Project' })
    })
    if (!r.ok) return alert('Rename failed')
    await refreshProjects()
    alert('Renamed ✅')
  }

  async function deleteProject() {
    if (!projectId) return alert('No project selected.')
    if (!confirm(`Delete project #${projectId}? This cannot be undone.`)) return
    const r = await fetch(`${API}/projects/${projectId}`, { method: 'DELETE' })
    if (!r.ok) return alert('Delete failed')
    setProjectId(null)
    setProjectTitle('')
    setNodes([]); setEdges([]); setCitations({}); setSelected({})
    setOutline([]); setEssay(''); setReferences([])
    await refreshProjects()
    alert('Deleted ✅')
  }

  async function saveProject() {
    if (!projectId) return alert('Create or select a project first.')
    setBusy('save')
    try {
      const payload = { nodes, edges }
      const r = await fetch(`${API}/projects/${projectId}/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (!r.ok) {
        const text = await r.text().catch(() => '')
        throw new Error(`HTTP ${r.status} ${text}`)
      }
      setLastSaved(Date.now())
      setDirty(false)
      alert('Saved ✅')
    } catch (e: any) {
      console.error('Save error:', e)
      alert(`Save failed:\n${e.message || e}`)
    } finally {
      setBusy('idle')
    }
  }

  async function saveProjectSilent() {
    if (!projectId) return
    try {
      const payload = { nodes, edges }
      const r = await fetch(`${API}/projects/${projectId}/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (!r.ok) {
        const text = await r.text().catch(() => '')
        console.warn('Autosave failed:', r.status, text)
      }
    } catch (e) {
      console.warn('Autosave error:', e)
    }
  }

  async function loadProject(id: number) {
    const r = await fetch(`${API}/projects/${id}`)
    if (!r.ok) return alert('Load failed')
    const data = await r.json()
    setProjectId(data.project.id)
    setProjectTitle(data.project.title)
    setNodes(data.nodes || [])
    setEdges(data.edges || [])
    setCitations({})
    setSelected({})
    setOutline([])
    setEssay('')
    setReferences([])
    setDirty(false)
    setLastSaved(null)
    alert(`Loaded project #${data.project.id}`)
  }

  // ---------------- Export / Import ----------------
  async function exportProject() {
    if (!projectId) return alert('Create or select a project first.')
    const r = await fetch(`${API}/projects/${projectId}/export`)
    if (!r.ok) return alert(`Export failed: ${await r.text()}`)
    const data = await r.json()
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `project-${projectId}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  async function importProject(file: File) {
    try {
      const text = await file.text()
      const r = await fetch(`${API}/projects/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: text
      })
      if (!r.ok) throw new Error(await r.text())
      const data = await r.json()
      await loadProject(data.id)
      alert(`Imported as project #${data.id}`)
    } catch (e: any) {
      alert(`Import failed:\n${e.message || e}`)
    }
  }

  // ---------------- Node positions (from GraphCanvas) ----------------
  const applyPositions = (pos: { id: string; x: number; y: number }[]) => {
    if (!pos.length) return
    const map = new Map(pos.map((p) => [p.id, p]))
    setNodes((prev) =>
      prev.map((n) =>
        map.has(n.id) ? { ...n, x: map.get(n.id)!.x, y: map.get(n.id)!.y } : n
      )
    )
  }

  // ---------------- Manual edits ----------------
  function updateNodeText(id: string, text: string) {
    setNodes((prev) => prev.map((n) => (n.id === id ? { ...n, name: text, text } : n)))
  }
  function deleteNode(id: string) {
    setNodes((prev) => prev.filter((n) => n.id !== id))
    setEdges((prev) => prev.filter((e) => e.from_id !== id && e.to_id !== id))
    setCitations((prev) => { const cp = { ...prev }; delete cp[id]; return cp })
    setSelected((prev) => { const s = { ...prev }; delete s[id]; return s })
  }
  function deleteEdge(index: number) {
    setEdges((prev) => prev.filter((_, i) => i !== index))
  }

  // ---------------- Selection & Compose ----------------
  function toggleSelected(id: string) {
    setSelected((prev) => ({ ...prev, [id]: !prev[id] }))
  }
  function selectAll() {
    const next: Record<string, boolean> = {}
    nodes.forEach((n) => { next[n.id] = true })
    setSelected(next)
  }
  function selectNone() {
    setSelected({})
  }

  async function composeFromSelectionBase(chosen: NodeT[], chosenEdges: EdgeT[]) {
  setBusy('compose')
  try {
    const payload = {
      thesis: thesis || undefined,
      nodes: chosen,
      edges: chosenEdges,
      words,
      audience,
      tone,
      mode: 'both',
    }

    console.info('[compose] API =', API)
    console.info('[compose] payload =', payload)

    const r = await fetch(`${API}/compose`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    // LLM badge
    const used = r.headers.get('X-LLM-Used') === '1'
    setLlmUsed(used)

    if (!r.ok) {
      const text = await r.text().catch(() => '')
      throw new Error(`HTTP ${r.status} ${text}`)
    }

    const data = await r.json()
    setOutline(data.outline || [])
    setEssay(data.essay_md || '')
    setTimeout(
      () => document.getElementById('compose-result')?.scrollIntoView({ behavior: 'smooth' }),
      50
    )
  } catch (e: any) {
    console.error('[compose] FAILED', e)
    // If this is the browser's network/CORS error, help the user
    if (e?.message?.includes('Failed to fetch') || e?.name === 'TypeError') {
      console.warn(
        '[compose] Likely URL/CORS/preflight problem. ' +
          'Check that the backend is running on http://localhost:8000, ' +
          'that /compose exists (GET should be 405), and that CORS allows http://localhost:3000.'
      )
    }
    alert(`Compose failed:\n${e.message || e}`)
  } finally {
    setBusy('idle')
  }
}


  async function composeWithCitations() {
    const chosen = nodes.filter((n) => selected[n.id])
    if (chosen.length === 0) return alert('Select at least one node.')
    const selIds = new Set(chosen.map((n) => n.id))
    const chosenEdges = edges.filter((e) => selIds.has(e.from_id) && selIds.has(e.to_id))

    try {
      setBusy('cite')
      const all: Citation[] = []
      await Promise.all(
        chosen.map(async (n) => {
          const r = await fetch(`${API}/retrieve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: getNodeText(n), top_k: 2 })
          })
          if (!r.ok) return
          const cs: Citation[] = await r.json()
          cs.forEach((c) => all.push(c))
        })
      )
      const seen = new Set<string>()
      const dedup = all.filter((c) => {
        if (seen.has(c.chunk_id)) return false
        seen.add(c.chunk_id)
        return true
      })
      setReferences(dedup)
    } catch (e) {
      console.warn('Citation retrieval error', e)
      setReferences([])
    } finally {
      setBusy('idle')
    }

    await composeFromSelectionBase(chosen, chosenEdges)
  }

  async function composeFromSelection() {
    const chosen = nodes.filter((n) => selected[n.id])
    if (chosen.length === 0) return alert('Select at least one node.')
    const selIds = new Set(chosen.map((n) => n.id))
    const chosenEdges = edges.filter((e) => selIds.has(e.from_id) && selIds.has(e.to_id))
    if (citeMode) await composeWithCitations()
    else await composeFromSelectionBase(chosen, chosenEdges)
  }

  // --- Markdown export ---
  function downloadMarkdown() {
    const title = projectTitle || thesis || 'Thesis Graph'
    const lines: string[] = []
    lines.push(`# ${title}`)
    if (outline.length) {
      lines.push('\n## Outline')
      outline.forEach((o) => {
        lines.push(`\n### ${o.heading}`)
        o.points.forEach((p) => lines.push(`- ${p}`))
      })
    }
    if (essay) {
      lines.push('\n## Essay\n')
      lines.push(essay)
    }
    if (citeMode && references.length) {
      lines.push('\n## References\n')
      references.forEach((c, i) => {
        const src = c.doc.title || c.doc.source || `Source ${i + 1}`
        lines.push(`- ${src} — score ${c.score.toFixed(3)}\n  ${c.text}`)
      })
    }
    const blob = new Blob([lines.join('\n')], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${(title || 'thesis-graph').toLowerCase().replace(/\s+/g, '-')}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  // --- NEW: Add node / edge helpers ---
  function addNode(kind: 'THESIS' | 'CLAIM') {
    const id = `N${Math.random().toString(36).slice(2, 7)}`
    const label = kind === 'THESIS' ? 'New thesis' : 'New claim'
    const nodeKind = kind === 'THESIS' ? 'THESIS' : 'VARIABLE'
    setNodes((prev) => [...prev, { id, name: label, kind: nodeKind, text: label, type: kind }])
    setSelected((prev) => ({ ...prev, [id]: true }))
  }

  async function createEdge(from_id: string, to_id: string) {
    if (from_id === to_id) return
    const edgeType = newEdgeRelation === 'SUPPORTS' ? 'CAUSES' : 'CONTRADICTS'
    const exists = edges.some(
      (e) => e.from_id === from_id && e.to_id === to_id && getEdgeType(e) === edgeType
    )
    if (exists) return

    // Set up pending edge and fetch rationale
    setPendingEdge({ from_id, to_id, type: edgeType })
    setEdgeRationale(null)
    setFetchingRationale(true)

    try {
      const fromNode = nodes.find((n) => n.id === from_id)
      const toNode = nodes.find((n) => n.id === to_id)
      if (!fromNode || !toNode) {
        throw new Error('Node not found')
      }

      const r = await fetch(`${API}/edge/rationale`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          a_name: getNodeText(fromNode),
          b_name: getNodeText(toNode)
        })
      })

      if (!r.ok) throw new Error(await r.text())
      const data = await r.json()
      setEdgeRationale(data)
    } catch (e: any) {
      console.error('Failed to fetch edge rationale:', e)
      // If fetching rationale fails, still show modal but with empty rationale
      setEdgeRationale({
        mechanisms: [],
        assumptions: [],
        likely_confounders: [],
        prior_evidence_types: []
      })
    } finally {
      setFetchingRationale(false)
    }
  }

  async function acceptEdge() {
    if (!pendingEdge) return

    const newEdge: EdgeT = {
      from_id: pendingEdge.from_id,
      to_id: pendingEdge.to_id,
      type: pendingEdge.type as 'CAUSES' | 'MODERATES' | 'MEDIATES' | 'CONTRADICTS',
      status: 'ACCEPTED' as 'ACCEPTED',
      relation: newEdgeRelation,
      mechanisms: edgeRationale?.mechanisms || [],
      assumptions: edgeRationale?.assumptions || [],
      confounders: edgeRationale?.likely_confounders || []
    }

    setEdges((prev) => [...prev, newEdge])
    const newEdgeIndex = edges.length

    // Close rationale modal
    setPendingEdge(null)
    setEdgeRationale(null)

    // Fetch evidence for this edge
    await fetchEvidence(newEdgeIndex, newEdge)
  }

  async function fetchEvidence(edgeIndex: number, edge: EdgeT) {
    const fromNode = nodes.find((n) => n.id === edge.from_id)
    const toNode = nodes.find((n) => n.id === edge.to_id)
    if (!fromNode || !toNode) return

    setCurrentEdgeIndex(edgeIndex)
    setShowCitationPanel(true)
    setFetchingEvidence(true)
    setCurrentEvidence([])

    try {
      const r = await fetch(`${API}/edge/evidence`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          a_name: getNodeText(fromNode),
          b_name: getNodeText(toNode),
          mechanisms: edge.mechanisms || [],
          top_k: 3
        })
      })

      if (!r.ok) throw new Error(await r.text())
      const data: EvidenceItem[] = await r.json()
      setCurrentEvidence(data)
    } catch (e: any) {
      console.error('Failed to fetch evidence:', e)
      setCurrentEvidence([])
    } finally {
      setFetchingEvidence(false)
    }
  }

  function rejectEdge() {
    setPendingEdge(null)
    setEdgeRationale(null)
  }

  function cancelEdgeModal() {
    setPendingEdge(null)
    setEdgeRationale(null)
  }

  function pinCitation(item: EvidenceItem) {
    if (currentEdgeIndex === null) return

    // Add citation to the edge
    setEdges((prev) =>
      prev.map((e, i) => {
        if (i !== currentEdgeIndex) return e
        const newCitation = {
          doc: item.title || item.url || 'Unknown',
          span: [0, 0] as [number, number],
          support: item.supports,
          strength: item.strength
        }
        return {
          ...e,
          citations: [...(e.citations || []), newCitation]
        }
      })
    )

    alert(`Citation pinned to edge #${currentEdgeIndex + 1}`)
  }

  function closeCitationPanel() {
    setShowCitationPanel(false)
    setCurrentEvidence([])
    setCurrentEdgeIndex(null)
  }

  // ---------------- Phase 4: Text → Node Extraction ----------------
  async function extractNodeFromText(text: string) {
    setHighlightedText(text)
    setShowNodeExtractCard(true)
    setFetchingExtraction(true)
    setNodeExtraction(null)

    try {
      const existingNames = nodes.map((n) => getNodeText(n))
      const r = await fetch(`${API}/node/extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          existing_names: existingNames
        })
      })

      if (!r.ok) throw new Error(await r.text())
      const data = await r.json()
      setNodeExtraction(data)
    } catch (e: any) {
      console.error('Failed to extract node:', e)
      alert(`Node extraction failed:\n${e.message || e}`)
      setShowNodeExtractCard(false)
    } finally {
      setFetchingExtraction(false)
    }
  }

  function acceptExtractedNode() {
    if (!nodeExtraction) return

    const id = `N${Math.random().toString(36).slice(2, 7)}`
    const newNode: NodeT = {
      id,
      name: nodeExtraction.name,
      kind: 'VARIABLE',
      definition: nodeExtraction.definition,
      synonyms: nodeExtraction.synonyms,
      measurement_ideas: nodeExtraction.measurement_ideas
    }

    setNodes((prev) => [...prev, newNode])
    setSelected((prev) => ({ ...prev, [id]: true }))
    setShowNodeExtractCard(false)
    setNodeExtraction(null)
  }

  function mergeExtractedNode() {
    if (!nodeExtraction?.merge_hint) return

    // Find the existing node and update it
    const existingName = nodeExtraction.merge_hint.existing_name
    const existingNode = nodes.find((n) => getNodeText(n) === existingName)

    if (existingNode) {
      setNodes((prev) =>
        prev.map((n) =>
          n.id === existingNode.id
            ? {
                ...n,
                definition: nodeExtraction.definition,
                synonyms: [...new Set([...(n.synonyms || []), ...nodeExtraction.synonyms])]
              }
            : n
        )
      )
      alert(`Merged with existing node: ${existingName}`)
    }

    setShowNodeExtractCard(false)
    setNodeExtraction(null)
  }

  function rejectExtractedNode() {
    setShowNodeExtractCard(false)
    setNodeExtraction(null)
  }

  // ---------------- Phase 4: Missing Pieces ----------------
  async function findMissingPieces(nodeId: string) {
    setFocusNodeId(nodeId)
    setShowMissingPieces(true)
    setFetchingMissingPieces(true)
    setMissingPieces(null)

    try {
      const graphNodes = nodes.map((n) => ({
        id: n.id,
        name: getNodeText(n),
        kind: getNodeKind(n) as 'THESIS' | 'VARIABLE' | 'ASSUMPTION'
      }))

      const graphEdges = edges.map((e, i) => ({
        id: `E${i}`,
        from_id: e.from_id,
        to_id: e.to_id,
        type: getEdgeType(e) as 'CAUSES' | 'MODERATES' | 'MEDIATES' | 'CONTRADICTS',
        status: getEdgeStatus(e) as 'PROPOSED' | 'ACCEPTED' | 'REJECTED'
      }))

      const r = await fetch(`${API}/graph/suggest_mediators`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          focus_node_id: nodeId,
          nodes: graphNodes,
          edges: graphEdges
        })
      })

      if (!r.ok) throw new Error(await r.text())
      const data = await r.json()
      setMissingPieces(data)
    } catch (e: any) {
      console.error('Failed to fetch missing pieces:', e)
      setMissingPieces({ mediators: [], moderators: [], study_designs: [] })
    } finally {
      setFetchingMissingPieces(false)
    }
  }

  function acceptMediator(mediator: string) {
    const id = `N${Math.random().toString(36).slice(2, 7)}`
    const newNode: NodeT = {
      id,
      name: mediator,
      kind: 'VARIABLE',
      definition: `Mediator variable: ${mediator}`
    }

    setNodes((prev) => [...prev, newNode])
    setSelected((prev) => ({ ...prev, [id]: true }))
    alert(`Added mediator: ${mediator}`)
  }

  function acceptModerator(moderator: string) {
    const id = `N${Math.random().toString(36).slice(2, 7)}`
    const newNode: NodeT = {
      id,
      name: moderator,
      kind: 'VARIABLE',
      definition: `Moderator variable: ${moderator}`
    }

    setNodes((prev) => [...prev, newNode])
    setSelected((prev) => ({ ...prev, [id]: true }))
    alert(`Added moderator: ${moderator}`)
  }

  // ---------------- Phase 4: Graph Critique ----------------
  async function critiqueGraph() {
    setShowCritique(true)
    setFetchingCritique(true)
    setCritiqueWarnings([])

    try {
      const graphNodes = nodes.map((n) => ({
        id: n.id,
        name: getNodeText(n),
        kind: getNodeKind(n) as 'THESIS' | 'VARIABLE' | 'ASSUMPTION'
      }))

      const graphEdges = edges.map((e, i) => ({
        id: `E${i}`,
        from_id: e.from_id,
        to_id: e.to_id,
        type: getEdgeType(e) as 'CAUSES' | 'MODERATES' | 'MEDIATES' | 'CONTRADICTS',
        status: getEdgeStatus(e) as 'PROPOSED' | 'ACCEPTED' | 'REJECTED'
      }))

      const r = await fetch(`${API}/graph/critique`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nodes: graphNodes,
          edges: graphEdges
        })
      })

      if (!r.ok) throw new Error(await r.text())
      const data = await r.json()
      setCritiqueWarnings(data.warnings || [])
    } catch (e: any) {
      console.error('Failed to critique graph:', e)
      setCritiqueWarnings([])
    } finally {
      setFetchingCritique(false)
    }
  }

  // --- UI helpers ---
  const lastSavedLabel = useMemo(() => {
    if (!lastSaved) return ''
    const secs = Math.max(0, Math.floor((Date.now() - lastSaved) / 1000))
    if (secs < 5) return 'just now'
    if (secs < 60) return `${secs}s ago`
    const mins = Math.floor(secs / 60)
    return `${mins}m ago`
  }, [lastSaved])

  // =====================================================
  // UI
  // =====================================================
  return (
    <main
      style={{
        padding: 24,
        display: 'grid',
        gap: 16,
        maxWidth: 1100,
        margin: '0 auto'
      }}
    >
      <h1>Thesis Graph</h1>
      <p>
        Backend says: <strong>{msg}</strong>
      </p>

      {/* Project Bar */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <input
          placeholder="Project title"
          value={projectTitle}
          onChange={(e) => setProjectTitle(e.target.value)}
          style={{ padding: 8, border: '1px solid #ddd', borderRadius: 8 }}
        />
        <button onClick={newProject} style={{ padding: '8px 12px', border: '1px solid #333', borderRadius: 8 }}>
          New
        </button>
        <button
          onClick={renameProject}
          disabled={!projectId}
          style={{ padding: '8px 12px', border: '1px solid #333', borderRadius: 8 }}
        >
          Rename
        </button>
        <button
          onClick={deleteProject}
          disabled={!projectId}
          style={{ padding: '8px 12px', border: '1px solid #c00', color: '#c00', borderRadius: 8 }}
        >
          Delete
        </button>
        <button
          onClick={saveProject}
          disabled={busy !== 'idle' || !nodes.length}
          style={{ padding: '8px 12px', border: '1px solid #333', borderRadius: 8 }}
        >
          {busy === 'save' ? 'Saving…' : 'Save'}
        </button>
        <button
          onClick={exportProject}
          disabled={!projectId}
          style={{ padding: '8px 12px', border: '1px solid #333', borderRadius: 8 }}
        >
          Export
        </button>
        <label style={{ display: 'inline-block' }}>
          <span
            style={{ padding: '8px 12px', border: '1px solid #333', borderRadius: 8, cursor: 'pointer' }}
          >
            Import
          </span>
          <input
            type="file"
            accept="application/json,.json"
            style={{ display: 'none' }}
            onChange={(e) => e.target.files?.[0] && importProject(e.target.files[0])}
          />
        </label>
        <select
          onChange={(e) => e.target.value && loadProject(Number(e.target.value))}
          value={projectId ?? ''}
          style={{ padding: 8, border: '1px solid #ddd', borderRadius: 8 }}
        >
          <option value="">Load…</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.title} (#{p.id})
            </option>
          ))}
        </select>

        {/* Autosave toggle & status */}
        <label style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 8 }}>
          <input
            type="checkbox"
            checked={autosave}
            onChange={(e) => setAutosave(e.target.checked)}
            title="Autosave every ~2s when editing"
          />
          <span style={{ fontSize: 12 }}>Autosave</span>
        </label>
        <span style={{ fontSize: 12, color: dirty ? '#d48806' : '#666' }}>
          {dirty ? 'unsaved changes' : lastSaved ? `auto-saved ${lastSavedLabel}` : ''}
        </span>

        {projectId ? <span style={{ fontSize: 12, color: '#666' }}>Current: #{projectId}</span> : null}
      </div>

      {/* Uploads */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <input
          type="file"
          onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])}
          disabled={busy !== 'idle'}
        />
        <span style={{ fontSize: 12, color: '#666' }}>Upload PDFs or .txt to enable citations</span>
      </div>

      {/* Inputs */}
      <input
        placeholder="(Optional) Thesis"
        value={thesis}
        onChange={(e) => setThesis(e.target.value)}
        style={{ padding: 10, border: '1px solid #ddd', borderRadius: 8 }}
      />
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        rows={5}
        style={{ padding: 10, border: '1px solid #ddd', borderRadius: 8 }}
      />

      {/* Actions */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button
          onClick={extract}
          disabled={busy !== 'idle'}
          style={{ padding: '8px 12px', border: '1px solid #333', borderRadius: 8 }}
        >
          {busy === 'extract' ? 'Extracting…' : 'Extract'}
        </button>
        <button
          onClick={suggest}
          disabled={busy !== 'idle' || !nodes.length}
          style={{ padding: '8px 12px', border: '1px solid #333', borderRadius: 8 }}
        >
          {busy === 'suggest' ? 'Suggesting…' : 'Suggest Links'}
        </button>

        {/* Compose controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginLeft: 'auto', flexWrap: 'wrap' }}>
          <label style={{ fontSize: 12 }}>
            Audience:{' '}
            <select value={audience} onChange={(e) => setAudience(e.target.value)}>
              <option value="academic">academic</option>
              <option value="general">general</option>
              <option value="policy">policy</option>
              <option value="technical">technical</option>
            </select>
          </label>
          <label style={{ fontSize: 12 }}>
            Tone:{' '}
            <select value={tone} onChange={(e) => setTone(e.target.value as Tone)}>
              <option value="neutral">neutral</option>
              <option value="critical">critical</option>
              <option value="persuasive">persuasive</option>
              <option value="explanatory">explanatory</option>
              <option value="skeptical">skeptical</option>
            </select>
          </label>
          <label style={{ fontSize: 12 }}>
            Words:{' '}
            <input
              type="number"
              min={200}
              max={1500}
              step={50}
              value={words}
              onChange={(e) => setWords(Number(e.target.value))}
              style={{ width: 90 }}
            />
          </label>
        </div>
      </div>

      {/* Graph editing toolbar */}
      <div
        style={{
          display: 'flex',
          gap: 8,
          alignItems: 'center',
          padding: 8,
          border: '1px dashed #ddd',
          borderRadius: 8,
          background: '#fafafa'
        }}
      >
        <strong>Graph Tools</strong>
        <button
          onClick={() => addNode('THESIS')}
          style={{ padding: '6px 10px', border: '1px solid #333', borderRadius: 6 }}
          title="Add a thesis node"
        >
          + Thesis
        </button>
        <button
          onClick={() => addNode('CLAIM')}
          style={{ padding: '6px 10px', border: '1px solid #333', borderRadius: 6 }}
          title="Add a claim node"
        >
          + Claim
        </button>

        <label style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 12 }}>
          <input
            type="checkbox"
            checked={edgeMode}
            onChange={(e) => setEdgeMode(e.target.checked)}
            title="Click two nodes on the canvas to create an edge"
          />
          <span style={{ fontSize: 12 }}>Edge Mode</span>
        </label>

        <label style={{ fontSize: 12 }}>
          Relation:{' '}
          <select
            value={newEdgeRelation}
            onChange={(e) => setNewEdgeRelation(e.target.value as 'SUPPORTS' | 'CONTRADICTS')}
            disabled={!edgeMode}
          >
            <option value="SUPPORTS">SUPPORTS</option>
            <option value="CONTRADICTS">CONTRADICTS</option>
          </select>
        </label>

        <button
          onClick={critiqueGraph}
          disabled={nodes.length === 0}
          style={{
            padding: '6px 10px',
            border: '1px solid #ff4d4f',
            borderRadius: 6,
            marginLeft: 'auto',
            background: showCritique ? '#fff1f0' : '#fff',
            color: '#ff4d4f'
          }}
          title="Run DAG validation and check for issues"
        >
          {showCritique ? 'Hide Critique' : 'Critique Graph'}
        </button>
      </div>

      {/* Phase 4: Text Highlight → Make Node */}
      <div
        style={{
          display: 'flex',
          gap: 8,
          alignItems: 'center',
          padding: 8,
          border: '1px dashed #ddd',
          borderRadius: 8,
          background: '#f0f5ff'
        }}
      >
        <strong style={{ fontSize: 13 }}>Extract Node from Text:</strong>
        <input
          placeholder="Paste highlighted text here..."
          value={highlightedText}
          onChange={(e) => setHighlightedText(e.target.value)}
          style={{
            flex: 1,
            padding: '6px 10px',
            border: '1px solid #adc6ff',
            borderRadius: 6,
            fontSize: 12
          }}
        />
        <button
          onClick={() => highlightedText.trim() && extractNodeFromText(highlightedText.trim())}
          disabled={!highlightedText.trim()}
          style={{
            padding: '6px 12px',
            border: 'none',
            background: highlightedText.trim() ? '#1890ff' : '#d9d9d9',
            color: '#fff',
            borderRadius: 6,
            cursor: highlightedText.trim() ? 'pointer' : 'not-allowed',
            fontWeight: 600
          }}
        >
          Make Node
        </button>
      </div>

      {/* Graph */}
      <GraphCanvas
        nodes={nodes}
        edges={edges}
        onNodesPosChange={applyPositions}
        edgeMode={edgeMode}
        onCreateEdge={createEdge}
        selectedIds={selected}
        onToggleSelect={toggleSelected}
      />

      {/* Nodes + Compose controls */}
      <section>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
          <h2 style={{ margin: 0 }}>Nodes</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <button
              onClick={composeFromSelection}
              disabled={busy !== 'idle'}
              style={{ padding: '6px 10px', border: '1px solid #333', borderRadius: 6 }}
              title="Compose from selected nodes"
            >
              {busy === 'compose' ? 'Composing…' : citeMode ? 'Compose + Citations' : 'Compose Outline/Essay'}
            </button>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <input
                type="checkbox"
                checked={citeMode}
                onChange={(e) => setCiteMode(e.target.checked)}
                title="Retrieve sources for selected nodes and append References"
              />
              <span style={{ fontSize: 12 }}>Citations</span>
            </label>
            <button onClick={selectAll} style={{ padding: '4px 8px', border: '1px solid #aaa', borderRadius: 6 }}>
              Select All
            </button>
            <button onClick={selectNone} style={{ padding: '4px 8px', border: '1px solid #aaa', borderRadius: 6 }}>
              None
            </button>
            <span style={{ fontSize: 12, color: '#666' }}>
              selected {Object.values(selected).filter(Boolean).length}/{nodes.length}
            </span>
            {llmUsed !== null && (
              <span
                style={{
                  padding: '2px 6px',
                  borderRadius: 6,
                  fontSize: 12,
                  background: llmUsed ? '#e6ffed' : '#fff5f5',
                  border: `1px solid ${llmUsed ? '#52c41a' : '#ff4d4f'}`,
                  color: llmUsed ? '#237804' : '#a8071a'
                }}
              >
                LLM: {llmUsed ? 'ON' : 'OFF (fallback)'}
              </span>
            )}
          </div>
        </div>

        {nodes.length === 0 ? (
          <p style={{ color: '#777' }}>No nodes yet. Click “Extract” or use the Graph Tools to add nodes.</p>
        ) : (
          <ul>
            {nodes.map((n) => (
              <li key={n.id} style={{ marginBottom: 12, display: 'grid', gap: 6 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <input
                    type="checkbox"
                    checked={!!selected[n.id]}
                    onChange={() => toggleSelected(n.id)}
                    title="Include in composition"
                  />
                  <b>{getNodeKind(n)}</b>
                  <span style={{ color: '#999' }}>({n.id})</span>
                  {n.definition && (
                    <span style={{ fontSize: 12, color: '#666', marginLeft: 8 }}>
                      {n.definition}
                    </span>
                  )}
                  <button
                    onClick={() => citeNode(n)}
                    disabled={busy !== 'idle'}
                    style={{ marginLeft: 8, padding: '2px 8px', border: '1px solid #333', borderRadius: 6 }}
                  >
                    Cite
                  </button>
                  <button
                    onClick={() => deleteNode(n.id)}
                    style={{ padding: '2px 8px', border: '1px solid #c00', color: '#c00', borderRadius: 6 }}
                    title="Delete node (and incident edges)"
                  >
                    Delete
                  </button>
                  <button
                    onClick={(e) => {
                      setContextMenu({
                        nodeId: n.id,
                        nodeName: getNodeText(n),
                        x: e.clientX,
                        y: e.clientY
                      })
                    }}
                    style={{ padding: '2px 8px', border: '1px solid #1890ff', color: '#1890ff', borderRadius: 6 }}
                    title="More actions"
                  >
                    •••
                  </button>
                </div>

                {/* inline rename */}
                <input
                  value={getNodeText(n)}
                  onChange={(e) => updateNodeText(n.id, e.target.value)}
                  style={{ width: '100%', padding: 8, border: '1px solid #ddd', borderRadius: 8 }}
                />

                {/* Show synonyms if available */}
                {n.synonyms && n.synonyms.length > 0 && (
                  <div style={{ fontSize: 11, color: '#999', marginTop: 4 }}>
                    Synonyms: {n.synonyms.join(', ')}
                  </div>
                )}

                {/* citations */}
                {citations[n.id]?.length ? (
                  <ol>
                    {citations[n.id].map((c) => (
                      <li key={c.chunk_id}>
                        <em>{c.doc.title || c.doc.source}</em> — score {c.score.toFixed(3)}
                        <br />
                        <span style={{ color: '#555' }}>{c.text}</span>
                      </li>
                    ))}
                  </ol>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Edges */}
      <section>
        <h2>Edges</h2>
        {edges.length === 0 ? (
          <p style={{ color: '#777' }}>No edges yet. Use “Suggest Links” or enable Edge Mode and click two nodes.</p>
        ) : (
          <ul>
            {edges.map((e, i) => (
              <li key={i} style={{ display: 'grid', gap: 4, marginBottom: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  {e.from_id} → {e.to_id} <i>({getEdgeType(e)})</i>
                  <span style={{
                    fontSize: 11,
                    padding: '2px 6px',
                    borderRadius: 4,
                    background: getEdgeStatus(e) === 'ACCEPTED' ? '#e6ffed' : '#fff5f5',
                    color: getEdgeStatus(e) === 'ACCEPTED' ? '#237804' : '#d48806'
                  }}>
                    {getEdgeStatus(e)}
                  </span>
                  {e.confidence != null ? (
                    <span style={{ color: '#999' }}>conf: {e.confidence.toFixed(2)}</span>
                  ) : null}
                  <button
                    onClick={() => fetchEvidence(i, e)}
                    style={{ padding: '2px 8px', border: '1px solid #1890ff', color: '#1890ff', borderRadius: 6 }}
                    title="View evidence for this edge"
                  >
                    View Evidence
                  </button>
                  <button
                    onClick={() => deleteEdge(i)}
                    style={{ marginLeft: 'auto', padding: '2px 8px', border: '1px solid #c00', color: '#c00', borderRadius: 6 }}
                    title="Delete edge"
                  >
                    Delete
                  </button>
                </div>

                {/* Show mechanisms if available */}
                {e.mechanisms && e.mechanisms.length > 0 && (
                  <div style={{ fontSize: 12, color: '#555' }}>
                    <strong>Mechanisms:</strong> {e.mechanisms.join(', ')}
                  </div>
                )}

                {/* Show assumptions if available */}
                {e.assumptions && e.assumptions.length > 0 && (
                  <div style={{ fontSize: 12, color: '#555' }}>
                    <strong>Assumptions:</strong> {e.assumptions.join(', ')}
                  </div>
                )}

                {/* Show confounders if available */}
                {e.confounders && e.confounders.length > 0 && (
                  <div style={{ fontSize: 12, color: '#d48806' }}>
                    <strong>Potential confounders:</strong> {e.confounders.join(', ')}
                  </div>
                )}

                {e.rationale ? <div style={{ fontSize: 12, color: '#555' }}>{e.rationale}</div> : null}
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Compose result + Export */}
      <section id="compose-result">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h2>Compose Result</h2>
          <button
            onClick={downloadMarkdown}
            disabled={!essay && !outline.length}
            style={{ padding: '6px 10px', border: '1px solid #333', borderRadius: 6 }}
            title="Download outline + essay (+ refs if enabled) as Markdown"
          >
            Download .md
          </button>
        </div>

        {outline.length ? (
          <div>
            <h3>Outline</h3>
            <ol>
              {outline.map((o, i) => (
                <li key={i}>
                  <strong>{o.heading}</strong>
                  <ul>
                    {o.points.map((p, j) => (
                      <li key={j}>{p}</li>
                    ))}
                  </ul>
                </li>
              ))}
            </ol>
          </div>
        ) : null}

        {essay ? (
          <div>
            <h3>Essay (Markdown)</h3>
            <div
              style={{
                width: '100%',
                padding: 16,
                border: '1px solid #ddd',
                borderRadius: 8,
                background: '#fff'
              }}
            >
              <ReactMarkdown>{essay}</ReactMarkdown>
            </div>
          </div>
        ) : null}

        {citeMode && references.length ? (
          <div style={{ marginTop: 16 }}>
            <h3>References (retrieved)</h3>
            <ol>
              {references.map((c, idx) => (
                <li key={c.chunk_id}>
                  <strong>{c.doc.title || c.doc.source || `Source ${idx + 1}`}</strong>
                  <div style={{ color: '#555' }}>{c.text}</div>
                  <div style={{ fontSize: 12, color: '#999' }}>score {c.score.toFixed(3)}</div>
                </li>
              ))}
            </ol>
          </div>
        ) : null}
      </section>

      {/* Edge Rationale Modal */}
      {pendingEdge && (
        <>
          {/* Backdrop */}
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(0, 0, 0, 0.5)',
              zIndex: 999
            }}
            onClick={cancelEdgeModal}
          />
          {/* Modal */}
          <EdgeRationaleCard
            fromName={getNodeText(nodes.find((n) => n.id === pendingEdge.from_id) || { id: '' })}
            toName={getNodeText(nodes.find((n) => n.id === pendingEdge.to_id) || { id: '' })}
            edgeType={pendingEdge.type}
            rationale={edgeRationale}
            loading={fetchingRationale}
            onAccept={acceptEdge}
            onReject={rejectEdge}
            onClose={cancelEdgeModal}
          />
        </>
      )}

      {/* Citation Panel */}
      {showCitationPanel && (
        <CitationPanel
          evidence={currentEvidence}
          loading={fetchingEvidence}
          onPin={pinCitation}
          onClose={closeCitationPanel}
        />
      )}

      {/* Phase 4: Node Extraction Modal */}
      {showNodeExtractCard && (
        <>
          {/* Backdrop */}
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(0, 0, 0, 0.5)',
              zIndex: 999
            }}
            onClick={() => setShowNodeExtractCard(false)}
          />
          {/* Modal */}
          <NodeExtractCard
            extraction={nodeExtraction}
            loading={fetchingExtraction}
            onAccept={acceptExtractedNode}
            onMerge={mergeExtractedNode}
            onReject={rejectExtractedNode}
            onClose={() => setShowNodeExtractCard(false)}
          />
        </>
      )}

      {/* Phase 4: Node Context Menu */}
      {contextMenu && (
        <NodeContextMenu
          nodeId={contextMenu.nodeId}
          nodeName={contextMenu.nodeName}
          x={contextMenu.x}
          y={contextMenu.y}
          onFindMissingPieces={() => findMissingPieces(contextMenu.nodeId)}
          onDelete={() => deleteNode(contextMenu.nodeId)}
          onClose={() => setContextMenu(null)}
        />
      )}

      {/* Phase 4: Missing Pieces Modal */}
      {showMissingPieces && (
        <>
          {/* Backdrop */}
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(0, 0, 0, 0.5)',
              zIndex: 999
            }}
            onClick={() => setShowMissingPieces(false)}
          />
          {/* Modal */}
          <MissingPiecesModal
            nodeName={focusNodeId ? getNodeText(nodes.find((n) => n.id === focusNodeId) || { id: '' }) : ''}
            suggestions={missingPieces}
            loading={fetchingMissingPieces}
            onAcceptMediator={acceptMediator}
            onAcceptModerator={acceptModerator}
            onClose={() => setShowMissingPieces(false)}
          />
        </>
      )}

      {/* Phase 4: Graph Critique Panel */}
      {showCritique && (
        <GraphCritiquePanel
          warnings={critiqueWarnings}
          loading={fetchingCritique}
          onClose={() => setShowCritique(false)}
        />
      )}
    </main>
  )
}
