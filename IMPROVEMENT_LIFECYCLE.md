# IMPROVEMENT_LIFECYCLE.md

This document defines the strict, immutable state machine and trace structure for any proposed self-improvement or self-modification within AlphaAlgo.

---

## 1. Lifecycle State Machine

An improvement proposal must progress sequentially through the following states. Any direct modification of runtime execution state bypassing this sequence is physically blocked by the compilation and testing harness.

```
       ┌───────────────┐
       │   PROPOSED    │  (Hypothesis formulated, ID generated)
       └───────┬───────┘
               │
               ▼
       ┌───────────────┐
       │  EXPERIMENT   │  (Challenger code generated, sandbox execution)
       └───────┬───────┘
               │
               ▼
       ┌───────────────┐
       │   FALSIFY     │  (Adverse scenarios, stress tests applied)
       └───────┬───────┘
               │
         ┌─────┴────────────────┐
         ▼                      ▼
  ┌─────────────┐        ┌──────────────┐
  │  REJECTED   │        │   STAGED     │  (Statistical gain verified)
  └─────────────┘        └──────┬───────┘
                                │
                                ▼
                         ┌──────────────┐
                         │   PROMOTED   │  (Shadow run, then production)
                         └──────┬───────┘
                                │
                                ▼
                         ┌──────────────┐
                         │  MONITORED   │  (Live performance tracking)
                         └──────────────┘
```

---

## 2. Standardized Experiment Ledger Schema

Every experiment is recorded in the immutable `DecisionProvenance` ledger using the following structured JSON schema:

```json
{
  "experiment_id": "EXP-2026-0808-01",
  "state": "PROMOTED",
  "motivation": "Variational Free Energy exceeded 1.5 in volatile regimes causing decision latency degradation.",
  "hypothesis": "Increasing SAGE graph pruning depth reduces retrieval hops from 4 to 2, maintaining search semantic precision.",
  "source_literature": {
    "paper_id": "ARXIV-2605.12061",
    "short_name": "SAGE",
    "principle_utilized": "Outcome-driven dynamic edge weight updates and node compaction."
  },
  "affected_components": [
    "trading_bot/core/hms/memory.py",
    "trading_bot/core/csc/controller.py"
  ],
  "champion": {
    "version": "1.4.2",
    "metrics": {
      "avg_latency_ms": 1.25,
      "mean_p_error": 0.082,
      "drawdown_pct": 0.05
    }
  },
  "challenger": {
    "version": "1.5.0-candidate",
    "metrics": {
      "avg_latency_ms": 0.84,
      "mean_p_error": 0.083,
      "drawdown_pct": 0.05
    }
  },
  "falsification_report": {
    "out_of_sample_p_value": 0.008,
    "latency_under_adversarial_load_ms": 1.10,
    "volatility_shock_stability": "PASSED"
  },
  "decision": {
    "action": "PROMOTE",
    "timestamp": "2026-08-08T18:50:00Z",
    "reasoning": "Challenger achieved a 32.8% reduction in latency without causing statistical regression on prediction error or trade drawdown.",
    "signatures": {
      "immutable_shield_hash": "sha256:d8b724...",
      "evolution_gate_hash": "sha256:a7b8e1..."
    }
  }
}
```

---

## 3. Rollback Protocol

If a promoted Challenger exhibits degradation during the `MONITORED` phase, a rollback is executed automatically.

### A. Failure Triggers for Rollback
- Mean latency degrades by $> 20\%$ over any 15-minute moving window.
- Decision calibration error (ECE) rises above $0.15$.
- Unhandled runtime exceptions occur $> 3$ times in 5 minutes.
- Peak memory consumption breaches safety limit ($> 500\text{MB}$).

### B. Execution of Rollback
- The event bus publishes a `ROLLBACK_TRIGGERED` event.
- The `ArtifactManager` deletes the staged Challenger weights and symlink.
- The `UnifiedComponentRegistry` falls back to the previous immutable Champion version (stored as a verified checkpoint).
- The system goes into a temporary 10-minute cooldown state, during which further self-improvement proposing is completely paused.
- The failure signature is appended to the **Improvement Memory** to avoid repeating the exact regression profile.
