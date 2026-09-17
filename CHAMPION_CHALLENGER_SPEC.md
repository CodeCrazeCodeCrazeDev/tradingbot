# CHAMPION_CHALLENGER_SPEC.md

This document defines the strict specification for executing Champion-Challenger evaluation and selection of self-improving candidates inside AlphaAlgo.

---

## 1. Primary Objectives of Champion-Challenger Evaluation

To prevent unconstrained or unvalidated self-improvement from destabilizing the live trading environment, AlphaAlgo maintains a strict dual-track configuration:

1. **The Champion (`CHAMPION`)**: The authoritative, production-grade active implementation of a subsystem (e.g. controller, memory, risk engine) currently executing in-production or as the base test target.
2. **The Challenger (`CHALLENGER`)**: A candidate self-improvement proposal containing modified hyper-parameters, revised SAGE schemas, or altered algorithmic execution paths.

The challenger must be rigorously compared to the champion under identical conditions before any promotion occurs.

---

## 2. Replay Simulation and Shadow Execution Modes

Every candidate evaluation must be executed in one of two modes depending on the nature of the subsystem.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CHAMPION-CHALLENGER TRACK                       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
         ┌──────────────────────────┴──────────────────────────┐
         ▼                                                     ▼
┌─────────────────────────────────┐                 ┌────────────────────┐
│      1. REPLAY SIMULATION       │                 │  2. SHADOW RUN     │
│  - Feeds identical ticks        │                 │  - Feeds live tick │
│  - Enforces deterministic seeds │                 │  - Challenger runs │
│  - Measures exact Delta IR/VFE  │                 │    in background   │
└─────────────────────────────────┘                 └────────────────────┘
```

### A. Replay Simulation (Offline Backtesting)
This is the primary method of evaluation. The Evolution Engine runs parallel processes where:
- Standard libraries, NumPy, and PyTorch are seeded with identical alignments (`seed=42`).
- Real tick/bar data from the SQLite database (`market_data.db`) are fed to both implementations simultaneously.
- Every state transition, action, and planning trace is captured and serialized.

### B. Shadow Execution (Online Monitoring)
For runtime policy parameters:
- The Champion executes the actual live trades.
- The Challenger runs in the background, receiving the exact same market feeds and publishing its decisions to the **Shadow Decision Registry**.
- PnL and decision calibration metrics are computed virtually. If the Challenger outperforms the Champion over a minimum of 500 consecutive test-time ticks, it becomes eligible for staging.

---

## 3. Strict Acceptance Criteria

A Challenger is **not** promoted merely because it achieves higher returns or passes a local unit test. It must outperform the Champion across a balanced scorecard of multi-dimensional criteria without degrading any baseline.

| Dimension | Metric | Required Threshold vs. Champion |
| :--- | :--- | :--- |
| **Logic Correctness** | Unit & Integration Test Suite | **100% Pass Rate** (Zero regression allowed) |
| **Performance** | Mean Latency per planning step | **No increase** (Tolerance: $\le 10\%$) |
| **Calibration** | Expected Calibration Error (ECE) | **ECE $\le 0.10$** (Minimal overconfidence) |
| **Robustness** | Max Drawdown under Volatility Shocks | **No regression** (Zero tolerance) |
| **Generalization** | Hold-out set statistical significance | **Wilcoxon $p < 0.01$, Effect size $d \ge 0.35$** |
| **Stability** | Variational Free Energy mean | **VFE $\le 1.2$** |
| **Resource Limits** | Peak VRAM / Memory footprint | **$\le 1.2$x Champion baseline** |

If a Challenger improves profitability but increases planning latency by $30\%$, **it is automatically rejected**.

---

## 4. Promotion Integrity and No-Contamination

To prevent over-fitting (gaming the evaluator) and maintain dataset integrity:
- **Benchmark Splitting**: The benchmark used to evaluate challengers is strictly held-out. The candidate generating system is completely blocked from accessing or reading the validation and hold-out data pools.
- **Hash Verification**: Hold-out dataset files are hashed using SHA-256. If a dataset's signature changes or shows unauthorized writes, the evaluation is halted and flagged as a security violation.
- **Durable Rollback Path**: A checkpoint of the active Champion is preserved by the `ArtifactManager`. If a newly promoted Challenger breaches any baseline boundary within the first 24 hours of production deployment, the system triggers an automated rollback to the preserved checkpoint.
