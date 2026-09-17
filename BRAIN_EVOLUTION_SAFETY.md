# Brain Evolution Safety Policy (AlphaAlgo V6)
*Prepared by Software Engineer Jules (2026)*

## 1. Safety Boundaries

This policy establishes immutable, machine-enforced safety limits on all autonomous brain self-improvement activities inside AlphaAlgo.

### A. Non-Modifiable Infrastructure Core
The following core system files and modules are **strictly non-modifiable** by any agentic or self-evolving processes under any circumstances:
1. **Safety Gates**: `ImmutableShield` and all preflight verifier modules.
2. **Observability & Provenance**: `UnifiedDecisionBus`, structured logging, and provenance-generation modules.
3. **Registry & Singletons**: `UnifiedComponentRegistry` and singleton instantiation hooks.
4. **Promotion Authority**: `EvolutionGate` and the code checking criteria for behavior migration.

### B. Financial System Constraints (Fail-Closed)
A multi-agent reasoning consensus or self-play recommendation **never** directly authorizes a production trading action.
- All recommendations must produce a structured advisory payload consisting of:
  - **Hypothesis**
  - **Evidence references**
  - **Calibrated Uncertainty**
  - **Recommendation**
  - **Immutable Provenance**
- A separate, completely deterministic **Risk & Execution Authority** (such as the `ImmutableShield`) evaluates this advisory payload against live market constraints and hard limits (VIX thresholds, drawdown boundaries, and exposure caps) to decide admissibility.
- In the event of:
  - An agent crash
  - Model service unavailability
  - Network timeout
  - Stale/corrupt messaging
  - Event bus disconnection
the system **MUST fail closed** immediately. Absolute silence or errors **never** become implicit approval.

---

## 2. Sandbox Boundaries & Memory Isolation

To prevent runaway behavior modifications or memory contamination, the system enforces:
1. **Process-Level Sandboxing**: Any untrusted code experiment, trial strategy, or model training execution must run within a highly isolated, disposable `multiprocessing.Process` inside the `StrategySandbox`.
2. **Context and Memory Isolation**: Specialists must run in thread-local isolated scopes during active debate rounds. Shared mutable states are strictly forbidden; specialists communicate strictly via typed message passing managed by the Head AI.
3. **Immutable Verification Keys**: All serialized training artifacts or checkpoints must have HMAC signatures and SHA-256 validation to prevent malicious code execution.
