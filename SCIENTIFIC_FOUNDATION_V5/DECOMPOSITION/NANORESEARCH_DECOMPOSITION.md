# Engineering Decomposition: NanoResearch (arXiv:2605.10813)

## Core Hypothesis
Research automation requires personalization, achieved through tri-level co-evolution of a skill bank, a memory module (user-specific), and label-free policy learning.

## Mathematical Formulation
- **Skill Bank**: $S = \{Rule_1, ..., Rule_n\}$ (compact procedural rules).
- **Memory Module**: $M = \{Exp_{user}, Exp_{project}\}$.
- **Policy Update**: $\Delta \theta_{planner} \propto \nabla \log \pi(a | s, M, S) \cdot F$ where $F$ is free-form feedback internalized into updates.

## Training Methodology
1. **Skill Distillation**: Recurring operations are distilled into rules.
2. **Memory Grounding**: Project history grounds current planning.
3. **Preference Internalization**: Converting feedback into parameter updates (label-free policy learning).

## Learning Algorithm
- Tri-level Co-evolutionary loop.
- Online policy adaptation based on implicit feedback.

## Memory Architecture
User-centric and project-centric hierarchical memory.

## Planning Architecture
Personalized planner that realigns its coordination style based on internalized preferences.

## Agent Architecture
Co-evolving multi-agent framework.

## World Model Contribution
Incorporates user methodological preferences into the causal world model.

## Self-improvement Contribution
Systematically refines research quality and reduces cost over successive cycles.

## Failure Modes
- Over-personalization: System becoming too narrow.
- Skill degradation: Rules becoming outdated.

## Scalability Limits
Managing large libraries of user-specific skills and memories.

## Computational Complexity
Overhead of tri-level management and online policy updates.

## Engineering Tradeoffs
Generalization vs. Personalization.

## Financial Applicability
Automating customized equity research reports and strategy backtesting tailored to specific institutional mandates.

## Production Readiness
Medium. High complexity in managing the co-evolutionary loops.

## Reusable Algorithms
- **TriLevelCoEvolver**: Logic for coordinating updates between Skill Bank, Memory, and Policy.
- **SkillDistiller**: Logic for converting interaction traces into reusable procedural rules.
