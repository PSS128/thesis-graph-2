# Integration Guide: Advanced Prompts → Existing Routers

## Quick Integration

### Option 1: Drop-in Replacement (Minimal Changes)

Update `backend/app/routers/node.py`:

```python
# Add import at top
from ..prompts.node_extraction import get_extraction_prompts

@router.post("/extract", response_model=ExtractVariableOut)
def extract_variable(req: ExtractVariableIn) -> ExtractVariableOut:
    # Replace the old prompt generation with:
    system, user = get_extraction_prompts(
        text=req.text,
        use_advanced=True,  # or False for basic
        include_examples=True  # or False to save tokens
    )

    # Rest of the function stays the same
    data: Optional[Dict[str, Any]] = chat_json(system, user, temperature=0.2, max_tokens=1200)
    # ... existing code
```

Update `backend/app/routers/edge.py`:

```python
# Add import at top
from ..prompts.edge_rationale import get_rationale_prompts

@router.post("/rationale", response_model=RationaleOut)
def edge_rationale(req: RationaleIn) -> RationaleOut:
    # Replace the old prompt generation with:
    system, user = get_rationale_prompts(
        a_name=req.a_name,
        b_name=req.b_name,
        use_advanced=True,
        include_examples=True
    )

    # Rest stays the same
    data: Optional[Dict[str, Any]] = chat_json(system, user, temperature=0.2, max_tokens=1500)
    # ... existing code
```

**Done!** This gives you advanced prompts without changing the API contract.

---

## Option 2: Full Integration with Context (Recommended)

### Step 1: Extend Input Schemas

Update `backend/app/routers/node.py`:

```python
class ExtractVariableIn(BaseModel):
    text: str = Field(..., description="Highlighted text from PDF/web page")
    source_ref: Optional[str] = Field(None, description="Opaque source reference")
    existing_names: Optional[List[str]] = Field(None, description="Known node names for merge hints")

    # NEW FIELDS for advanced prompts
    domain: Optional[str] = Field(None, description="Domain: economics, psychology, medicine, policy")
    thesis: Optional[str] = Field(None, description="Main thesis statement for context")
    use_advanced: bool = Field(True, description="Use advanced prompt template")
    include_examples: bool = Field(True, description="Include few-shot examples")
```

Update `backend/app/routers/edge.py`:

```python
class RationaleIn(BaseModel):
    a_name: str = Field(..., description="Source variable name (A)")
    b_name: str = Field(..., description="Target variable name (B)")

    # NEW FIELDS for advanced prompts
    domain: Optional[str] = Field(None, description="Domain for specialized prompts")
    edge_type: str = Field("CAUSES", description="CAUSES, MODERATES, MEDIATES, CONTRADICTS")
    existing_confounders: Optional[List[str]] = Field(None, description="Already-identified confounders")
    a_definition: Optional[str] = Field(None, description="Definition of variable A")
    b_definition: Optional[str] = Field(None, description="Definition of variable B")
    use_advanced: bool = Field(True, description="Use advanced prompt template")
    include_examples: bool = Field(True, description="Include few-shot examples")
```

### Step 2: Update Route Handlers

`backend/app/routers/node.py`:

```python
from ..prompts.node_extraction import get_extraction_prompts, NodeExtractionPrompts

@router.post("/extract", response_model=ExtractVariableOut)
def extract_variable(req: ExtractVariableIn) -> ExtractVariableOut:
    """
    Convert a highlighted sentence into a canonical causal variable descriptor.
    Now supports advanced prompts with domain awareness and context integration.
    """

    # Generate prompts using new advanced templates
    system, user = get_extraction_prompts(
        text=req.text,
        domain=req.domain,
        existing_nodes=req.existing_names,
        thesis=req.thesis,
        use_advanced=req.use_advanced,
        include_examples=req.include_examples
    )

    # Adjust max_tokens for advanced prompts
    max_tokens = 1200 if req.use_advanced else 800

    data: Optional[Dict[str, Any]] = chat_json(system, user, temperature=0.2, max_tokens=max_tokens)

    # Guard: produce fallback if model is unavailable
    if not data or not isinstance(data, dict):
        base = ExtractVariableOut(
            **NodeExtractionPrompts.get_fallback_response()
        )
        return _with_merge_hint(base, req.existing_names)

    # Normalize fields (now including new fields from advanced schema)
    name = (str(data.get("name") or "").strip()) or "Candidate Variable"
    definition = (str(data.get("definition") or "").strip()) or "A concise causal factor."
    synonyms = [str(s).strip() for s in (data.get("synonyms") or []) if str(s).strip()]
    measurement = [str(m).strip() for m in (data.get("measurement_ideas") or []) if str(m).strip()]

    # NEW: Extract additional fields from advanced prompts
    theoretical_role = data.get("theoretical_role")
    level_of_analysis = data.get("level_of_analysis")
    temporal_scope = data.get("temporal_scope")
    similar_to = data.get("similar_to_existing")

    out = ExtractVariableOut(
        name=name,
        definition=definition,
        synonyms=synonyms[:8],
        measurement_ideas=measurement[:8],
    )

    # Optional: Store metadata for advanced features
    # (You might want to extend ExtractVariableOut or store in DB)
    if theoretical_role:
        out.metadata = {
            "theoretical_role": theoretical_role,
            "level_of_analysis": level_of_analysis,
            "temporal_scope": temporal_scope,
            "similar_to_existing": similar_to
        }

    return _with_merge_hint(out, req.existing_names)
```

`backend/app/routers/edge.py`:

```python
from ..prompts.edge_rationale import get_rationale_prompts, EdgeRationalePrompts

@router.post("/rationale", response_model=RationaleOut)
def edge_rationale(req: RationaleIn) -> RationaleOut:
    """
    On draw A -> B, return a comprehensive reason card with causal inference framework.
    """

    # Generate prompts using advanced templates
    system, user = get_rationale_prompts(
        a_name=req.a_name,
        b_name=req.b_name,
        domain=req.domain,
        edge_type=req.edge_type,
        existing_confounders=req.existing_confounders,
        a_definition=req.a_definition,
        b_definition=req.b_definition,
        use_advanced=req.use_advanced,
        include_examples=req.include_examples
    )

    # Adjust max_tokens for advanced prompts
    max_tokens = 1500 if req.use_advanced else 900

    data: Optional[Dict[str, Any]] = chat_json(system, user, temperature=0.2, max_tokens=max_tokens)

    if not data:
        return RationaleOut(
            **EdgeRationalePrompts.get_fallback_response()
        )

    # Standard fields
    mechanisms = [s for s in (data.get("mechanisms") or []) if str(s).strip()][:8]
    assumptions = [s for s in (data.get("assumptions") or []) if str(s).strip()][:8]
    confounders = [s for s in (data.get("likely_confounders") or []) if str(s).strip()][:8]
    evidence = [s for s in (data.get("prior_evidence_types") or []) if str(s).strip()][:8]

    # NEW: Extract advanced fields
    heterogeneity = [s for s in (data.get("effect_heterogeneity") or []) if str(s).strip()][:6]
    predictions = [s for s in (data.get("testable_predictions") or []) if str(s).strip()][:6]

    return RationaleOut(
        mechanisms=mechanisms,
        assumptions=assumptions,
        likely_confounders=confounders,
        prior_evidence_types=evidence,
        # Optional: Add these to RationaleOut schema
        # effect_heterogeneity=heterogeneity,
        # testable_predictions=predictions
    )
```

### Step 3: Extend Response Models (Optional)

If you want to return the new fields to the frontend:

```python
class ExtractVariableOut(BaseModel):
    name: str
    definition: str
    synonyms: List[str] = []
    measurement_ideas: List[str] = []
    merge_hint: Optional[MergeHint] = None

    # NEW: Advanced fields
    theoretical_role: Optional[str] = None
    level_of_analysis: Optional[str] = None
    temporal_scope: Optional[str] = None
    similar_to_existing: Optional[str] = None


class RationaleOut(BaseModel):
    mechanisms: List[str] = []
    assumptions: List[str] = []
    likely_confounders: List[str] = []
    prior_evidence_types: List[str] = []

    # NEW: Advanced fields
    effect_heterogeneity: List[str] = []
    testable_predictions: List[str] = []
```

---

## Option 3: Environment-Based Toggle

Use environment variables to control which template to use:

`.env`:
```bash
USE_ADVANCED_PROMPTS=true
INCLUDE_PROMPT_EXAMPLES=true
DEFAULT_DOMAIN=psychology
```

`backend/app/routers/node.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

USE_ADVANCED = os.getenv("USE_ADVANCED_PROMPTS", "true").lower() == "true"
INCLUDE_EXAMPLES = os.getenv("INCLUDE_PROMPT_EXAMPLES", "true").lower() == "true"
DEFAULT_DOMAIN = os.getenv("DEFAULT_DOMAIN")

@router.post("/extract", response_model=ExtractVariableOut)
def extract_variable(req: ExtractVariableIn) -> ExtractVariableOut:
    system, user = get_extraction_prompts(
        text=req.text,
        domain=req.domain or DEFAULT_DOMAIN,
        existing_nodes=req.existing_names,
        thesis=req.thesis,
        use_advanced=USE_ADVANCED,
        include_examples=INCLUDE_EXAMPLES
    )
    # ... rest of function
```

---

## Testing the Integration

### 1. Test Basic → Advanced Migration

```python
# Test script
import requests

# Before (works with old endpoint)
response = requests.post("http://localhost:8000/node/extract", json={
    "text": "Employees report less burnout with 4-day weeks"
})
print(response.json())

# After (with new advanced features)
response = requests.post("http://localhost:8000/node/extract", json={
    "text": "Employees report less burnout with 4-day weeks",
    "domain": "psychology",
    "thesis": "4-day workweeks improve productivity",
    "use_advanced": True,
    "include_examples": True
})
print(response.json())
```

### 2. Compare Output Quality

```bash
# Run demo to see difference
cd backend
python ADVANCED_PROMPTS_DEMO.py
```

### 3. Benchmark Performance

```python
import time

# Basic template
start = time.time()
response = extract_variable(ExtractVariableIn(
    text="...", use_advanced=False, include_examples=False
))
print(f"Basic: {time.time() - start:.2f}s")

# Advanced template
start = time.time()
response = extract_variable(ExtractVariableIn(
    text="...", use_advanced=True, include_examples=True, domain="psychology"
))
print(f"Advanced: {time.time() - start:.2f}s")
```

---

## Frontend Integration

Update `frontend/src/app/page.tsx` to pass domain context:

```typescript
// Add domain state
const [domain, setDomain] = useState<string>('psychology')

// Update extract function
const extract = async () => {
  const res = await fetch(`${API}/node/extract`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: input,
      thesis: thesis || null,
      domain: domain,  // NEW
      existing_names: nodes.map(n => n.name),  // NEW
      use_advanced: true,  // NEW
      include_examples: false  // Set false to save tokens
    })
  })
  // ... rest
}

// Add domain selector UI
<select value={domain} onChange={(e) => setDomain(e.target.value)}>
  <option value="economics">Economics</option>
  <option value="psychology">Psychology</option>
  <option value="medicine">Medicine</option>
  <option value="policy">Policy</option>
  <option value="">General</option>
</select>
```

---

## Migration Checklist

- [ ] Install new prompt modules (`backend/app/prompts/`)
- [ ] Update imports in `node.py` and `edge.py`
- [ ] Test with basic template first (set `use_advanced=False`)
- [ ] Extend input schemas with optional fields
- [ ] Update route handlers to use new prompt functions
- [ ] Test output quality with advanced templates
- [ ] Update response models to include new fields (optional)
- [ ] Update frontend to pass domain/context (optional)
- [ ] Configure environment variables (optional)
- [ ] Benchmark token usage and latency
- [ ] Update documentation
- [ ] Deploy to production

---

## Rollback Plan

If you need to revert:

```python
# In node.py and edge.py, replace:
system, user = get_extraction_prompts(...)

# With original code:
system = (
    "You map a highlighted sentence to a SINGLE causal variable. "
    "Return STRICT JSON ONLY as {\"name\",\"definition\",\"synonyms\",\"measurement_ideas\"}. "
    "Keep the name concise and domain-neutral."
)
# ... original user prompt
```

Or use:
```python
system, user = get_extraction_prompts(text, use_advanced=False, include_examples=False)
```

---

## Performance Tuning

**Token Usage:**
- Basic, no examples: ~300 tokens/call
- Advanced, no examples: ~1,200 tokens/call
- Advanced, with examples: ~2,000 tokens/call

**Recommendations:**
1. **Development**: `use_advanced=False, include_examples=False`
2. **Production**: `use_advanced=True, include_examples=False`
3. **Research**: `use_advanced=True, include_examples=True`

**Cost Optimization:**
```python
# Use advanced only for complex variables
if is_complex_variable(text):
    use_advanced = True
else:
    use_advanced = False
```

---

## Summary

You now have **three integration options**:

1. **Drop-in**: Minimal changes, instant upgrade
2. **Full**: Extended API with domain/context support
3. **Environment**: Toggle via config without code changes

**Recommended path**: Start with **Drop-in**, test quality, then migrate to **Full** for production.
