#!/usr/bin/env python3
"""
Demonstration of advanced prompt templates.
Shows the difference between basic and advanced outputs.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.prompts.node_extraction import get_extraction_prompts, NodeExtractionPrompts
from app.prompts.edge_rationale import get_rationale_prompts, EdgeRationalePrompts


def demo_node_extraction():
    """Compare basic vs advanced node extraction prompts."""

    text = "Studies show that employees who work four days a week report significantly less emotional exhaustion and stress-related symptoms."

    print("=" * 80)
    print("NODE EXTRACTION DEMO")
    print("=" * 80)
    print(f"\nInput text: {text}\n")

    # Basic prompt
    print("-" * 80)
    print("BASIC PROMPT (Original)")
    print("-" * 80)
    basic_system = NodeExtractionPrompts.get_basic_system()
    basic_user = NodeExtractionPrompts.get_user_prompt(text, include_examples=False)

    print(f"\nSystem ({len(basic_system)} chars):")
    print(basic_system)
    print(f"\nUser ({len(basic_user)} chars):")
    print(basic_user[:500] + "..." if len(basic_user) > 500 else basic_user)

    # Advanced prompt
    print("\n" + "-" * 80)
    print("ADVANCED PROMPT (with Context)")
    print("-" * 80)
    adv_system, adv_user = get_extraction_prompts(
        text=text,
        domain="psychology",
        existing_nodes=["Work Hours", "Job Satisfaction", "Productivity"],
        thesis="A 4-day workweek increases worker productivity without reducing output",
        use_advanced=True,
        include_examples=True
    )

    print(f"\nSystem ({len(adv_system)} chars):")
    print(adv_system[:1000] + "\n... [truncated] ..." if len(adv_system) > 1000 else adv_system)
    print(f"\nUser ({len(adv_user)} chars):")
    print(adv_user[:1000] + "\n... [truncated] ..." if len(adv_user) > 1000 else adv_user)

    print("\n" + "=" * 80)
    print("KEY DIFFERENCES:")
    print("=" * 80)
    print(f"✓ System prompt length: {len(basic_system)} → {len(adv_system)} (+{len(adv_system) - len(basic_system)} chars)")
    print(f"✓ User prompt length: {len(basic_user)} → {len(adv_user)} (+{len(adv_user) - len(basic_user)} chars)")
    print("✓ Domain-specific guidance: Psychology frameworks and measurement scales")
    print("✓ Context awareness: Checks against 3 existing nodes")
    print("✓ Thesis integration: Links variable to overall argument")
    print("✓ Few-shot examples: 2 detailed examples with full schemas")
    print("✓ Extended output schema: theoretical_role, level_of_analysis, temporal_scope")


def demo_edge_rationale():
    """Compare basic vs advanced edge rationale prompts."""

    a_name = "Exercise Frequency"
    b_name = "Cognitive Function"

    print("\n\n" + "=" * 80)
    print("EDGE RATIONALE DEMO")
    print("=" * 80)
    print(f"\nProposed relationship: {a_name} → {b_name}\n")

    # Basic prompt
    print("-" * 80)
    print("BASIC PROMPT (Original)")
    print("-" * 80)
    basic_system = EdgeRationalePrompts.get_basic_system()
    basic_user = EdgeRationalePrompts.get_user_prompt(a_name, b_name, include_examples=False)

    print(f"\nSystem ({len(basic_system)} chars):")
    print(basic_system)
    print(f"\nUser ({len(basic_user)} chars):")
    print(basic_user)

    # Advanced prompt
    print("\n" + "-" * 80)
    print("ADVANCED PROMPT (with Causal Inference Framework)")
    print("-" * 80)
    adv_system, adv_user = get_rationale_prompts(
        a_name=a_name,
        b_name=b_name,
        domain="medicine",
        edge_type="CAUSES",
        existing_confounders=["Age", "Education", "Baseline Cognition"],
        a_definition="Weekly hours of moderate-intensity aerobic activity",
        b_definition="Executive function measured via Stroop task performance",
        use_advanced=True,
        include_examples=True
    )

    print(f"\nSystem ({len(adv_system)} chars):")
    print(adv_system[:1500] + "\n... [truncated] ..." if len(adv_system) > 1500 else adv_system)
    print(f"\nUser ({len(adv_user)} chars):")
    print(adv_user[:800] + "\n... [truncated] ..." if len(adv_user) > 800 else adv_user)

    print("\n" + "=" * 80)
    print("KEY DIFFERENCES:")
    print("=" * 80)
    print(f"✓ System prompt length: {len(basic_system)} → {len(adv_system)} (+{len(adv_system) - len(basic_system)} chars)")
    print(f"✓ User prompt length: {len(basic_user)} → {len(adv_user)} (+{len(adv_user) - len(basic_user)} chars)")
    print("✓ Causal inference framework: SUTVA, temporal precedence, identification assumptions")
    print("✓ Domain-specific: Medical/pathophysiology mechanisms")
    print("✓ Confounder prioritization: CRITICAL/MODERATE/MINOR severity ratings")
    print("✓ Evidence hierarchy: RCT, quasi-experiments, IV, longitudinal designs")
    print("✓ Effect heterogeneity: Subgroup analysis suggestions")
    print("✓ Testable predictions: Falsification tests and dose-response checks")
    print("✓ Context integration: Variable definitions and existing confounders")


def demo_output_schema():
    """Show example JSON outputs."""

    print("\n\n" + "=" * 80)
    print("EXAMPLE OUTPUT SCHEMAS")
    print("=" * 80)

    print("\nNODE EXTRACTION (Advanced Output):")
    print("-" * 80)
    print('''{
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
  "similar_to_existing": "Workplace Stress"
}''')

    print("\n\nEDGE RATIONALE (Advanced Output):")
    print("-" * 80)
    print('''{
  "mechanisms": [
    "Increased cerebral blood flow via cardiovascular improvements delivers oxygen to prefrontal cortex",
    "Upregulation of BDNF enhances neuroplasticity in hippocampus",
    "Reduced systemic inflammation decreases cytokine-mediated impairment"
  ],
  "assumptions": [
    "Temporal precedence: Exercise occurs before cognitive assessment",
    "No reverse causality: Cognitive function does not determine exercise",
    "SUTVA: No spillover effects between participants",
    "No measurement error: Valid cognitive tests without practice effects"
  ],
  "likely_confounders": [
    "[CRITICAL] Baseline cognitive ability: Affects both exercise adherence and outcomes",
    "[CRITICAL] Socioeconomic status: Access to facilities and baseline resources",
    "[MODERATE] Genetic factors: APOE-ε4 affects motivation and Alzheimer's risk"
  ],
  "prior_evidence_types": [
    "RCT: Randomize sedentary adults to exercise vs control for 6 months",
    "Quasi-experiment: Gym openings as natural experiment (DiD design)",
    "Mendelian randomization: Genetic variants as instrumental variable"
  ],
  "effect_heterogeneity": [
    "Stronger for older adults (60+) due to age-related cognitive decline",
    "May be null for severe cognitive impairment (floor effects)"
  ],
  "testable_predictions": [
    "Dose-response: More exercise frequency → larger cognitive gains",
    "Temporal: Gains emerge after 3-6 months for neuroplastic changes"
  ]
}''')


if __name__ == "__main__":
    demo_node_extraction()
    demo_edge_rationale()
    demo_output_schema()

    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("""
The advanced prompts provide:

1. **Theory-driven guidance**: Grounded in causal inference, domain expertise
2. **Quality criteria**: Explicit standards for variable naming, mechanism identification
3. **Context integration**: Uses existing graph state, thesis, domain knowledge
4. **Comprehensive outputs**: Extended schemas with metadata (role, analysis level, etc.)
5. **Few-shot learning**: In-context examples improve LLM performance
6. **Research-grade rigor**: Assumptions, confounders, study designs, heterogeneity

Trade-offs:
- 3-5x longer prompts (higher token cost)
- Requires more LLM capacity (GPT-4, Claude 3 recommended)
- More complex parsing (extended JSON schema)

When to use:
- Advanced: Academic research, high-stakes analysis, publication-quality
- Basic: Rapid prototyping, exploratory analysis, cost-sensitive applications
""")

    print("\nTo run with actual LLM:")
    print("  python -m app.routers.node  # Update to use advanced prompts")
    print("  python -m app.routers.edge  # Update to use advanced prompts")
