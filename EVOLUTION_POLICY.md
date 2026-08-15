# AlphaAlgo Cognitive Evolution Policy (UCA-2026)

This document establishes the operational policies, limits, and safety guidelines governing the self-improvement and evolution of the AlphaAlgo system.

---

## 1. Scope & Jurisdiction

This policy applies recursively to all self-improvement engines, evolutionary planners, code-mutation processes, and prompt-tuning scripts operating within the AlphaAlgo ecosystem.

---

## 2. Immutable Operational Limits (Preventing Recursive Instability)

To prevent recursive instability, feedback loops, and chaotic code oscillations, the system enforces the following limits:

| Policy Variable | Hard Limit | Enforcement Action |
| :--- | :---: | :--- |
| **Recursive Depth** | Max 3 levels | Shuts down the mutation daemon and freezes the branch. |
| **Modification Frequency**| Max 1 promotion per 48 hours | Delays subsequent evaluations. |
| **Concurrent Experiments**| Max 1 active sandboxed run | Locks the sandbox from launching parallel runs. |
| **Compute Budget** | Max 10% total system CPU | Throttles process execution using standard OS niceness values. |
| **Rollback Trigger** | 3 successive rollbacks | Freezes the component and triggers manual investigation. |

---

## 3. Oscillation Detection & Component Freezing

If Alpha repeatedly toggles a component back and forth between two states (e.g. changing learning rate from 0.001 to 0.005, then back to 0.001, then to 0.005), an oscillation detector is triggered:
1.  The specific component's self-improvement flag is set to `False`.
2.  The configuration is locked to the last known stable state.
3.  A warning is written to the structured JSONL audit ledger.
4.  Further modifications are locked for 168 hours (1 week).

---

## 4. Promotion & Handshake Criteria

No cognitive modification can be promoted without satisfying the following:
*   **Green Unit Tests**: All 26 standard UCA V5 test cases must pass.
*   **Monotone Improvement**: The stateful Gain Metric must be strictly greater than or equal to the RSEA threshold ($G \ge 0.05$).
*   **Veto Clearance**: Zero vetos from the `VerificationSwarm` or `ImmutableShield` security validators.
*   **Cryptographic Handshake**: The proposal must be signed and hashed.
