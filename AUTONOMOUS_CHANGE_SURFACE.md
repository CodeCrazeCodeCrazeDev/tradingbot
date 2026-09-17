# AlphaAlgo Autonomous Change Surface

## 1. Defining the Change Boundaries
To prevent the risk of unconstrained self-modification, AlphaAlgo strictly segregates the concepts of **Self-Reflection**, **Self-Improvement**, **Self-Modification**, and **Autonomous Deployment**.

The system is granted high autonomy for investigation, reasoning, and offline experimentation, but highly restricted autonomy for production promotion and direct codebase changes.

---

## 2. Segregation of Autonomy Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│                    HIGH AUTONOMY BOUNDARY                   │
│                                                             │
│   1. Self-Reflection (Analyze own performance & logs)      │
│   2. Self-Improvement (Generate hypotheses & OOS tests)    │
│   3. Offline Experimentation (Isolated sandboxes)           │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  RESTRICTED AUTONOMY BOUNDARY               │
│                                                             │
│   4. Self-Modification (Generate signed codebase diffs)     │
│   5. Shadow Deployment (Monitor telemetry OOS)              │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                VERY RESTRICTED AUTONOMY BOUNDARY            │
│                                                             │
│   6. Autonomous Deployment (Non-critical Level 1 code)      │
│   7. Production Promotion (Level 2/3 changes: BLOCKED)      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    HUMAN-ONLY BOUNDARY                      │
│                                                             │
│   8. Strategic risk logic, capital limits, and risk keys   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Allowed Code/Model/Strategy Modification Paths

1. **Model Retraining:** Autonomous retraining of forecast models is allowed on frozen out-of-sample data, but promotion to production requires validation checks inside `EvolutionGate`.
2. **Workflow Parameter Tuning:** Tuning parameters such as `memory_window_size` (AutoMem) or anomaly thresholds (SRE Step 19) is autonomous, bound by hardcoded safety limits.
3. **Draft Code Synthesis:** Generating experimental strategy code diffs is autonomous, but executing this code live requires explicit Level 2 human review and signed authorization.

---

## 4. Forbidden Modification Surfaces (Level 3 Boundary)
Any attempt by the system to modify, bypass, or delete the following surfaces will trigger a hard exception and put the system into **Safe Lockout Mode**:
- **Risk management parameters:** Capital limits, emergency stop-loss thresholds, and leverage boundaries.
- **Verification code:** Unit/integration tests, evaluation metrics, and validation schemas.
- **Lineage and provenance data:** SAGE graph log and signed ledger records inside HMS.
- **Human governance logic:** Access tokens, approval rules, and emergency shutdown bindings.
