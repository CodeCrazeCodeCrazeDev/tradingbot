# Subsystem Audit: world_model

## 1. Scientific Audit
- **Purpose**: Predictive environment modeling, causal reasoning, and imagination.
- **Architecture**: Transitions from V2 (audit baseline) to WM-V3.
- **Algorithms**: Latent dynamics, counterfactual engine, causal modeling, Active Inference.
- **Strengths**: Deep theoretical grounding in Active Inference and Causal SCMs.
- **Weaknesses**: Current implementation is split between V2 (legacy) and V3 (in-progress).
- **Technical Debt**: Parallel V2/V3 paths in `trading_bot/world_model`.
- **Duplication**: Overlaps with `simulation` and `reality_gates`.
- **Scientific Gaps**: Needs full integration of Mamba-based SSMs for long-horizon temporal reasoning.

## 2. One Brain Compliance
- **CSC Integration**: YES (referenced as GWM).
- **HMS Integration**: YES (uses HMS for experience replay).
- **Decision Bus Integration**: Partial.
- **Immutable Shield Integration**: Partial.

## 3. Decision
- **Decision**: KEEP & EVOLVE (Authoritative)
- **Justification**: This is a core component of the "One Brain". Complete the migration to WM-V3 and decommission V2.
