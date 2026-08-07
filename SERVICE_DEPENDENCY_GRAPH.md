# SERVICE DEPENDENCY GRAPH - AlphaAlgo Production Engineering

This document details the microservice integrations, startup execution sequences, and runtime dependency bounds of the AlphaAlgo Quantitative Platform.

---

## 1. System Startup Ordering Sequence

To guarantee deterministic, crash-free initialization of the platform's multi-agent components, services must be booted in a strict, linear startup sequence:

```
[Start Thread]
      │
      ▼ (Step 1)
[UnifiedDecisionBus (LogAct)]  ──► Spawns background LogAct processor task.
      │
      ▼ (Step 2)
[HierarchicalMemorySystem]     ──► Boots SAGE Graph, loads memory schemas, runs AutoMem.
      │
      ▼ (Step 3)
[SkillRouter]                  ──► Registers default PFs and behavior adapters.
      │
      ▼ (Step 4)
[CognitiveSystemController]    ──► Unifies injected dependencies (HMS, Router, Shield).
      │
      ▼ (Step 5)
[Secure Sandbox / Shield]      ──► Initiates AST verification and sandbox process limits.
```

### 1.1. Startup Initialization Ordering Risks
*   **Vector:** Initializing `CognitiveSystemController` before the `UnifiedDecisionBus` is running.
*   **Consequence:** Proposed transactions will be rejected, or block indefinitely in uninitialized priority queues.
*   **Mitigation:** `CognitiveSystemController` constructor checks `decision_bus._running` and triggers a warning or auto-starts the bus if inactive.

---

## 2. Runtime & Async Dependency Limits

*   **Database Connections (SAGE):** Restricted to a single, authoritative SQLite and NetworkX Graph instance to avoid file locks.
*   **Asynchronous Voter Timeout Limit:** Fixed at exactly $1.0$ second to prevent infinite wait conditions.

---

*End of Service Dependency Graph.*
