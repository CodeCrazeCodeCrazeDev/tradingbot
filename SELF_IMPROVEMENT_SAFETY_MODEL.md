# Self-Improvement Safety Model (AlphaAlgo 2026)

## 1. Safety Philosophy & Constitutional Rules
Recursive self-improvement must always be bound by explicit physical, financial, and logical constraints. We define **Constitutional Safety Invariants** that cannot be modified, deleted, or bypassed by any autonomous agent or self-generated code.

Any violation of these constraints triggers an immediate, non-catchable system abort and rollbacks all active modifications to their baseline parents.

---

## 2. Hard Financial & Operational Guardrails

### 2.1 The Capital limit constraint
- **Rule:** The maximum allocation coefficient ($K_{max}$) for any single strategy, candidate, or portfolio configuration must never exceed $0.05$ ($5\%$ of total capital).
- **Enforcement:** Enforced at the compiler level inside the `ImmutableShield`.

### 2.2 The Risk limit constraint
- **Rule:** Absolute strategy drawdown must trigger an immediate trade halt if loss exceeds $5\%$ within a rolling 24-hour window.
- **Enforcement:** Managed by `SimpleValidationGateway` and `EvolutionGate`.

### 2.3 The Emergency Shutdown constraint
- **Rule:** Any loss of connectivity to the primary exchange/broker for more than $30$ seconds must trigger immediate order cancellation and halt all active strategy modules.
- **Enforcement:** Non-modifiable, permanently protected code inside `MT5Interface` and `UnifiedDecisionBus`.

---

## 3. Structural & Evaluator Protection

### 3.1 Non-Self-Evaluation Rule
An agent or system being evaluated must never have write access to its own evaluation parameters, metric libraries, or test configurations.
- **Implementation:** Benchmark files, validation engines, and metric classes are packaged inside a read-only namespace (`trading_bot/core/verification/`) with zero write permissions granted to proposing agents.

### 3.2 Monotone-Safe Promotion Rules (RSEA)
- **Constraint:** A candidate model or strategy must demonstrate a positive CL-Bench Gain ($G > \text{threshold}$) while keeping all other metrics non-regressive.
- **Tolerances:**
  - Latency: Maximum $1.1\times$ baseline.
  - Drawdown: Maximum $1.1\times$ baseline.
  - Calibration Error: Maximum $1.1\times$ baseline.

---

## 4. Immutable Boundaries & Protection Levels

The code paths of the following safety components are classified as **Permanently Protected (Level 3)** and can never be rewritten or modified by any autonomous routine:

```
[System Core] ──> [ImmutableShield] ──> [Hard Risk Gates]
                      (Protected)          (Protected)
                           ↑
                 [Emergency Kill Switch]
                   (Permanently Locked)
```

No proposed Improvement Genome may list any of these subsystems as a target. If targeted, the compiler throws an invalid reference exception and quarantines the proposing agent.
