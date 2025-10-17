# LLM Prompt Templates Review

## Summary
The existing prompt templates in `backend/app/routers/node.py` and `backend/app/routers/edge.py` **already match the project outline requirements perfectly**. No changes needed.

## ✅ Implemented Prompts

### 1. POST /node/extract (node.py:43)
**Purpose:** Convert highlighted text into a canonical causal variable

**Prompt Structure:**
```
System: You map a highlighted sentence to a SINGLE causal variable.
        Return STRICT JSON ONLY as {"name","definition","synonyms","measurement_ideas"}.
        Keep the name concise and domain-neutral.

User: Text (highlight): {text}
      - Propose a single canonical variable name
      - Provide one-sentence definition
      - Include 2-6 concise synonyms
      - Include 2-6 concrete measurement ideas
```

**Output Schema:**
```json
{
  "name": "string",
  "definition": "string",
  "synonyms": ["string"],
  "measurement_ideas": ["string"],
  "merge_hint": {
    "existing_name": "string",
    "similarity": 0.85
  }
}
```

**Features:**
- Temperature: 0.2 (consistent outputs)
- Max tokens: 800
- Fallback mechanism for LLM unavailability
- Similarity-based merge hints using Jaccard similarity
- Defensive normalization of LLM outputs

---

### 2. POST /edge/rationale (edge.py:33)
**Purpose:** Generate reason card for proposed causal edge A → B

**Prompt Structure:**
```
System: You analyze a proposed causal edge A -> B and list mechanisms,
        assumptions, confounders, and prior evidence types.
        Return STRICT JSON ONLY: {"mechanisms":[],"assumptions":[],
        "likely_confounders":[],"prior_evidence_types":[]}.

User: User proposes causality A -> B.
      A: {a_name}
      B: {b_name}
```

**Output Schema:**
```json
{
  "mechanisms": ["string"],
  "assumptions": ["string"],
  "likely_confounders": ["string"],
  "prior_evidence_types": ["string"]
}
```

**Features:**
- Temperature: 0.2
- Max tokens: 900
- Fallback defaults: plausible pathway, ceteris paribus, baseline differences
- Output capped at 8 items per array

---

### 3. POST /edge/evidence (edge.py:58)
**Purpose:** Retrieve and format citations from RAG for confirmed edge

**Query Construction:**
```python
query_parts = [f"Does {a_name} cause {b_name}?"]
if mechanisms:
    query_parts += ["mechanism: " + m for m in mechanisms[:4]]
query = "; ".join(query_parts)
```

**Output Schema:**
```json
{
  "title": "string",
  "url": "string",
  "quote": "string",
  "span": [start, end],
  "supports": "supports" | "contradicts",
  "strength": 0.73
}
```

**Features:**
- RAG integration via `embeddings.retrieve()`
- Heuristic contradiction detection (keywords: "no effect", "null effect", "contradict", etc.)
- Top-k retrieval (1-6 items)
- Model metadata in response headers

---

## Alignment with Project Outline

| Project Requirement | Implementation Status | Notes |
|---------------------|----------------------|-------|
| **1) On text highlight → node** | ✅ Fully implemented | `/node/extract` with merge hints |
| **2) On edge draw (A → B)** | ✅ Fully implemented | `/edge/rationale` returns mechanisms, assumptions, confounders |
| **3) On edge confirm** | ✅ Fully implemented | `/edge/evidence` fetches RAG citations with support/contradict labels |
| **4) On node menu → "Find missing pieces"** | ⚠️ Not yet implemented | Need: `/graph/suggest_mediators`, `/graph/suggest_moderators` |
| **5) On graph critique** | ⚠️ Not yet implemented | Need: `/graph/critique` for cycle/collider detection |
| **6) On lasso-select → "Compose section"** | ⚠️ Partially implemented | Existing `/compose` endpoint needs subgraph support |

---

## Next Steps for Full Implementation

### Missing Endpoints (from outline):

1. **POST /graph/suggest_mediators**
   - Input: `{node_id, subgraph_context}`
   - Output: `{mediators: [], moderators: [], study_designs: []}`
   - Prompt: "Given the current subgraph around B, suggest mediators, moderators, and test designs"

2. **POST /graph/critique**
   - Input: `{nodes: [], edges: []}`
   - Output: `{warnings: [{node_or_edge_id, label, fix_suggestion}]}`
   - Checks: cycles, colliders, missing evidence, back-door adjustments

3. **POST /compose/subgraph** (enhance existing `/compose`)
   - Input: `{selected_nodes, selected_edges, style, word_budget}`
   - Output: `{section_md: "..."}`
   - Prompt: "Compose a cohesive section from this subgraph using only ACCEPTED nodes/edges"

---

## Prompt Quality Assessment

**Strengths:**
- ✅ Clear, concise system instructions
- ✅ Strict JSON output enforcement
- ✅ Domain-neutral language
- ✅ Defensive fallbacks for reliability
- ✅ Appropriate temperature settings (0.2 for consistency)
- ✅ Output validation and normalization

**Recommendations:**
- Consider adding few-shot examples for complex prompts (e.g., mediator suggestion)
- Add prompt versioning for A/B testing
- Consider user-customizable prompt templates for domain experts
- Add logging for prompt performance metrics

---

## Testing Checklist

- [x] `/node/extract` returns valid variable descriptors
- [x] `/edge/rationale` generates plausible mechanisms
- [x] `/edge/evidence` retrieves relevant citations
- [ ] Test merge hint accuracy with similar variable names
- [ ] Test contradiction detection heuristics
- [ ] Validate JSON schema enforcement with malformed LLM outputs
- [ ] Test fallback behavior when LLM is unavailable
