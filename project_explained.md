# Thesis Graph Builder - Complete Architecture Guide

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Backend Architecture (FastAPI)](#2-backend-architecture-fastapi)
3. [Frontend Architecture (Next.js/React)](#3-frontend-architecture-nextjsreact)
4. [Data Models & Database](#4-data-models--database)
5. [API Endpoints Reference](#5-api-endpoints-reference)
6. [Data Flow & Integration](#6-data-flow--integration)
7. [LLM Integration](#7-llm-integration)
8. [Vector Embeddings & Retrieval](#8-vector-embeddings--retrieval)
9. [File Structure Maps](#9-file-structure-maps)
10. [Key Design Patterns](#10-key-design-patterns--best-practices)
11. [Environment Configuration](#11-environment-configuration)

---

## 1. Project Overview

**Thesis-Graph** is an LLM-assisted visual workspace for building and refining causal arguments. Users can:
- Extract claims (nodes) from text using LLM or fallback heuristics
- Suggest relationships (edges) between claims with AI-powered rationale
- Compose outlines and essays from selected subgraphs
- Cite sources using vector embeddings (FAISS + sentence-transformers)
- Collaborate and track multiple projects with automatic persistence

### Tech Stack
- **Frontend:** Next.js 15.5.4 + React 19.1.0 (TypeScript)
- **Backend:** FastAPI (Python) + SQLModel + SQLite
- **LLM Providers:** Groq (default, free tier) or OpenAI
- **Vector Database:** FAISS for semantic search + SentenceTransformers embeddings
- **PDF Processing:** pdfplumber for text extraction

### General Workflow
```
Ingest Documents → Extract Nodes → Create Edges → Analyze & Critique → Compose Essay → Export
```

---

## 2. Backend Architecture (FastAPI)

### 2.1 Directory Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app setup + CORS + router registration
│   ├── db.py                   # SQLite engine, session factory
│   ├── models/
│   │   └── store.py            # SQLModel schemas (Project, GraphNode, GraphEdge, Feedback)
│   ├── services/
│   │   ├── llm.py              # Unified LLM service (OpenAI/Groq)
│   │   └── embeddings.py       # FAISS indexing, chunking, retrieval
│   ├── routers/
│   │   ├── extract.py          # POST /extract/nodes - node extraction
│   │   ├── edges.py            # POST /edges/suggest - suggest edges
│   │   ├── node.py             # POST /node/extract - variable from text
│   │   ├── edge.py             # POST /edge/rationale, /edge/evidence
│   │   ├── graph.py            # POST /graph/missing_pieces, /graph/critique
│   │   ├── compose.py          # POST /compose - outline/essay generation
│   │   ├── ingest.py           # POST /ingest/upload - PDF upload & chunking
│   │   ├── retrieve.py         # POST /retrieve - semantic search
│   │   └── projects.py         # Project CRUD endpoints
│   └── storage/
│       ├── index.faiss         # Persisted FAISS vector index
│       └── docstore.json       # Document metadata mapping
├── recreate_db.py              # Utility to reset database
└── .env                        # API keys: GROQ_API_KEY, OPENAI_API_KEY, LLM_PROVIDER
```

### 2.2 Key Files Explained

#### `main.py` - Application Entry Point
- Initializes FastAPI app with CORS configuration
- Registers all routers (extract, edges, node, edge, graph, compose, ingest, retrieve, projects)
- Allows CORS for `localhost:3000` (frontend development)
- Exposes headers: `X-LLM-Used`, `X-Model` for frontend detection

#### `db.py` - Database Setup
- SQLite engine: `sqlite:///./thesis_graph.db`
- Uses SQLModel for ORM (combines Pydantic + SQLAlchemy)
- Provides `get_session()` dependency injection for routes

#### `models/store.py` - Data Models

**Project**
- `id` (int, primary key)
- `title` (str) - project name

**GraphNode**
- `id`, `project_id`, `node_id` (unique identifier)
- `name` (str) - canonical variable name
- `kind` (str) - "THESIS", "VARIABLE", or "ASSUMPTION"
- `definition`, `synonyms`, `measurement_ideas`, `citations` (JSON arrays)
- `x`, `y` (floats) - canvas position
- Legacy fields: `text`, `type` for backward compatibility

**GraphEdge**
- `id`, `project_id`, `from_id`, `to_id`
- `type` (str) - "CAUSES", "MODERATES", "MEDIATES", "CONTRADICTS"
- `status` (str) - "PROPOSED", "ACCEPTED", "REJECTED"
- `mechanisms`, `assumptions`, `confounders`, `citations` (JSON arrays)
- Legacy fields: `relation`, `rationale`, `confidence`

#### `services/llm.py` - LLM Integration
- **Providers:** Groq (llama-3.1-8b-instant) or OpenAI (gpt-4)
- **Key Functions:**
  - `_client()` - Returns SDK client based on `LLM_PROVIDER`
  - `chat_json()` - Calls LLM and extracts JSON response
  - `compose_outline_essay()` - High-level essay generation
- **Graceful Fallback:** Returns deterministic response if LLM unavailable

#### `services/embeddings.py` - Vector Search
- **Model:** `all-MiniLM-L6-v2` (384-dimensional embeddings)
- **Index:** FAISS IndexFlatIP (cosine similarity)
- **Functions:**
  - `add_document()` - Chunk text, embed, add to FAISS
  - `chunk_text()` - Split into 600-char chunks with 100-char overlap
  - `retrieve()` - Semantic search for top-k results

#### `routers/` - API Endpoints

**extract.py** - Node Extraction
- `POST /extract/nodes` - Extract nodes from text using LLM or fallback
- Returns: `[{id, text, type}]`

**edges.py** - Edge Suggestion
- `POST /edges/suggest` - Suggest edges between nodes
- Returns: `[{from_id, to_id, relation}]`

**node.py** - Variable Extraction
- `POST /node/extract` - Map highlighted text to canonical variable
- Returns: `{name, definition, synonyms, measurement_ideas, merge_hint}`

**edge.py** - Edge Analysis
- `POST /edge/rationale` - Generate mechanisms, assumptions, confounders
- `POST /edge/evidence` - Retrieve citations supporting/contradicting edge

**graph.py** - Graph Analysis
- `POST /graph/missing_pieces` - Suggest mediators, moderators, confounders
- `POST /graph/critique` - Validate DAG and warn on issues

**compose.py** - Essay Generation
- `POST /compose` - Generate outline + essay from selected subgraph
- Returns: `{outline: [{heading, points}], essay_md: "..."}`

**ingest.py** - Document Upload
- `POST /ingest/upload` - Upload PDF/text and queue embedding
- Background task: Extract text → chunk → embed → FAISS

**retrieve.py** - Semantic Search
- `POST /retrieve` - Search for citations using vector similarity
- Returns: `[{rank, score, chunk_id, text, doc}]`

**projects.py** - Project Management
- `GET /projects` - List all projects
- `POST /projects` - Create new project
- `GET /projects/{id}` - Load project with nodes/edges
- `POST /projects/{id}/save` - Save graph state
- `DELETE /projects/{id}` - Delete project

---

## 3. Frontend Architecture (Next.js/React)

### 3.1 Directory Structure

```
frontend/src/app/
├── page.tsx                    # Main app component (2250+ lines)
├── layout.tsx                  # Root layout wrapper
├── globals.css                 # Global styles
├── components/
│   ├── GraphCanvas.tsx         # SVG-based graph visualization
│   ├── EdgeRationaleCard.tsx   # Edge reasoning modal
│   ├── CitationPanel.tsx       # Evidence/citations sidebar
│   ├── NodeExtractCard.tsx     # Extract variable from text modal
│   ├── MissingPiecesModal.tsx  # Suggest mediators/moderators
│   ├── GraphCritiquePanel.tsx  # DAG validation warnings
│   ├── NodeContextMenu.tsx     # Right-click node menu
│   ├── FileUploadZone.tsx      # Drag-drop PDF upload
│   ├── PDFViewer.tsx           # PDF rendering with text selection
│   ├── Toast.tsx               # Notification toasts
│   ├── HelpModal.tsx           # Instructions/help dialog
│   ├── ProgressBar.tsx         # Upload progress
│   └── LoadingIndicator.tsx    # Spinner component
├── hooks/
│   └── useHistory.ts           # Undo/redo state management
└── utils/
    ├── export.ts               # PNG/JSON/Markdown export
    ├── graphLayout.ts          # Auto-layout algorithms
    └── debounce.ts             # Debounce utility
```

### 3.2 Core Component: `page.tsx`

This monolithic component (2250+ lines) manages all application state and UI.

#### State Variables
- **Graph State:** `nodes`, `edges` (with undo/redo via `useHistory`)
- **Projects:** `projectId`, `projectTitle`, `projects`, `autosave`, `dirty`
- **UI States:** `busy`, `toasts`, `showHelp`
- **Modals:** `showNodeExtractCard`, `showMissingPieces`, `showCritique`, `showCitationPanel`
- **Document Library:** `uploadedFiles`, `selectedPdfIndex`
- **Compose:** `audience`, `tone`, `words`, `outline`, `essay`, `llmUsed`

#### Key Functions

**Node Management:**
- `extract()` - POST /extract/nodes (full text)
- `extractNodeFromText()` - POST /node/extract (highlighted text)
- `addNode()` - Create node manually
- `deleteNode()` - Remove node and incident edges

**Edge Management:**
- `suggest()` - POST /edges/suggest
- `createEdge()` - POST /edge/rationale (fetch rationale)
- `acceptEdge()` / `rejectEdge()` - Modal callbacks
- `fetchEvidence()` - POST /edge/evidence (citations)

**Composition:**
- `composeFromSelection()` - POST /compose
- `composeWithCitations()` - Retrieve references for nodes

**Project Management:**
- `newProject()`, `loadProject()`, `saveProject()`
- `saveProjectSilent()` - Autosave (2-second debounce)
- `exportProject()` / `importProject()` - JSON import/export

**Document Management:**
- `upload()` - POST /ingest/upload (background embedding)
- `deleteFile()` - Remove uploaded document

**Graph Analysis:**
- `findMissingPieces()` - POST /graph/missing_pieces
- `critiqueGraph()` - POST /graph/critique
- `handleAutoLayout()` - Apply hierarchical/force/circular/grid layout

**Export:**
- `handleExportAsPNG()` - html2canvas → download
- `handleExportAsJSON()` - Graph data export
- `handleExportAsMarkdown()` - Formatted document

---

## 4. Data Models & Database

### 4.1 Schema Evolution

**Old Schema (Legacy):**
```json
{
  "nodes": [{"id": "n1", "text": "...", "type": "THESIS|CLAIM"}],
  "edges": [{"from_id": "n1", "to_id": "n2", "relation": "SUPPORTS|CONTRADICTS"}]
}
```

**New Schema (Current):**
```json
{
  "nodes": [{
    "id": "n1",
    "name": "Variable Name",
    "kind": "THESIS|VARIABLE|ASSUMPTION",
    "definition": "...",
    "synonyms": ["..."],
    "measurement_ideas": ["..."],
    "citations": [{"doc": "...", "span": [0, 100]}]
  }],
  "edges": [{
    "from_id": "n1",
    "to_id": "n2",
    "type": "CAUSES|MODERATES|MEDIATES|CONTRADICTS",
    "status": "PROPOSED|ACCEPTED|REJECTED",
    "mechanisms": ["..."],
    "assumptions": ["..."],
    "confounders": ["..."],
    "citations": [...]
  }]
}
```

**Backward Compatibility:**
- Models store both old and new fields
- Frontend normalizes on read: `getNodeText(n) = n.name || n.text`

### 4.2 Data Persistence

**SQLite Database:** `backend/thesis_graph.db`
- Stores projects, nodes, edges, feedback
- Initialized via `init_db()` on first run

**FAISS Vector Index:** `backend/storage/index.faiss`
- Sentence embeddings for semantic search
- `all-MiniLM-L6-v2` model (384 dimensions)
- IndexFlatIP (cosine similarity)

**Document Metadata:** `backend/storage/docstore.json`
```json
{
  "chunk_id": {
    "doc_id": "hash123",
    "doc_title": "Paper.pdf",
    "source": "Paper.pdf",
    "text": "chunk content"
  }
}
```

---

## 5. API Endpoints Reference

### Node Extraction
**POST /extract/nodes**
```json
Request: {"text": "...", "thesis": "...", "max_items": 8}
Response: [{"id": "n1", "text": "...", "type": "THESIS|CLAIM"}]
```

**POST /node/extract**
```json
Request: {"text": "highlighted text", "existing_names": ["var1"]}
Response: {
  "name": "Variable Name",
  "definition": "...",
  "synonyms": ["..."],
  "measurement_ideas": ["..."],
  "merge_hint": {"existing_name": "var1", "similarity": 0.95}
}
```

### Edge Analysis
**POST /edges/suggest**
```json
Request: {"nodes": [...], "max_edges": 12}
Response: [{"from_id": "n1", "to_id": "n2", "relation": "SUPPORTS"}]
```

**POST /edge/rationale**
```json
Request: {"a_name": "Variable A", "b_name": "Variable B"}
Response: {
  "mechanisms": ["..."],
  "assumptions": ["..."],
  "likely_confounders": ["..."],
  "prior_evidence_types": ["observational", "experimental"]
}
```

**POST /edge/evidence**
```json
Request: {"a_name": "...", "b_name": "...", "mechanisms": [...], "top_k": 3}
Response: [{
  "title": "Paper Title",
  "quote": "Relevant excerpt",
  "supports": "supports|contradicts",
  "strength": 0.85
}]
```

### Graph Analysis
**POST /graph/missing_pieces**
```json
Request: {"focus_node_id": "N1", "nodes": [...], "edges": [...]}
Response: {
  "mediators": [{"name": "...", "definition": "...", "rationale": "..."}],
  "moderators": [...],
  "measurements": [{"approach": "...", "pros": [...], "cons": [...]}],
  "confounders": [...]
}
```

**POST /graph/critique**
```json
Request: {"nodes": [...], "edges": [...]}
Response: {
  "warnings": [{
    "node_or_edge_id": "N1",
    "label": "Orphan node",
    "fix_suggestion": "Connect or remove"
  }]
}
```

### Composition
**POST /compose**
```json
Request: {
  "thesis": "...",
  "nodes": [...],
  "edges": [...],
  "words": 700,
  "audience": "academic|general|policy|technical",
  "tone": "neutral|critical|persuasive|explanatory|skeptical",
  "mode": "outline|essay|both"
}
Response: {
  "outline": [{"heading": "...", "points": ["..."]}],
  "essay_md": "# Markdown essay"
}
Headers: X-LLM-Used: "1", X-Model: "groq:llama-3.1-8b-instant"
```

### Document Ingestion
**POST /ingest/upload**
```
Request: multipart/form-data (file, title)
Response: {
  "ok": true,
  "doc_id": "hash123",
  "page_count": 42,
  "status": "processing"
}
```

### Semantic Search
**POST /retrieve**
```json
Request: {"query": "search text", "top_k": 3}
Response: [{
  "rank": 1,
  "score": 0.876,
  "chunk_id": "hash_chunk",
  "text": "relevant passage",
  "doc": {"id": "doc_hash", "title": "Paper.pdf"}
}]
```

### Project Management
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/projects` | List all projects |
| POST | `/projects?title=X` | Create new project |
| GET | `/projects/{id}` | Load project with graph |
| POST | `/projects/{id}/save` | Save nodes/edges |
| PATCH | `/projects/{id}` | Rename project |
| DELETE | `/projects/{id}` | Delete project |
| GET | `/projects/{id}/export` | Export as JSON |
| POST | `/projects/import` | Import JSON |

---

## 6. Data Flow & Integration

### 6.1 Full Workflow

```
[User Input Text]
     ↓
[1] Extract Nodes (LLM or fallback)
     ↓ POST /extract/nodes
[Backend] extract.py / chat_json()
     ↓
[Frontend] Receive nodes → render in GraphCanvas
     ↓
[2] Optional: Upload PDFs
     ↓ POST /ingest/upload (background)
[Backend] pdfplumber → chunk → embed → FAISS
     ↓
[3] Suggest Edges
     ↓ POST /edges/suggest
[Backend] edges.py / chat_json()
     ↓
[4] Interactive Graph Editing
     - Manual node/edge manipulation
     - Drag nodes, create connections
     - Right-click context menu
     ↓
[5] Cite Nodes (Semantic Search)
     ↓ POST /retrieve
[Backend] Query embeddings → FAISS search
     ↓
[6] Create Edges with Rationale
     ↓ POST /edge/rationale
[Backend] LLM reasoning about mechanisms
     ↓ POST /edge/evidence
[Backend] Semantic search for citations
     ↓
[7] Select Subgraph & Compose
     ↓ POST /compose
[Backend] LLM-powered outline/essay
     ↓
[Frontend] Display & export as .md or .json
```

### 6.2 Autosave Flow

```javascript
useEffect(() => {
  if (!autosave || !projectId || !dirty) return;

  const timer = setTimeout(() => {
    saveProjectSilent() // POST /projects/{id}/save
    setDirty(false)
  }, 2000) // 2-second debounce

  return () => clearTimeout(timer)
}, [autosave, projectId, dirty, nodes, edges])
```

---

## 7. LLM Integration

### 7.1 Configuration

```bash
# .env
LLM_PROVIDER=groq              # or "openai"
LLM_MODEL=llama-3.1-8b-instant # or "gpt-4"
GROQ_API_KEY=gsk_...
OPENAI_API_KEY=sk-...
```

### 7.2 Key Functions (`llm.py`)

**`chat_json(system, user, temperature, max_tokens)`**
- Calls provider-specific API
- Extracts JSON from response (handles edge cases)
- Returns `(data, used_llm)` tuple
- Gracefully returns `None` if LLM fails

**Fallback Strategy:**
```python
data = chat_json(system, user)
if not data:
    return _deterministic_fallback()  # No randomness
```

### 7.3 Prompt Design

**System Prompt:**
```python
system = "You are an expert. Return STRICT JSON ONLY. No prose."
```

**User Prompt:**
```python
user = f"""
Input: {data}
Instructions: Be concise, follow exact format
Return JSON: {{"key": "value"}}
"""
```

---

## 8. Vector Embeddings & Retrieval

### 8.1 Architecture

**Model:** `all-MiniLM-L6-v2` (SentenceTransformers)
- 384-dimensional embeddings
- Fast CPU inference
- Good semantic understanding

**Index:** FAISS IndexFlatIP (cosine similarity)

### 8.2 Document Ingestion

```
1. POST /ingest/upload
   └─ Extract text with pdfplumber
   └─ Return doc_id immediately
   └─ Queue background task

2. Background: add_document()
   ├─ chunk_text(text, size=600, overlap=100)
   ├─ Embed chunks with SentenceTransformer
   ├─ Add to FAISS index
   └─ Save docstore.json
```

**Chunking:**
- Size: 600 characters
- Overlap: 100 characters (context preservation)

### 8.3 Retrieval

```
POST /retrieve {"query": "...", "top_k": 3}
  ↓
[Backend] Embed query → FAISS search
  ↓
Return top_k chunks with metadata
```

---

## 9. File Structure Maps

### 9.1 Backend

```
backend/app/
├── main.py                     (47 lines)
├── db.py                       (12 lines)
├── models/store.py             (78 lines - 4 models)
├── services/
│   ├── llm.py                  (250+ lines)
│   └── embeddings.py           (200+ lines)
├── routers/
│   ├── extract.py              (165 lines)
│   ├── edges.py                (147 lines)
│   ├── node.py                 (150+ lines)
│   ├── edge.py                 (100+ lines)
│   ├── graph.py                (200+ lines)
│   ├── compose.py              (100 lines)
│   ├── ingest.py               (66 lines)
│   ├── retrieve.py             (15 lines)
│   └── projects.py             (250+ lines)
└── storage/
    ├── index.faiss
    └── docstore.json
```

### 9.2 Frontend

```
frontend/src/app/
├── page.tsx                    (2250 lines - main component)
├── components/
│   ├── GraphCanvas.tsx         (1000+ lines)
│   ├── EdgeRationaleCard.tsx
│   ├── CitationPanel.tsx
│   ├── NodeExtractCard.tsx
│   ├── MissingPiecesModal.tsx
│   ├── GraphCritiquePanel.tsx
│   ├── HelpModal.tsx
│   └── [other components]
├── hooks/useHistory.ts
└── utils/
    ├── export.ts
    ├── graphLayout.ts
    └── debounce.ts
```

---

## 10. Key Design Patterns & Best Practices

### 10.1 Graceful Degradation
- Every LLM endpoint has deterministic fallback
- No crashes when LLM unavailable
- Frontend detects via `X-LLM-Used` header

### 10.2 Backward Compatibility
- Store both old and new schema fields
- Normalize on read: `getNodeText(n) = n.name || n.text`
- Map legacy types: "CLAIM" → "VARIABLE", "SUPPORTS" → "CAUSES"

### 10.3 Response Normalization
```typescript
function normalizeNodes(d: any): NodeT[] {
  return Array.isArray(d) ? d : d?.nodes ?? []
}
```

### 10.4 Undo/Redo
```typescript
const { state, set, undo, redo } = useHistory({ nodes, edges })
// Automatic history tracking on set()
```

### 10.5 Toast Notifications
```typescript
showToast('success', 'Saved!', 3000)
// Queue-based, auto-dismissing
```

---

## 11. Environment Configuration

### Backend `.env`
```bash
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
GROQ_API_KEY=gsk_...
OPENAI_API_KEY=sk-...
```

### Frontend `.env.local`
```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

---

## 12. Deployment

### Development
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev  # http://localhost:3000
```

### Production Notes
1. **Database:** Consider PostgreSQL for multi-user
2. **Vector Index:** Cloud storage for distributed setup
3. **CORS:** Update `allow_origins` for production domain
4. **LLM Costs:** Monitor Groq/OpenAI usage
5. **Background Tasks:** Use Celery/RQ for distributed queues

---

## Summary

**Thesis-Graph** combines:
1. **FastAPI Backend** - LLM reasoning, vector retrieval, persistence
2. **React Frontend** - Interactive graph visualization
3. **LLM Integration** - Flexible providers with graceful fallbacks
4. **Vector Search** - Semantic citations via FAISS
5. **Project Management** - Multi-project support with autosave

The architecture prioritizes **usability** (no LLM crashes), **flexibility** (pluggable providers), and **backward compatibility** (legacy schema support).
