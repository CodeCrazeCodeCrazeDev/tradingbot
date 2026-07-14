# Engineering Decomposition: S2L (arXiv:2606.16769)

## Core Hypothesis
Large skill documents consume context tokens and cause instruction drift. Converting procedural behaviors into dynamically loadable LoRA adapters (Skill-to-LoRA) improves efficiency and behavioral stability.

## Mathematical Formulation
- **Skill Adapter**: $\Delta W_{skill} = BA$ (LoRA).
- **Routing**: $a = \pi(s, \text{Adapter}_k)$.

## Training Methodology
Self-distillation of procedural skill traces into adapter weights.

## Learning Algorithm
Behavioral distillation; LoRA fine-tuning.

## Memory Architecture
Procedural Adapter Library.

## Planning Architecture
Adapter routing based on task/state classification.

## Agent Architecture
Adapter-routed agent using multi-LoRA inference (e.g., LoRAX).

## World Model Contribution
Skills act as specialized transition models for specific regimes.

## Self-improvement Contribution
Internalization of new skills into dedicated adapters.

## Failure Modes
Interference between active adapters; routing errors.

## Scalability Limits
Number of concurrent adapters in memory.

## Computational Complexity
O(1) overhead for routing; standard inference cost.

## Engineering Tradeoffs
Model size vs. adapter count.

## Financial Applicability
Execution archetypes (VWAP, TWAP) as loadable weights.

## Production Readiness
Highest.
