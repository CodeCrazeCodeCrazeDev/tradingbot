# Engineering Decomposition: HASP (arXiv:2605.17734)

## Core Hypothesis
Textual guidance for agents is too advisory. Upgrading skills into executable Program Functions (PFs) provides hard guardrails and structured intervention in the agent loop.

## Mathematical Formulation
- **Skill Program (PF)**: $PF(s, a) \to \{a', context_{corr}, \text{null}\}$.
- **Intervention Loop**: $a_{final} = \text{apply}(PF, a_{base}, s)$.

## Training Methodology
- Post-training with structured supervision from teacher-reviewed PFs.
- Controlled evolution of the PF library.

## Learning Algorithm
- Program synthesis/evolution for PFs.
- Direct intervention in the inference loop.

## Memory Architecture
The PF library acts as a procedural memory of "hard skills" and "guardrails."

## Planning Architecture
Planner incorporates PF checks to ensure actions are within known-safe or known-effective bounds.

## Agent Architecture
"Harnessed" agent where the base LLM is constrained/guided by executable code.

## World Model Contribution
PFs can represent "physical" or "logical" invariants that the world model must respect.

## Self-improvement Contribution
Evolving validated PFs creates a progressively more reliable agent.

## Failure Modes
- Rigid guardrails: PFs preventing novel but correct actions.
- PF bugs: Executable code errors crashing the agent loop.

## Scalability Limits
Complexity of managing and verifying a large number of PFs.

## Computational Complexity
Low (code execution) but depends on the complexity of PF logic.

## Engineering Tradeoffs
Reliability (hard code) vs. Flexibility (LLM reasoning).

## Financial Applicability
Hard risk limits, compliance checks, and execution-logic verification (e.g., "Never sell before buy is confirmed").

## Production Readiness
High. Very practical for institutional safety and reliability.

## Reusable Algorithms
- **HASPHarness**: Middleware for intercepting agent actions and applying PF library.
- **PFEvolutionaryGate**: Logic for validating and promoting new Program Functions.
