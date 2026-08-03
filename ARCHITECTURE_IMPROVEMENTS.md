# ARCHITECTURE_IMPROVEMENTS.md

# AlphaAlgo — Architectural Improvements

This document outlines the high-level design improvements implemented during the UCA-2026-V5 production engineering audit.

---

## 1. Single-Brain Authoritative Controller (One Brain Pattern)

Previously, the codebase suffered from architectural drift due to multiple "competing" orchestrators (e.g., `mastery_orchestrator`, `master_orchestrator`, `aamis_master_orchestrator`) running in parallel across different directories. This created fragmented learning states and duplicated execution tasks.

### Architecture Cleanup
- Moved all legacy/competing orchestrators to `trading_bot/_archive/legacy_orchestrators/`.
- Positioned the **Cognitive System Controller (CSC)** as the *single authoritative decision engine* ("One Brain").
- Unified the **SkillRouter** and **ImmutableShield** as core supportive services registered with the `UnifiedComponentRegistry` singleton.

---

## 2. Shared-Log Consensus (LogAct Integration)

The trading bus has been upgraded to strictly follow the LogAct total-ordering protocol:

```
Proposed Actions (Market Obs) -> Audited (Verifier Swarm) -> Consensus (Consensus Gate) -> Approved/Vetoed (UnifiedEventBus)
```

By enforcing a monotonic sequence ordering on the `UnifiedDecisionBus`, decisions are fully audit-logged, reproducible, and verifiable.

---

## 3. High-Horizon Stability Mechanisms

To ensure long-duration deployment stability (e.g., months of continuous execution on trading servers without OOM failures), two key resource-management designs were integrated:

### Sliding-Window Buffering
The CSC channels now implement memory bounding. Upon processing each observation, if the size of the discrete channel exceeds 100 entries, the list is automatically sliced:

```python
if len(self.discrete_channel) > 100:
    self.discrete_channel = self.discrete_channel[-100:]
```

### Task-Driven SAGE Evolution
The Hierarchical Memory System (HMS) now cleans up dead graph connections. SAGE leverages Reader-Writer feedback to systematically prune edges with zero active weight, keeping the semantic network optimized.
