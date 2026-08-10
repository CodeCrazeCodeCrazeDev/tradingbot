# Self-Improvement Safety Model & Operational Limits

This document specifies the safety policies and operational boundaries governing all self-improving layers in AlphaAlgo UCA V6.

---

## 1. Safety Boundaries & Execution Isolation

To prevent out-of-control optimization or resource exhaustion, the following strict bounds are enforced:

### A. Execution Isolation (Sandbox)
*   **Subprocess Isolation**: All untrusted or newly proposed strategy/agent code must run inside the `StrategySandbox` (defined in `trading_bot/core/security/sandbox.py`).
*   **Process Boundaries**: Code runs in a dedicated `multiprocessing.Process` completely decoupled from the parent orchestrator thread.
*   **Timeout Boundaries**: Strict wall-clock timeouts are enforced using SIGTERM signal mapping. If execution exceeds 10 seconds, the sandbox kills the child process.
*   **Syntax Audits**: Proposals undergo AST-level syntax checking before compilation, raising a `SecurityException` if keywords like `eval()`, `exec()`, `__import__`, or `pickle` are detected outside approved sandboxes.

### B. Computational Budgets
*   **VRAM Limits**: Candidate evaluations are restricted to a maximum of 4GB VRAM.
*   **CPU Shares**: Sandbox processes are restricted to low-priority CPU shares (e.g., `nice` value of 19) to prevent CPU starvation on the main execution loop.

---

## 2. Progressive Exposure & Canary Deployment

An approved improvement candidate is never deployed globally or with full risk exposure. It must undergo **Progressive Exposure**:

```
        [Approved Candidate]
                 │
                 ▼
     [Stage 1: Mock/Dry Run] (1000 simulated ticks) -> (Regression?) ──> [Reject/Rollback]
                 │ (Passed)
                 ▼
     [Stage 2: Canary Exposure] (5% position size)  -> (Regression?) ──> [Reject/Rollback]
                 │ (Passed)
                 ▼
     [Stage 3: Multi-Regime Walk] (30-day trial)     -> (Regression?) ──> [Reject/Rollback]
                 │ (Passed)
                 ▼
       [Stage 4: Full Promotion] (100% position size)
```

---

## 3. Atomic Rollback Policies

An active candidate is instantly rolled back to its parent version if any of the following triggers occur:
1. **Drawdown Breach**: The canary strategy suffers a drawdown exceeding $1.5\times$ its out-of-sample baseline.
2. **Calibration Drift**: ECE (Expected Calibration Error) exceeds the baseline by $20\%$ over a 100-step window.
3. **Consensus Starvation**: The Verification Swarm repeatedly vetoes or times out on proposals.
4. **Latency Spike**: Average execution latency of the candidate increases past $1.2\times$ the baseline.

The rollback is **atomic and instant**: the deployment controller swaps the active code pointer back to the verified parent git commit SHA in less than 50ms.
