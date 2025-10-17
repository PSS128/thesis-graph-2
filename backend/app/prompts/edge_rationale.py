"""
Advanced prompt templates for edge rationale generation.
Supports causal mechanism identification, assumption surfacing, and confounder detection.
"""

from typing import Optional, List, Literal
from dataclasses import dataclass


EdgeType = Literal["CAUSES", "MODERATES", "MEDIATES", "CONTRADICTS"]


@dataclass
class EdgeContext:
    """Context for edge rationale to improve quality."""
    domain: Optional[str] = None
    edge_type: EdgeType = "CAUSES"
    existing_confounders: List[str] = None
    a_definition: Optional[str] = None
    b_definition: Optional[str] = None
    study_design: Optional[str] = None  # "observational", "experimental", "quasi-experimental"


class EdgeRationalePrompts:
    """Collection of edge rationale prompt templates."""

    @staticmethod
    def get_basic_system() -> str:
        """Simple, fast rationale generation (original)."""
        return (
            "You analyze a proposed causal edge A -> B and list mechanisms, assumptions, confounders, and prior evidence types. "
            "Return STRICT JSON ONLY: {\"mechanisms\":[],\"assumptions\":[],\"likely_confounders\":[],\"prior_evidence_types\":[]}."
        )

    @staticmethod
    def get_advanced_system(context: Optional[EdgeContext] = None) -> str:
        """
        Advanced rationale with causal inference framework.

        Features:
        - Theory-driven mechanism identification
        - Explicit assumption enumeration
        - Systematic confounder detection
        - Evidence hierarchy classification
        - Domain-specific causal frameworks
        """
        edge_type = context.edge_type if context else "CAUSES"

        if edge_type == "CAUSES":
            relation_guidance = """
## Causal Relationship Analysis (A → B)

You are analyzing a proposed **direct causal effect** from A to B.

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

### Assumptions (Required Conditions):
**Definition**: Conditions that MUST hold for the causal effect to exist or be identified.

**Categories**:
1. **Temporal**: A must occur before B
2. **No reverse causality**: B does not cause A
3. **Monotonicity**: Effect direction is consistent across units
4. **Homogeneity**: Effect size is similar across subgroups (or specify heterogeneity)
5. **Excludability**: A only affects B through the specified mechanisms
6. **SUTVA** (Stable Unit Treatment Value): One unit's treatment doesn't affect others
7. **Measurement validity**: Variables are measured without error
8. **Functional form**: Linear, threshold, dose-response relationship

**Example**: "A=Exercise → B=Cognitive Function"
- "Exercise occurs before cognitive assessment (temporal precedence)"
- "Cognitive function does not determine exercise behavior (no reverse causality)"
- "Exercise intensity remains constant during the study period"
- "No spillover effects between participants in group exercise settings (SUTVA)"
- "Cognitive tests validly measure executive function without practice effects"

### Likely Confounders (Threats to Identification):
**Definition**: Variables that causally affect BOTH A and B, creating spurious association.

**Detection Strategy**:
- Ask: "What causes variation in A?"
- Ask: "What causes variation in B?"
- Identify overlap: Variables in both lists are potential confounders

**Categories**:
1. **Demographic**: age, sex, education, SES
2. **Contextual**: geographic location, time period, institutional setting
3. **Pre-treatment**: baseline levels of B, prior exposure to A
4. **Behavioral**: motivation, health behaviors, risk preferences
5. **Biological**: genetics, comorbidities, physiological states
6. **Structural**: access to resources, social networks, policy environment

**Prioritization**:
- Mark with [CRITICAL] if omitting this confounder would severely bias estimates
- Mark with [MODERATE] if effect is uncertain or could go either direction
- Mark with [MINOR] if effect is likely small

**Example**: "A=Exercise → B=Cognitive Function"
- "[CRITICAL] Baseline cognitive ability - affects both exercise adherence and cognitive scores"
- "[CRITICAL] Socioeconomic status - affects access to exercise facilities and baseline cognition"
- "[MODERATE] Genetic predisposition to Alzheimer's - may affect both exercise motivation and cognitive decline"
- "[MODERATE] Social engagement - active people may have more social interaction (itself beneficial for cognition)"
- "[MINOR] Sleep quality - partially overlaps with exercise effects"

### Prior Evidence Types (What Studies Would Help?):
**Hierarchy of Causal Evidence** (strongest to weakest):
1. **Randomized Controlled Trials (RCTs)**: Gold standard for causal inference
2. **Quasi-experiments**: Natural experiments, regression discontinuity, DiD
3. **Instrumental variables (IV)**: If valid instrument exists
4. **Longitudinal studies**: Panel data with fixed effects
5. **Cross-sectional with rich controls**: Observational with confounder adjustment
6. **Case studies / qualitative**: Mechanism identification

**Specify**:
- Study design appropriate for this question
- Key identification strategy
- Feasibility considerations
- Ethical constraints

**Example**: "A=Exercise → B=Cognitive Function"
- "RCT: Randomize sedentary adults to exercise vs control, measure cognitive change over 6 months"
- "Quasi-experiment: Gym opening in neighborhood as natural experiment (DiD design)"
- "Longitudinal: Panel study tracking exercise and cognition with individual fixed effects"
- "Mendelian randomization: Use genetic variants predicting exercise as instrumental variable"
"""

        elif edge_type == "MODERATES":
            relation_guidance = """
## Moderation Relationship Analysis (A moderates X → B)

You are analyzing a proposed **moderator**: A changes the strength or direction of X's effect on B.

### Mechanisms (How Moderation Works):
- Explain why A amplifies or dampens the X→B relationship
- Specify whether moderation is quantitative (change in magnitude) or qualitative (change in direction)
- Ground in interaction theory

**Example**: "A=Stress moderates Exercise → Cognitive Function"
- "High stress depletes cognitive resources needed to benefit from exercise (attention depletion)"
- "Stress-induced cortisol blocks BDNF production triggered by exercise"

### Assumptions:
- Moderator A is independent of treatment X (no confounding of the moderator)
- Moderator effect is not spurious (not driven by third variable)
- Functional form of interaction is correctly specified

### Likely Confounders:
- Variables that affect both the moderator A and the outcome B
- Variables that create spurious interaction effects

### Evidence Types:
- "Subgroup analysis within RCT (test A×X interaction)"
- "Meta-regression across studies varying in A"
"""

        elif edge_type == "MEDIATES":
            relation_guidance = """
## Mediation Relationship Analysis (X → A → B)

You are analyzing a proposed **mediator**: A transmits the effect of X to B.

### Mechanisms (Mediation Pathway):
- Explain how X causes A
- Explain how A causes B
- Specify whether mediation is partial or complete

**Example**: "A=Burnout mediates Workload → Turnover"
- "High workload triggers emotional exhaustion (X→A)"
- "Emotional exhaustion reduces job commitment and increases quit intentions (A→B)"

### Assumptions:
- No confounding of X→A, A→B, or X→B relationships
- No mediator-outcome confounding affected by treatment (sequential ignorability)
- Correctly specified functional forms

### Likely Confounders:
- Variables affecting both A and B (post-treatment confounders)

### Evidence Types:
- "Mediation analysis with sequential ignorability (e.g., inverse probability weighting)"
- "Experimental manipulation of both X and proposed mediator A"
"""

        elif edge_type == "CONTRADICTS":
            relation_guidance = """
## Contradiction Analysis (Evidence Against A → B)

You are analyzing why evidence might contradict a causal claim.

### Mechanisms (Alternative Explanations):
- Reverse causality (B → A instead)
- Null effect (no relationship)
- Spurious correlation (confounding)
- Measurement error masking true effect

### Assumptions Being Violated:
- Which assumptions of the original causal claim are not met?

### Confounders That Might Explain Contradiction:
- Third variables creating spurious negative/null results

### Evidence Types:
- Studies with negative results, null findings, or opposite effects
"""

        base = f"""You are an expert in causal inference, research methodology, and domain-specific theory.

{relation_guidance}

"""

        # Add domain-specific guidance
        if context and context.domain:
            domain_guidance = {
                "economics": """
## Domain-Specific Framework (Economics):
- Apply standard economic models (utility maximization, general equilibrium, etc.)
- Consider supply and demand mechanisms
- Note elasticities and marginal effects
- Address endogeneity concerns (simultaneity, omitted variables)
- Reference natural experiments when possible
- Consider macroeconomic vs microeconomic channels
""",
                "psychology": """
## Domain-Specific Framework (Psychology):
- Ground mechanisms in psychological theory (cognitive, behavioral, affective)
- Reference validated theoretical frameworks (e.g., TPB, SCT, stress-appraisal)
- Consider individual differences and personality factors
- Note self-report bias and demand characteristics
- Address temporality in psychological processes
""",
                "medicine": """
## Domain-Specific Framework (Medicine):
- Ground mechanisms in pathophysiology
- Consider biological plausibility
- Note dose-response relationships
- Address iatrogenic effects and side effects
- Reference clinical guidelines and biomarkers
- Consider pharmacokinetics and pharmacodynamics
""",
                "policy": """
## Domain-Specific Framework (Policy):
- Consider implementation fidelity and compliance
- Note intended vs unintended consequences
- Address targeting and eligibility criteria
- Consider cost-effectiveness and scalability
- Note political feasibility constraints
"""
            }
            base += domain_guidance.get(context.domain, "")

        # Add existing context
        if context and context.existing_confounders:
            base += f"""
## Already-Identified Confounders:
{', '.join(context.existing_confounders)}

**Task**: Identify ADDITIONAL confounders not in this list.
"""

        if context and context.a_definition:
            base += f"""
## Variable A Definition:
{context.a_definition}
"""

        if context and context.b_definition:
            base += f"""
## Variable B Definition:
{context.b_definition}
"""

        base += """
## Output Format (STRICT JSON):
```json
{
  "mechanisms": [
    "Mechanism 1: [process-oriented description with theoretical grounding]",
    "Mechanism 2: [alternative pathway]",
    "Mechanism 3: [specify if biological/psychological/social/economic]"
  ],
  "assumptions": [
    "Temporal precedence: [specify A before B]",
    "No reverse causality: [B does not cause A]",
    "SUTVA: [no interference between units]",
    "[other assumption]: [specify]"
  ],
  "likely_confounders": [
    "[CRITICAL] Confounder 1: [why it affects both A and B]",
    "[MODERATE] Confounder 2: [mechanism]",
    "[MINOR] Confounder 3: [mechanism]"
  ],
  "prior_evidence_types": [
    "RCT: [specific design for this question]",
    "Quasi-experiment: [identification strategy]",
    "Observational: [with specific controls]"
  ],
  "effect_heterogeneity": [
    "May be stronger for [subgroup] because [reason]",
    "May be null for [subgroup] because [reason]"
  ],
  "testable_predictions": [
    "If this relationship is causal, we should observe [specific empirical pattern]",
    "Falsification test: No effect should exist for [placebo outcome]"
  ]
}
```

**Critical**: Return ONLY the JSON object. No markdown formatting, no additional text.
"""

        return base.strip()

    @staticmethod
    def get_user_prompt(
        a_name: str,
        b_name: str,
        context: Optional[EdgeContext] = None,
        include_examples: bool = True
    ) -> str:
        """Generate user prompt with optional examples."""
        prompt_parts = []

        if include_examples:
            prompt_parts.append("""
## Example:

**Proposed Relationship**: Exercise → Cognitive Function

**Output**:
```json
{
  "mechanisms": [
    "Increased cerebral blood flow via cardiovascular improvements delivers oxygen and glucose to prefrontal cortex",
    "Upregulation of BDNF (brain-derived neurotrophic factor) enhances neuroplasticity and neurogenesis in hippocampus",
    "Reduced systemic inflammation decreases cytokine-mediated cognitive impairment",
    "Improved sleep quality strengthens memory consolidation during REM and slow-wave sleep"
  ],
  "assumptions": [
    "Temporal precedence: Exercise regimen occurs before cognitive assessment",
    "No reverse causality: Cognitive function does not determine exercise behavior (possible violation if cognitive decline reduces exercise)",
    "SUTVA: No spillover effects between participants (violated in group exercise settings)",
    "Monotonicity: More exercise leads to better cognition (may have inverted-U relationship)",
    "No measurement error: Cognitive tests validly measure executive function without practice effects"
  ],
  "likely_confounders": [
    "[CRITICAL] Baseline cognitive ability: Higher cognition → more likely to adhere to exercise; also predicts follow-up cognition",
    "[CRITICAL] Socioeconomic status: Affects access to exercise facilities/time and baseline cognitive resources",
    "[MODERATE] Genetic factors: APOE-ε4 allele affects both exercise motivation and Alzheimer's risk",
    "[MODERATE] Social engagement: Exercisers may have more social interaction, itself protective for cognition",
    "[MODERATE] Depression: Affects both exercise behavior and cognitive performance",
    "[MINOR] Diet quality: Correlated with exercise and independently affects brain health"
  ],
  "prior_evidence_types": [
    "RCT: Randomize sedentary older adults (60+) to supervised aerobic exercise vs. stretching control for 6 months; measure episodic memory with RAVLT",
    "Quasi-experiment: Gym opening/closing in neighborhoods as natural experiment (difference-in-differences with geomatched controls)",
    "Mendelian randomization: Use genetic variants predicting exercise behavior as instrumental variable to address confounding",
    "Longitudinal: 10-year panel study with individual fixed effects to control time-invariant confounders"
  ],
  "effect_heterogeneity": [
    "Stronger for older adults (60+) due to age-related cognitive decline being more responsive to intervention",
    "Stronger for sedentary individuals (larger room for improvement from baseline)",
    "May be null for those with severe cognitive impairment (floor effects)",
    "Stronger for aerobic vs. resistance exercise (cardiovascular pathway more important)"
  ],
  "testable_predictions": [
    "Dose-response: More exercise frequency/intensity → larger cognitive gains",
    "Mediator evidence: Exercise should increase BDNF levels, which should correlate with cognitive improvement",
    "Temporal: Cognitive gains should emerge after 3-6 months (time needed for neuroplastic changes)",
    "Falsification: No effect on outcomes unrelated to brain function (e.g., visual acuity)"
  ]
}
```
""")

        prompt_parts.append(f"""
## Your Task:

**Proposed Relationship**: {a_name} → {b_name}
""")

        if context and context.edge_type != "CAUSES":
            prompt_parts.append(f"\n**Relationship Type**: {context.edge_type}")

        if context and context.study_design:
            prompt_parts.append(f"\n**Study Design Context**: {context.study_design}")

        prompt_parts.append("""
**Instructions**:
1. Identify 3-6 plausible causal mechanisms
2. List all critical assumptions required for causal identification
3. Systematically detect likely confounders (mark severity: CRITICAL/MODERATE/MINOR)
4. Suggest appropriate study designs and identification strategies
5. Note effect heterogeneity across subgroups
6. Propose testable predictions to validate the causal claim

**Output**: Return ONLY the JSON object. No markdown, no additional text.
""")

        return "\n".join(prompt_parts).strip()

    @staticmethod
    def get_fallback_response() -> dict:
        """High-quality fallback when LLM is unavailable."""
        return {
            "mechanisms": [
                "Plausible causal pathway connecting A to B (requires theory-driven specification)",
                "Alternative mechanism through intermediate variable (specify)"
            ],
            "assumptions": [
                "Temporal precedence: A occurs before B",
                "No reverse causality: B does not cause A",
                "Ceteris paribus: All else equal, variation in A causes variation in B"
            ],
            "likely_confounders": [
                "[MODERATE] Baseline differences: Variables affecting both A and B",
                "[MODERATE] Contextual factors: Environment or setting influencing both variables"
            ],
            "prior_evidence_types": [
                "Observational study with rich controls",
                "Experimental manipulation if feasible",
                "Quasi-experimental design leveraging natural variation"
            ],
            "effect_heterogeneity": [
                "Effect may vary across subgroups (specify relevant moderators)"
            ],
            "testable_predictions": [
                "Specific empirical pattern that would support causal claim"
            ]
        }


def get_rationale_prompts(
    a_name: str,
    b_name: str,
    domain: Optional[str] = None,
    edge_type: EdgeType = "CAUSES",
    existing_confounders: Optional[List[str]] = None,
    a_definition: Optional[str] = None,
    b_definition: Optional[str] = None,
    use_advanced: bool = True,
    include_examples: bool = True
) -> tuple[str, str]:
    """
    Get system and user prompts for edge rationale.

    Returns:
        (system_prompt, user_prompt) tuple
    """
    context = EdgeContext(
        domain=domain,
        edge_type=edge_type,
        existing_confounders=existing_confounders or [],
        a_definition=a_definition,
        b_definition=b_definition
    )

    if use_advanced:
        system = EdgeRationalePrompts.get_advanced_system(context)
    else:
        system = EdgeRationalePrompts.get_basic_system()

    user = EdgeRationalePrompts.get_user_prompt(a_name, b_name, context, include_examples)

    return system, user
