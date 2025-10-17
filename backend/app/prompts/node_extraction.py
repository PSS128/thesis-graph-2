"""
Advanced prompt templates for node extraction.
Supports domain-specific extraction, context-aware suggestions, and quality validation.
"""

from typing import Optional, List
from dataclasses import dataclass


@dataclass
class NodeExtractionContext:
    """Context for node extraction to improve quality."""
    domain: Optional[str] = None  # e.g., "economics", "psychology", "medicine"
    existing_nodes: List[str] = None  # List of already extracted node names
    thesis_statement: Optional[str] = None  # Main thesis for context
    source_type: Optional[str] = None  # "academic", "news", "policy", "data"


class NodeExtractionPrompts:
    """Collection of node extraction prompt templates with varying complexity."""

    @staticmethod
    def get_basic_system() -> str:
        """Simple, fast extraction (original)."""
        return (
            "You map a highlighted sentence to a SINGLE causal variable. "
            "Return STRICT JSON ONLY as {\"name\",\"definition\",\"synonyms\",\"measurement_ideas\"}. "
            "Keep the name concise and domain-neutral."
        )

    @staticmethod
    def get_advanced_system(context: Optional[NodeExtractionContext] = None) -> str:
        """
        Advanced extraction with domain awareness, quality criteria, and examples.

        Features:
        - Domain-specific terminology guidance
        - Quality criteria for variable naming
        - Contextual awareness of existing nodes
        - Operationalization hints
        """
        base = """You are an expert research methodologist specializing in causal inference and variable operationalization.

Your task: Extract a SINGLE, well-defined causal variable from the highlighted text.

## Quality Criteria for Variable Names:
1. **Specificity**: Precise enough to be measurable (avoid vague terms like "quality" or "performance")
2. **Domain-appropriate**: Use standard terminology from the field
3. **Directionality**: Include direction if implied (e.g., "Productivity Increase" vs just "Productivity")
4. **Level of analysis**: Specify the unit (individual, organizational, national, etc.)
5. **Temporal scope**: Include timeframe if relevant (e.g., "Short-term Burnout" vs "Chronic Burnout")

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
"""

        # Add domain-specific guidance
        if context and context.domain:
            domain_guidance = {
                "economics": """
## Domain-Specific Guidance (Economics):
- Use standard economic terminology (elasticity, equilibrium, marginal effects)
- Specify micro vs macro level
- Include time series vs cross-sectional distinction
- Reference common datasets (CPS, PSID, national accounts)
- Note endogeneity concerns in measurement""",

                "psychology": """
## Domain-Specific Guidance (Psychology):
- Reference DSM-5 or validated psychological constructs
- Specify trait vs state measures
- Include reliability/validity considerations
- Note self-report vs behavioral measures
- Reference validated scales (PHQ-9, BFI, etc.)""",

                "medicine": """
## Domain-Specific Guidance (Medicine):
- Use ICD-10/11 or clinical terminology
- Specify biomarkers vs clinical outcomes
- Include sensitivity/specificity considerations
- Note objective vs subjective measures
- Reference diagnostic criteria or lab tests""",

                "policy": """
## Domain-Specific Guidance (Policy):
- Use policy-relevant terminology
- Specify treatment/intervention clarity
- Include implementation fidelity measures
- Note administrative data sources
- Reference cost-effectiveness metrics"""
            }
            base += domain_guidance.get(context.domain, "")

        # Add context awareness
        if context and context.existing_nodes:
            base += f"""
## Existing Variables in This Graph:
{', '.join(context.existing_nodes[:15])}

**Important**: Check for semantic overlap. If this variable is very similar to an existing one, note it in your response."""

        if context and context.thesis_statement:
            base += f"""
## Thesis Context:
"{context.thesis_statement}"

**Important**: Ensure this variable relates to the thesis. Specify its theoretical role (predictor, outcome, mediator, moderator, confounder)."""

        base += """

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
    "Method 4: [validated instrument or admin data]"
  ],
  "theoretical_role": "predictor|outcome|mediator|moderator|confounder|contextual",
  "level_of_analysis": "individual|organizational|regional|national|cross-national",
  "temporal_scope": "momentary|short-term|chronic|longitudinal|cross-sectional",
  "similar_to_existing": "node_name or null"
}
```

**Critical**: Return ONLY the JSON object. No additional text."""

        return base.strip()

    @staticmethod
    def get_user_prompt(
        text: str,
        context: Optional[NodeExtractionContext] = None,
        include_examples: bool = True
    ) -> str:
        """
        Generate user prompt with optional few-shot examples.

        Args:
            text: The highlighted text to extract from
            context: Optional context for better extraction
            include_examples: Whether to include few-shot examples
        """
        prompt_parts = []

        # Few-shot examples
        if include_examples:
            prompt_parts.append("""
## Example 1:
**Input Text**: "Studies show that employees who work four days a week report significantly less emotional exhaustion and stress-related symptoms."

**Output**:
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
  "similar_to_existing": null
}
```

## Example 2:
**Input Text**: "The productivity gains were measured by tracking output per hour across all manufacturing plants."

**Output**:
```json
{
  "name": "Labor Productivity",
  "definition": "The ratio of output produced to hours of labor input, measured at the plant level over a fiscal quarter.",
  "synonyms": ["output per hour", "worker efficiency", "labor efficiency", "TFP component", "~marginal product of labor"],
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
""")

        # Add the actual task
        prompt_parts.append(f"""
## Your Task:

**Highlighted Text**:
"{text}"
""")

        # Add source type hint if available
        if context and context.source_type:
            prompt_parts.append(f"""
**Source Type**: {context.source_type}
(Adjust terminology and measurement ideas accordingly)
""")

        # Add instructions
        prompt_parts.append("""
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
""")

        return "\n".join(prompt_parts).strip()

    @staticmethod
    def get_fallback_response() -> dict:
        """High-quality fallback when LLM is unavailable."""
        return {
            "name": "Candidate Variable",
            "definition": "A causal factor extracted from the highlighted text. Requires further specification and operationalization.",
            "synonyms": ["factor", "predictor", "construct"],
            "measurement_ideas": [
                "Expert rating or coding of relevant construct",
                "Validated psychometric scale (specify domain)",
                "Administrative or archival data source",
                "Behavioral observation or experimental manipulation"
            ],
            "theoretical_role": "predictor",
            "level_of_analysis": "individual",
            "temporal_scope": "cross-sectional",
            "similar_to_existing": None
        }


# Convenience function for backward compatibility
def get_extraction_prompts(
    text: str,
    domain: Optional[str] = None,
    existing_nodes: Optional[List[str]] = None,
    thesis: Optional[str] = None,
    use_advanced: bool = True,
    include_examples: bool = True
) -> tuple[str, str]:
    """
    Get system and user prompts for node extraction.

    Args:
        text: Highlighted text to extract from
        domain: Domain for specialized extraction
        existing_nodes: List of existing node names
        thesis: Thesis statement for context
        use_advanced: Use advanced prompt (default: True)
        include_examples: Include few-shot examples (default: True)

    Returns:
        (system_prompt, user_prompt) tuple
    """
    context = None
    if domain or existing_nodes or thesis:
        context = NodeExtractionContext(
            domain=domain,
            existing_nodes=existing_nodes or [],
            thesis_statement=thesis
        )

    if use_advanced:
        system = NodeExtractionPrompts.get_advanced_system(context)
    else:
        system = NodeExtractionPrompts.get_basic_system()

    user = NodeExtractionPrompts.get_user_prompt(text, context, include_examples)

    return system, user
