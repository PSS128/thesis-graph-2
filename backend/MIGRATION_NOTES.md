# Database Schema Migration Notes

## Changes Made (2025-10-16)

### GraphNode Model Updates
Added new fields to support the Causal Thesis Builder feature:

**New Required Fields:**
- `name` (str) - Canonical variable name (replaces informal `text`)
- `kind` (str, default="VARIABLE") - Node type: THESIS | VARIABLE | ASSUMPTION

**New Optional Fields:**
- `definition` (str) - Short definition of the variable
- `synonyms` (JSON str) - Array of synonym strings
- `measurement_ideas` (JSON str) - Array of measurement idea strings
- `citations` (JSON str) - Array of citation objects: `[{"doc":"d7","span":[1023,1101]}]`

**Deprecated (kept for backward compatibility):**
- `text` - Now optional, use `name` + `definition` instead
- `type` - Now optional, use `kind` instead

### GraphEdge Model Updates
Added new fields to support edge rationale and status tracking:

**New Required Fields:**
- `type` (str, default="CAUSES") - Edge type: CAUSES | MODERATES | MEDIATES | CONTRADICTS
- `status` (str, default="PROPOSED") - Edge status: PROPOSED | ACCEPTED | REJECTED

**New Optional Fields:**
- `mechanisms` (JSON str) - Array of mechanism strings
- `assumptions` (JSON str) - Array of assumption strings
- `confounders` (JSON str) - Array of confounder strings
- `citations` (JSON str) - Array of citation objects with support/strength

**Deprecated (kept for backward compatibility):**
- `relation` - Now optional, use `type` instead

## Migration Strategy

### For Existing Data:
1. **GraphNode**: Map `text` → `name`, `type` → `kind`
2. **GraphEdge**: Map `relation` → `type`
3. Set defaults for new fields (synonyms=null, status="ACCEPTED" for existing edges)

### For New Code:
- Use the new fields (`name`, `kind`, `type`, `status`)
- Store JSON arrays as strings (use `json.dumps()` to serialize)
- Parse JSON fields with `json.loads()` when reading

## Database Recreation Required

Since we're using SQLite without migrations, you'll need to:

```bash
# Backup existing database (optional)
cp backend/thesis_graph.db backend/thesis_graph.db.backup

# Delete old database
rm backend/thesis_graph.db

# Restart the FastAPI server to create new schema
cd backend
python -m uvicorn app.main:app --reload
```

The new schema will be created automatically on first run.

## Code Updates Needed

### 1. Update `projects.py` helper functions
- Modify `_node_to_dict()` to use new fields
- Modify `_edge_to_dict()` to use new fields
- Update save/import logic to handle both old and new formats

### 2. Frontend Updates
- Update node/edge TypeScript interfaces
- Handle new fields in GraphCanvas component
- Add UI for synonyms, mechanisms, assumptions display

### 3. API Response Updates
- Ensure all endpoints return the new schema
- Maintain backward compatibility for legacy clients
