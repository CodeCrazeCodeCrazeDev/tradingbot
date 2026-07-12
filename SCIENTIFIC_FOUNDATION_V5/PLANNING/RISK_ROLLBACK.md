# Phase 4: Risk Analysis & Rollback Strategy (UCA V5)

## 1. Risk Analysis

| Risk | Impact | Likelihood | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Log Bottleneck** | High | Medium | Implement priority-queue sequencing; optimize voter latency (<100ms). |
| **DiscoLoop Divergence** | Medium | Medium | Use residual connections in the loop; implement StopGradient on discrete bridges. |
| **SAGE Graph Complexity** | Low | High | Periodic pruning (Evolution Loop); limit multi-hop retrieval depth (K=3). |
| **S2L Adapter Interference** | High | Low | Orthogonalization loss during training; strict single-adapter activation per task. |
| **EKSFT Information Loss** | Medium | Low | Dynamic thresholding based on validation performance; monitor KL-divergence. |

## 2. Rollback Strategy

### 2.1 Tiered Rollback
- **Tier 0 (Backbone)**: The `UnifiedDecisionBus` maintains the old `publish/subscribe` API. If LogAct fails, revert the internal `_process_log` to immediate dispatch.
- **Tier 1 (Intelligence)**: `CognitiveSystemController` (V5) will be implemented as a new class. The `master_orchestrator` can switch back to `V4Controller` via a feature flag.
- **Tier 2 (Memory)**: Maintain the legacy `.json` research ledger. SAGE will shadow-write to the new `.graphml` format but retrieval will fallback to JSON if graph connectivity is < 50%.

### 2.2 Trigger Criteria
Rollback will be triggered if:
1.  End-to-end latency exceeds 1500ms for 5 consecutive trade proposals.
2.  The `EvolutionGate` rejects 100% of candidates for > 24 hours.
3.  The `VerificationSwarm` consensus drops below 40% (indicating model misalignment).
