# Recursive Self-Improvement Architecture Specification (RSI-2026)

## 1. System Philosophy and Objectives

AlphaAlgo operates under a rigorous, science-first cognitive paradigm governed by **Active Inference** (Friston, 2010), the **Free Energy Principle**, and a totally ordered shared transaction log (**LogAct**). The objective of the **Governed Recursive Self-Improvement (RSI)** architecture is to enable AlphaAlgo to systematically self-reflect, identify capability gaps, hypothesize improvements, safely experiment in sandboxes, independently evaluate candidates, and seek explicit human authorization before promoting changes.

This architecture enforces **uncompromising empirical justification**. Self-improvement is never trusted because AlphaAlgo generated it; it is trusted only because it has survived rigorous statistical and adversarial falsification.

### The Objective Function
The global optimization objective is defined as:
$$\text{Maximize } \Phi = \frac{\Delta \mathcal{C}}{\mathcal{R} \cdot \Omega \cdot \Lambda \cdot \Gamma \cdot \mathcal{E}}$$

Where:
*   $\Delta \mathcal{C}$: Measurable, independently validated capability improvement.
*   $\mathcal{R}$: Operational and financial risk.
*   $\Omega$: Architectural and structural complexity.
*   $\Lambda$: Inference and processing latency.
*   $\Gamma$: Computational overhead.
*   $\mathcal{E}$: Engineering and maintenance costs.

AlphaAlgo rejects complex candidates that provide marginal performance gains at the expense of high complexity, latency, or risk.

---

## 2. Authorized Sequence of Operations (The Pipeline)

No bypasses, shortcuts, or direct-to-production self-modifications are permitted. Every proposed improvement, regardless of the domain, must follow the exact canonical sequence:

```
[Observation]
      ↓
[Problem Detection] (Variational Free Energy or performance spikes)
      ↓
[Root-Cause Analysis] (Counterfactual debugging)
      ↓
[Hypothesis Formulation] (Falsifiable claims)
      ↓
[Research Phase] (Literature & historical outcome mining)
      ↓
[Candidate Design] (Configuration, code, or model mutations)
      ↓
[Sandbox Isolation] (StrategySandbox containerized execution)
      ↓
[Experimentation] (MC simulations, Walk-Forward, historical replays)
      ↓
[Independent Evaluation] (Verification Swarm audit)
      ↓
[Adversarial Falsification] (Stress testing under extreme regimes)
      ↓
[Out-of-Sample (OOS) Validation] (Purged/embargoed historical testing)
      ↓
[Risk & Safety Validation] (Safety Kernel policy audits)
      ↓
[Human Approval Gate] (Dashboard review & verification sign-off)
      ↓
[Versioned Candidate Locking] (Immutable git-tag/HMAC generation)
      ↓
[Shadow / Canary Rollout] (Non-risk production shadow running)
      ↓
[Production Transition] (Canary scaling)
      ↓
[Continuous Monitoring] (Drift detection & SLA tracking)
      ↓
[Outcome Attribution] (Attributing performance to the Genome)
      ↓
[Improvement Genome Update] (Persisting the historical learnings)
```

---

## 3. Autonomy Tiers (Levels of Autonomy)

To establish safety boundaries and protect the system against rogue self-modification, we partition all operations into six distinct **Autonomy Tiers**:

### Tier 0: Observation (Fully Autonomous)
*   **Permissions:** AlphaAlgo can autonomously monitor system state, track metrics, compile execution traces, audit logs, compute surprise values, and detect performance drift.
*   **Behavioral Impact:** Zero behavior modification. The system remains purely reflective.

### Tier 1: Bounded Adaptation (Fully Autonomous within Safe Bounds)
*   **Permissions:** AlphaAlgo can modify predefined operational parameters within hard limits.
*   **Allowed Scenarios:** Updating model routing thresholds, cache expiration periods, memory retrieval rankings, prompt parameters, research prioritization weights, or non-critical resource allocation.
*   **Controls:** All updates must be logged in LogAct, easily reversible, versioned, and monitored for regression.

### Tier 2: Experimental Evolution (Autonomous inside Sandbox)
*   **Permissions:** AlphaAlgo can autonomously generate, mutate, and compile experimental strategies, features, models, planning heuristics, and agents.
*   **Controls:** Executable code must be isolated inside the `StrategySandbox` subprocesses. Absolute wall-clock limits and resource caps are enforced by the OS. Nothing in Tier 2 can touch live network connections or the production database.

### Tier 3: Production Candidate (Pre-Approval State)
*   **Permissions:** The candidate has completed sandbox trials and passed unit, integration, and security checks.
*   **Controls:** The system compiles the candidate's validation report, hashes all files, creates an immutable pull request, and prepares the Human Control Dashboard with complete supporting evidence.

### Tier 4: Human-Governed Production Evolution (Human Authorization Required)
*   **Permissions:** The human operator signs off on the candidate.
*   **Controls:** The system applies the change, tags the repository version, activates canary/shadow deployment, and monitors telemetry with instant rollback triggers.

### Tier 5: Architectural Evolution (Highest Risk - Human Authorization Required)
*   **Permissions:** Modifications affecting the Recursive Improvement Engine itself, the Safety Kernel, Risk Authority, or Human Approval Gates.
*   **Controls:** Any attempt to autonomously bypass or weaken safety guards triggers an immediate, hard-wired shutdown of the improvement engine and sounds an emergency alert.

---

## 4. Subsystem Mapping and Integration

The Governed Recursive Self-Improvement Architecture is designed to recursively improve all 30+ domains of AlphaAlgo by routing proposals through specialized adapters to the single, authoritative **RecursiveSelfImprovementEngine** (`trading_bot/recursive_self_improvement/engine.py`):

1.  **World Model Improvement:** Updates transition models and counterfactual predictions, validating that newer models decrease prediction errors relative to simple statistical baselines.
2.  **Alpha / Strategy Discovery:** Mutates alpha logic and parameters, logging parental lineage inside the `IMPROVEMENT_GENOME.md` to prevent backtest overfitting.
3.  **Trading Policy:** Enhances entry/exit logic while remaining strictly subordinate to the deterministic `RiskAuthority` and `ImmutableShield`.
4.  **Risk Intelligence:** Refines Value-at-Risk (VaR), CVaR, and liquidity models independently of strategy generation.
5.  **Market & Sentiment Intelligence:** Calibrates source reliability and text embedding models, validating incremental predictive gains.
6.  **Research & Planning:** Adapts literature searching, priority scores, and task decomposition strategies.
7.  **Feature & Model Selection:** Discovers predictive representations and optimizes model routing paths.
8.  **Uncertainty & Calibration:** Tunes confidence estimation to enforce trade abstention during periods of high epistemic uncertainty.
9.  **Execution & Portfolio:** Improves execution algorithms to minimize market impact and slippage.
10. **Data & Simulation:** Calibrates spread, slippage, and fill dynamics to match historical market depth.
11. **Failure Diagnosis & Self-Debugging:** Generates post-mortems and counterfactual hypotheses to fix broken contracts or performance regressions.
12. **Resource & Tool Selection:** Optimizes compute allocation per subtask to maximize reliable intelligence per unit of resource cost.
