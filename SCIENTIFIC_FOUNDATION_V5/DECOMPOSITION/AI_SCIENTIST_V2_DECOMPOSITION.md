# Engineering Decomposition: AI Scientist-v2 (arXiv:2504.08066)

## Core Hypothesis
Fully automated scientific discovery is possible via agentic tree-search over the research lifecycle (ideation, experiment, analysis, writing). Eliminating human-authored code templates and using VLM feedback loops improves generalization.

## Mathematical Formulation
- **Search Method**: Progressive Agentic Tree Search (e.g., Best-First Tree Search).
- **Optimization**: Iterative refinement based on automated reviewer feedback.

## Training Methodology
N/A (Primarily an agentic framework using frontier models).

## Learning Algorithm
- Ideation -> Experiment Design -> Execution -> Analysis -> Manuscript Authoring.
- VLM feedback loop for figure refinement.

## Memory Architecture
Experiment manager maintains state across the tree search.

## Planning Architecture
High-level hierarchical planning managed by a dedicated "Experiment Manager."

## Agent Architecture
Multi-agent system (Ideator, Executor, Analyst, Reviewer).

## World Model Contribution
Scientific domain knowledge captured through literature search and experiment results.

## Self-improvement Contribution
Iterative refinement of papers based on peer-review scores.

## Failure Modes
- Hallucinated experimental results (mitigated by verifiable execution).
- Brittle code generation for novel experiments.

## Scalability Limits
Computational cost of tree-search and long-running experiments.

## Computational Complexity
Very high (multiple frontier model calls and code execution).

## Engineering Tradeoffs
Search depth vs. success rate of paper acceptance.

## Financial Applicability
Automating the full lifecycle of quantitative strategy research.

## Production Readiness
Medium. Requires high reliability in code execution and validation.
