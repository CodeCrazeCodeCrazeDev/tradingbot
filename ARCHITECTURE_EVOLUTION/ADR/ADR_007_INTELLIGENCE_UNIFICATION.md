# ADR 007: Unification of Intelligence and Learning Loops

## Status
Proposed

## Context
Intelligence and learning are currently spread across `intelligence_core`, `learning`, `self_learning`, and `meta_learning`. This leads to "parallel brains" with separate memory and self-improvement loops.

## Decision
Unify all intelligence components under the **Cognitive System Controller (CSC)** and **Hierarchical Memory System (HMS)**.
1. **Registry**: All specialized intelligence agents (e.g., from `intelligence_core`) will be registered in the `UnifiedComponentRegistry`.
2. **Memory**: Local `structural_memory` or `knowledge_base` files will be migrated to HMS Semantic/Procedural tiers.
3. **Loop**: The CSC will manage a single Active Inference loop that invokes these specialized modules as "Skills".

## Consequences
- **Positive**: "One Brain" compliance, shared learning across the entire system.
- **Negative**: Requires careful migration of specialized agent logic to the CSC interface.
