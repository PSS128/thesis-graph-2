# Visual Prompt Comparison: Basic vs Advanced

## Quick Stats

| Metric | Basic | Advanced | Difference |
|--------|-------|----------|------------|
| **System Prompt Length** | 182 chars | 2,928 chars | **16x larger** |
| **User Prompt Length** | 634 chars | 634 chars | Same (no examples) |
| **With Examples** | N/A | 2,645 chars | 4x larger |
| **Total Tokens (approx)** | ~200 | ~1,000 | 5x more |
| **Token Cost** | $0.0001 | $0.0005 | 5x more |

---

## BASIC TEMPLATE

### System Prompt (182 characters)

```
You map a highlighted sentence to a SINGLE causal variable.
Return STRICT JSON ONLY as {"name","definition","synonyms","measurement_ideas"}.
Keep the name concise and domain-neutral.
```

**That's it!** Very simple.

### User Prompt (634 characters)

```
## Your Task:

**Highlighted Text**:
"Employees who work four days a week report less burnout."

**Instructions**:
1. Read the highlighted text carefully
2. Identify the SINGLE most important causal variable
3. Create a concise, precise variable name (2-5 words)
4. Write a clear definition with theoretical grounding
5. List comprehensive synonyms (include ~ for related concepts)
6. Provide diverse, concrete measurement ideas (4-8 methods)
7. Specify the theoretical role, analysis level, and temporal scope
8. Check against existing variables for overlap

**Output**: Return ONLY the JSON object. No markdown, no additional text.
```

**Output Example:**
```json
{
  "name": "Work Burnout",
  "definition": "Emotional exhaustion from work stress.",
  "synonyms": ["job stress", "fatigue"],
  "measurement_ideas": ["Survey", "Sick days"]
}
```

---

## ADVANCED TEMPLATE (Psychology Domain)

### System Prompt (2,928 characters - **16x LONGER**)

```
You are an expert research methodologist specializing in causal inference
and variable operationalization.

Your task: Extract a SINGLE, well-defined causal variable from the
highlighted text.

## Quality Criteria for Variable Names:
1. **Specificity**: Precise enough to be measurable (avoid vague terms
   like "quality" or "performance")
2. **Domain-appropriate**: Use standard terminology from the field
3. **Directionality**: Include direction if implied (e.g., "Productivity
   Increase" vs just "Productivity")
4. **Level of analysis**: Specify the unit (individual, organizational,
   national, etc.)
5. **Temporal scope**: Include timeframe if relevant (e.g., "Short-term
   Burnout" vs "Chronic Burnout")

## Definition Requirements:
- One clear sentence (15-30 words)
- Specify the construct being measured
- Clarify boundaries (what is/isn't included)
- Note the theoretical framework if applicable

## Synonyms Guidelines:
- Include 3-8 alternative terms used in the literature
- Cover both formal/technical and colloquial variants
- Note abbreviations or acronyms
- Include related but distinct concepts (mark with ~)

## Measurement Ideas:
- Provide 4-8 concrete operationalization approaches
- Mix quantitative and qualitative methods
- Include validated instruments when applicable
- Note data sources (surveys, admin data, experiments, etc.)
- Specify measurement level (nominal, ordinal, interval, ratio)

## Domain-Specific Guidance (Psychology):
- Reference DSM-5 or validated psychological constructs
- Specify trait vs state measures
- Include reliability/validity considerations
- Note self-report vs behavioral measures
- Reference validated scales (PHQ-9, BFI, etc.)

## Existing Variables in This Graph:
Work Hours, Productivity

**Important**: Check for semantic overlap. If this variable is very
similar to an existing one, note it in your response.

## Thesis Context:
"4-day workweek improves outcomes"

**Important**: Ensure this variable relates to the thesis. Specify its
theoretical role (predictor, outcome, mediator, moderator, confounder).

## Output Format (STRICT JSON):
```json
{
  "name": "Concise Variable Name (2-5 words)",
  "definition": "Precise one-sentence definition with boundaries and context",
  "synonyms": ["synonym1", "synonym2", "~related_concept", "ACRONYM"],
  "measurement_ideas": [
    "Method 1: [scale/instrument name] - [ordinal/ratio/etc]",
    "Method 2: [data source] - [specific operationalization]",
    "Method 3: [behavioral measure or biomarker]",
    "Method 4": [validated instrument or admin data]"
  ],
  "theoretical_role": "predictor|outcome|mediator|moderator|confounder|contextual",
  "level_of_analysis": "individual|organizational|regional|national|cross-national",
  "temporal_scope": "momentary|short-term|chronic|longitudinal|cross-sectional",
  "similar_to_existing": "node_name or null"
}
```

**Critical**: Return ONLY the JSON object. No additional text.
```

### With Few-Shot Examples (+2,645 chars)

If you enable `include_examples=True`, the user prompt becomes 3,279 chars and includes:

```
## Example 1:
**Input Text**: "Studies show that employees who work four days a week
report significantly less emotional exhaustion and stress-related symptoms."

**Output**:
```json
{
  "name": "Work-Related Burnout",
  "definition": "Psychological exhaustion resulting from prolonged exposure
    to chronic workplace stressors, characterized by emotional depletion and
    reduced work capacity.",
  "synonyms": ["occupational burnout", "job burnout", "emotional exhaustion",
    "work stress", "~compassion fatigue"],
  "measurement_ideas": [
    "Maslach Burnout Inventory (MBI) - 22-item validated scale (interval)",
    "Copenhagen Burnout Inventory - emotional exhaustion subscale (ordinal)",
    "Self-reported sick leave days due to stress (count data)",
    "Cortisol levels measured via hair samples (biomarker, ratio)",
    "Weekly time diary: hours of work-related stress (continuous)"
  ],
  "theoretical_role": "mediator",
  "level_of_analysis": "individual",
  "temporal_scope": "chronic",
  "similar_to_existing": null
}
```

## Example 2:
**Input Text**: "The productivity gains were measured by tracking output
per hour across all manufacturing plants."

**Output**:
```json
{
  "name": "Labor Productivity",
  "definition": "The ratio of output produced to hours of labor input,
    measured at the plant level over a fiscal quarter.",
  "synonyms": ["output per hour", "worker efficiency", "labor efficiency",
    "TFP component", "~marginal product of labor"],
  "measurement_ideas": [
    "Total output / total labor hours (ratio scale, plant-level)",
    "Revenue per FTE (full-time equivalent) from payroll data",
    "Units produced per worker-hour from production logs",
    "Value-added per labor hour (from national accounts)",
    "Quality-adjusted output using defect rates"
  ],
  "theoretical_role": "outcome",
  "level_of_analysis": "organizational",
  "temporal_scope": "short-term",
  "similar_to_existing": null
}
```
```

**Advanced Output Example:**
```json
{
  "name": "Work-Related Burnout",
  "definition": "Psychological exhaustion resulting from prolonged exposure to chronic workplace stressors, characterized by emotional depletion and reduced work capacity.",
  "synonyms": ["occupational burnout", "job burnout", "emotional exhaustion", "work stress", "~compassion fatigue"],
  "measurement_ideas": [
    "Maslach Burnout Inventory (MBI) - 22-item validated scale (interval)",
    "Copenhagen Burnout Inventory - emotional exhaustion subscale (ordinal)",
    "Self-reported sick leave days due to stress (count data)",
    "Cortisol levels measured via hair samples (biomarker, ratio)",
    "Weekly time diary: hours of work-related stress (continuous)"
  ],
  "theoretical_role": "mediator",
  "level_of_analysis": "individual",
  "temporal_scope": "chronic",
  "similar_to_existing": "Work Hours"
}
```

---

## KEY DIFFERENCES VISUALIZED

### Quality Enforcement

| Aspect | Basic | Advanced |
|--------|-------|----------|
| Variable naming | Implicit | **5 explicit criteria** (specificity, domain-appropriate, directionality, level, temporal) |
| Definition quality | "Short" | **15-30 words, construct boundaries, theoretical framework** |
| Synonyms | List them | **3-8 terms: formal/colloquial, acronyms, related concepts (marked with ~)** |
| Measurement ideas | "Provide some" | **4-8 methods: quant/qual mix, validated instruments, measurement level** |

### Context Awareness

| Feature | Basic | Advanced |
|---------|-------|----------|
| Domain knowledge | ❌ None | ✅ **4 domains** (economics, psychology, medicine, policy) |
| Existing nodes | ❌ | ✅ **Checks for duplicates** |
| Thesis alignment | ❌ | ✅ **Ensures relevance** |
| Few-shot examples | ❌ | ✅ **2 complete examples** |

### Output Schema

| Field | Basic | Advanced |
|-------|-------|----------|
| name | ✅ | ✅ |
| definition | ✅ | ✅ (stricter: 15-30 words) |
| synonyms | ✅ | ✅ (3-8, with ~ notation) |
| measurement_ideas | ✅ | ✅ (4-8, with scale types) |
| theoretical_role | ❌ | ✅ **NEW** |
| level_of_analysis | ❌ | ✅ **NEW** |
| temporal_scope | ❌ | ✅ **NEW** |
| similar_to_existing | ❌ | ✅ **NEW** |

---

## EDGE RATIONALE: Even Bigger Difference!

### Basic (189 chars)
```
You analyze a proposed causal edge A -> B and list mechanisms, assumptions,
confounders, and prior evidence types. Return STRICT JSON ONLY:
{"mechanisms":[],"assumptions":[],"likely_confounders":[],"prior_evidence_types":[]}.
```

### Advanced (7,200+ chars - **38x LONGER**)

Includes:
- Full causal inference framework (SUTVA, temporal precedence, reverse causality, etc.)
- Mechanism quality criteria (plausibility, specificity, testability)
- Assumption categories (8+ types: temporal, excludability, homogeneity, etc.)
- Systematic confounder detection strategy with severity ratings [CRITICAL], [MODERATE], [MINOR]
- Evidence hierarchy (RCT → quasi → IV → longitudinal → observational)
- Effect heterogeneity guidance
- Testable predictions and falsification tests
- Domain-specific frameworks for each field

**Example Advanced Edge Prompt Includes:**

```
### Mechanisms (Causal Pathways):
**Definition**: Intermediate processes or steps through which A produces changes in B.

**Requirements**:
- Describe the causal chain: A triggers X, which affects B
- Use active, process-oriented language
- Specify temporal sequence (A must precede B)
- Ground in theory (cite frameworks: e.g., "via stress-performance curve")
- Distinguish biological, psychological, social, economic pathways
- Include both intended and unintended pathways

**Quality Criteria**:
- Plausibility: Is this mechanism scientifically credible?
- Specificity: Avoid vague terms like "influences" or "impacts"
- Testability: Can this pathway be empirically verified?
- Completeness: Are there multiple mechanisms? List 3-6.

**Example**: "A=Exercise → B=Cognitive Function"
- "Increased cerebral blood flow delivers oxygen to prefrontal cortex"
- "BDNF (brain-derived neurotrophic factor) production enhances neuroplasticity"
- "Reduced inflammation improves synaptic efficiency"
- "Improved sleep quality strengthens memory consolidation"
```

And similar detail for assumptions, confounders, evidence types, etc.

---

## WHEN YOU SEE THE DIFFERENCE

### Running the Demo

```bash
cd backend
python ADVANCED_PROMPTS_DEMO.py
```

**Output:**
```
=== BASIC TEMPLATE ===
System (182 chars):
You map a highlighted sentence...

=== ADVANCED TEMPLATE ===
System (2,984 chars):
You are an expert research methodologist specializing in causal inference...

Quality Criteria for Variable Names:
1. Specificity: Precise enough...
2. Domain-appropriate...
3. Directionality...
[... 2,800 more characters of guidance ...]
```

---

## BOTTOM LINE

The advanced templates are **research-grade** with:

✅ **16x longer system prompts** (182 → 2,928 chars)
✅ **5x higher token cost** but **much higher quality**
✅ **Domain expertise** built-in (economics, psychology, medicine, policy)
✅ **Causal inference framework** (assumptions, confounders, identification)
✅ **Theory-driven** (references validated scales, frameworks)
✅ **Publication-quality** outputs

The basic templates are good for **rapid prototyping**.
The advanced templates are for **academic research and high-stakes analysis**.
