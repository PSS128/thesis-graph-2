# Advanced Prompt Templates

This package contains sophisticated, research-grade prompt templates for causal graph construction.

## Features

### Node Extraction (`node_extraction.py`)
- **Domain-aware extraction**: Specialized prompts for economics, psychology, medicine, policy
- **Context integration**: Uses existing nodes and thesis statement to avoid duplicates
- **Quality criteria**: Enforces specificity, measurability, and theoretical grounding
- **Comprehensive operationalization**: 4-8 concrete measurement ideas per variable
- **Few-shot examples**: Optional in-context learning
- **Extended schema**: Includes `theoretical_role`, `level_of_analysis`, `temporal_scope`

### Edge Rationale (`edge_rationale.py`)
- **Causal inference framework**: Theory-driven mechanism identification
- **Assumption enumeration**: Explicit listing of identification assumptions (SUTVA, no reverse causality, etc.)
- **Systematic confounder detection**: Categorized and prioritized by severity
- **Evidence hierarchy**: Suggests appropriate study designs (RCT, quasi-experiments, IV, etc.)
- **Effect heterogeneity**: Identifies subgroups with differential effects
- **Testable predictions**: Proposes falsification tests and mediator checks
- **Multiple relationship types**: Supports CAUSES, MODERATES, MEDIATES, CONTRADICTS

## Usage

### Basic (Original)

```python
from app.prompts.node_extraction import NodeExtractionPrompts

system = NodeExtractionPrompts.get_basic_system()
user = NodeExtractionPrompts.get_user_prompt("Text to extract from", include_examples=False)
```

### Advanced with Context

```python
from app.prompts.node_extraction import get_extraction_prompts

system, user = get_extraction_prompts(
    text="Studies show that employees who work four days a week report less burnout.",
    domain="psychology",  # Optional: "economics", "medicine", "policy"
    existing_nodes=["Work Hours", "Productivity", "Job Satisfaction"],
    thesis="A 4-day workweek increases worker productivity",
    use_advanced=True,
    include_examples=True
)

# Use with your LLM
response = chat_json(system, user, temperature=0.2, max_tokens=1200)
```

### Edge Rationale

```python
from app.prompts.edge_rationale import get_rationale_prompts

system, user = get_rationale_prompts(
    a_name="Exercise Frequency",
    b_name="Cognitive Function",
    domain="medicine",
    edge_type="CAUSES",  # or "MODERATES", "MEDIATES", "CONTRADICTS"
    existing_confounders=["Age", "Education"],
    a_definition="Weekly hours of moderate-intensity aerobic activity",
    b_definition="Executive function measured via Stroop task performance",
    use_advanced=True,
    include_examples=True
)

response = chat_json(system, user, temperature=0.2, max_tokens=1500)
```

## Output Schema

### Node Extraction (Advanced)

```json
{
  "name": "Work-Related Burnout",
  "definition": "Psychological exhaustion from chronic workplace stressors...",
  "synonyms": ["job burnout", "emotional exhaustion", "~compassion fatigue"],
  "measurement_ideas": [
    "Maslach Burnout Inventory (MBI) - 22-item scale (interval)",
    "Self-reported sick leave days (count data)",
    "Cortisol levels via hair samples (biomarker)"
  ],
  "theoretical_role": "mediator",
  "level_of_analysis": "individual",
  "temporal_scope": "chronic",
  "similar_to_existing": "Workplace Stress"
}
```

### Edge Rationale (Advanced)

```json
{
  "mechanisms": [
    "Increased cerebral blood flow delivers oxygen to prefrontal cortex",
    "BDNF production enhances neuroplasticity in hippocampus"
  ],
  "assumptions": [
    "Temporal precedence: Exercise before cognitive assessment",
    "No reverse causality: Cognition does not determine exercise",
    "SUTVA: No spillover between participants"
  ],
  "likely_confounders": [
    "[CRITICAL] Baseline cognitive ability - affects both exercise and cognition",
    "[MODERATE] Socioeconomic status - access and resources"
  ],
  "prior_evidence_types": [
    "RCT: Randomize to exercise vs control for 6 months",
    "Mendelian randomization: Genetic variants as IV"
  ],
  "effect_heterogeneity": [
    "Stronger for older adults (60+) due to age-related decline",
    "Null for severe cognitive impairment (floor effects)"
  ],
  "testable_predictions": [
    "Dose-response: More exercise → larger gains",
    "Temporal: Gains emerge after 3-6 months"
  ]
}
```

## Integration with Routers

### Update `node.py`

```python
from ..prompts.node_extraction import get_extraction_prompts

@router.post("/extract", response_model=ExtractVariableOut)
def extract_variable(req: ExtractVariableIn) -> ExtractVariableOut:
    # Get advanced prompts with context
    system, user = get_extraction_prompts(
        text=req.text,
        domain=req.domain,  # Add to ExtractVariableIn
        existing_nodes=req.existing_names,
        thesis=req.thesis,  # Add to ExtractVariableIn
        use_advanced=True,
        include_examples=True
    )

    data = chat_json(system, user, temperature=0.2, max_tokens=1200)
    # ... process response
```

### Update `edge.py`

```python
from ..prompts.edge_rationale import get_rationale_prompts

@router.post("/rationale", response_model=RationaleOut)
def edge_rationale(req: RationaleIn) -> RationaleOut:
    system, user = get_rationale_prompts(
        a_name=req.a_name,
        b_name=req.b_name,
        domain=req.domain,  # Add to RationaleIn
        edge_type=req.edge_type,  # Add to RationaleIn
        a_definition=req.a_definition,  # Add to RationaleIn
        b_definition=req.b_definition,  # Add to RationaleIn
        use_advanced=True
    )

    data = chat_json(system, user, temperature=0.2, max_tokens=1500)
    # ... process response
```

## Customization

### Add New Domain

Edit `node_extraction.py` and `edge_rationale.py`:

```python
domain_guidance = {
    "your_domain": """
## Domain-Specific Guidance (Your Domain):
- Use terminology specific to your field
- Reference standard frameworks or theories
- Note common measurement approaches
- Address domain-specific validity threats
"""
}
```

### Adjust Temperature & Tokens

- **Node extraction**: temperature=0.2, max_tokens=1200 (deterministic, concise)
- **Edge rationale**: temperature=0.2-0.3, max_tokens=1500 (some creativity for mechanisms)
- **Graph critique**: temperature=0.1, max_tokens=2000 (very deterministic)

### Toggle Examples

```python
# Faster, cheaper (no examples)
system, user = get_extraction_prompts(text, include_examples=False)

# Slower, higher quality (with examples)
system, user = get_extraction_prompts(text, include_examples=True)
```

## Performance Tips

1. **Cache prompts**: System prompts rarely change - cache them
2. **Batch requests**: Process multiple nodes/edges in parallel
3. **Fallbacks**: Always have non-LLM fallbacks for reliability
4. **Validation**: Parse and validate JSON output strictly
5. **Logging**: Track prompt performance (quality, latency, cost)

## Future Enhancements

- [ ] Graph critique prompts (cycle detection, collider warnings)
- [ ] Subgraph composition prompts
- [ ] Mediator/moderator suggestion prompts
- [ ] Study design recommendation prompts
- [ ] Prompt versioning and A/B testing
- [ ] User-customizable templates
- [ ] Multi-language support
