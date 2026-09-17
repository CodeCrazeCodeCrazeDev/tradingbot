# EVOLUTION_ENGINE_SPECIFICATION.md

This document provides the authoritative engineering specification for AlphaAlgo's Evolution and Research Layer (The Evolution Engine).

---

## 1. Engine Architecture & Component Topology

The Evolution Engine resides asynchronously to the high-frequency trading runtime. It is organized into a modular pipeline executing sequential post-training optimization, validation, and promotion.

```
┌──────────────┐      ┌────────────────┐      ┌─────────────────┐      ┌──────────────┐
│  Diagnosis  │ ───>  │   Hypothesis   │ ───>  │  Candidate Gen  │ ───>  │  Evaluation  │
│  Anomalies   │      │   Correction   │      │   AST Sandbox   │      │  Simulation  │
└──────────────┘      └────────────────┘      └─────────────────┘      └──────┬───────┘
                                                                              │
┌──────────────┐      ┌────────────────┐      ┌─────────────────┐             │
│  Governance  │ <─── │   Promotion    │ <─── │  Falsification  │ <───────────┘
│  Production  │      │  Statistical   │      │   Adversarial   │
└──────────────┘      └────────────────┘      └─────────────────┘
```

---

## 2. Core Functional Modules

### A. Diagnosis Engine (`EvolutionDiagnostic`)
Continuously tracks active runtime metrics. It consumes telemetry from the event bus and logs:
- World model prediction errors (MAE, MSE).
- Real-time Variational Free Energy spikes.
- Expected Calibration Error (ECE) of strategic decisions.
- Latency and Memory overhead per planning step.
- Trade drawdowns and slippage.

### B. Hypothesis Generator (`ScientificHypothesisGenerator`)
When a metric crosses its defined weakness threshold, the Diagnosis Engine triggers a weakness flag. The Hypothesis Generator converts this flag into a specific scientific target:
- *Example*: High VFE spikes in volatile regimes $\to$ Hypothesis: Reduce learning rate parameter and broaden the SAGE graph search window size.

### C. Candidate Generator (`IsolatedCandidateGenerator`)
Compiles the proposed change. For code modifications, it uses AST-level validation to compile candidate logic in an isolated branch. It strictly enforces:
- AST safelisting: Blocks forbidden primitives (`eval`, `exec`, shell execution).
- Non-overlapping execution environments: Each challenger candidate runs in its own process sandbox.

### D. Replay Evaluation Engine (`SimulationReplayManager`)
Executes the candidate against real tick-level historical data imported from the SQLite database.
- Uses exact seed alignment across PyTorch, NumPy, and random libraries (Deterministic Replay).
- Performs offline backtests to collect trade logs and decision provenance records.

### E. Falsification Gate (`FalsificationValidator`)
Actively attempts to break the candidate using adverse scenarios:
- Distribution shifts (out-of-sample data).
- Extreme volatility injection.
- Corrupted feed simulation.
- Stale memory retrievals.

---

## 3. Mathematical Foundations of Selection

To determine whether a Challenger $\mathcal{M}_C$ should be promoted over a Champion $\mathcal{M}_{P}$, the Evolution Engine executes a strict **Statistical Sign-Test** and **Wilcoxon Signed-Rank Test** on the paired profit-and-loss (PnL) or information-ratio (IR) distributions.

### A. Hypothesis Hypothesis
- $H_0$: The median difference in metric distribution between Challenger and Champion is non-positive ($Median(\mathcal{M}_C - \mathcal{M}_{P}) \le 0$).
- $H_1$: The Challenger statistically outperforms the Champion ($Median(\mathcal{M}_C - \mathcal{M}_{P}) > 0$).

### B. Significance Filtering
Promotion is granted if and only if:
1. The Wilcoxon $p$-value is below the significance alpha:

   $$p < 0.01$$

2. The effect size (Cohen's $d$) exceeds the target threshold:

   $$d > 0.35$$

3. All zero-regression constraints on latency, memory, and safety metrics are fully satisfied.

---

## 4. Byzantine and Fault Tolerance Bounds

Every candidate run is isolated in a separate `multiprocessing.Process` wrapper:
- **Timeouts**: Strict wall-clock SIGTERM enforcement is set per evaluation. If an execution exceeds 120 seconds, the child process is killed and the experiment is flagged as a failure.
- **Exceptions**: Unhandled NameErrors, AttributeErrors, or TypeErrors inside the candidate logic are caught, logged, and the candidate is immediately dropped and blacklisted.
- **Resource Constraints**: Peak memory consumption is monitored; any candidate exceeding 1.5x the Champion's baseline is rejected.
