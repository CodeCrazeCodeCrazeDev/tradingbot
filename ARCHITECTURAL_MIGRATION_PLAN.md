# ARCHITECTURAL_MIGRATION_PLAN.md
## Architectural Migration and Rollback Strategy

This document specifies the deployment roadmap, shadow modes, and rollback gates for migrating AlphaAlgo from legacy orchestration to UCA-2026.

---

## 1. Shadow Mode and Canary Deployment

1.  **Phase 1: Shadow Deployment (Zero PnL Impact)**:
    Deploy `CognitiveSystemController` (CSC) in a separate, isolated shadow thread. Feed it normalized live data and record output proposals in the HMS Ledger. Compare decisions with legacy production system logs.
2.  **Phase 2: Canary Promotion**:
    Promote CSC to handle 10% of portfolio execution under the strict supervision of the `EvolutionGate` and `ImmutableShield`.

---

## 2. Fail-Closed Rollback Strategy

The rollback daemon monitors three critical triggers over a sliding 10-observation window:

*   **Trigger 1**: Any safety score violation ($safety\_score < 1.0$).
*   **Trigger 2**: ECE Calibration error increases by $> 5\%$.
*   **Trigger 3**: Controller execution latency spikes $> 20ms$.

### Rollback Execution Sequence
If triggered, the daemon executes:
1. Instantly routes all open positions to neutral hedges or exits.
2. Restores code to the immutable, cached git SHA baseline.
3. Shuts down the self-modification loops.
