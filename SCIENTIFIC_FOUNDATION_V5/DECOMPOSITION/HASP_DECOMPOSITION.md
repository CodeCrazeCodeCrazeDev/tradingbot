# Engineering Decomposition: HASP (arXiv:2605.17734)

## Core Hypothesis
Prompt-based skills are "advisory." Reliable agents need "harnessing" via executable Skill Programs (Program Functions - PFs) that trigger on state invariants.

## Mathematical Formulation
- **Harness Operator**: $H(a | s, \text{PF})$.
- **PF Execution**: $a' = \text{PF}(s, a)$.
- **Invariant Check**: $\forall s \in \mathcal{S}_{crit}, \text{PF}(s, a) \in \mathcal{A}_{safe}$.

## Training Methodology
- **Program Synthesis**: Generating Python/WASM snippets from textual skill descriptions.
- **PF-SFT**: Training the agent to "hand-off" control to the PFs at the correct state boundaries.

## Learning Algorithm
Skill Program Evolution.

## Memory Architecture
Procedural Skill Bank (Tier 4).

## Planning Architecture
Constraint-based planning. The planner only considers actions that are "safe" according to the active PFs.

## Agent Architecture
"Harnessed" Hybrid Agent (LLM + Executable Code).

## World Model Contribution
PFs represent "Physical/Logical Invariants" of the market (e.g., "Price cannot be negative").

## Self-improvement Contribution
Validated PFs are "immortal" and do not drift like prompt-based skills.

## Failure Modes
- **Rigid Invariants**: PFs blocking valid but novel high-alpha trades.
- **PF Error**: Runtime crash in the executable snippet.

## Scalability Limits
Complexity of managing and verifying a large library of code snippets.

## Computational Complexity
Low (direct code execution).

## Engineering Tradeoffs
Safety (code) vs. Flexibility (LLM).

## Financial Applicability
Hard-coding risk limits, compliance checks, and mandatory execution steps (e.g., "Cancel all pending before closing").

## Production Readiness
Critical. Standardizes complex behaviors for institutional grade bots.
