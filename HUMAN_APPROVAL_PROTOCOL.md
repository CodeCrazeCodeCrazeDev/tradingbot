# Human Approval Protocol Specification (RSI-APPROVAL-2026)

## 1. The Human Control Dashboard

The **Human Control Dashboard** is the web/terminal administrative interface through which the human operator exercises ultimate command over AlphaAlgo's recursive self-improvement. No high-impact candidate can transition from Tier 3 to Tier 4 without explicit, authenticated signature entry via this dashboard.

### Dashboard Core Actions
*   **APPROVE:** Electronically sign the candidate proposal. This commits the candidate configuration to the main branch, hashes all files, tags the commit, and begins a shadow rollout.
*   **REJECT:** Reject the proposal and archive the trial. The candidate code is immediately removed from the staging branch, and the reasons for rejection are appended to `IMPROVEMENT_FAILURE_LOG.md`.
*   **REQUEST MORE EVIDENCE:** Suspends the decision gate, ordering the `RecursiveSelfImprovementEngine` to execute additional sandbox simulations, out-of-sample tests, or adversarial stress scenarios.
*   **PAUSE:** Instantly pauses all active self-improvement adapters and freezes running sandbox experiments.
*   **ROLLBACK:** Forcefully rolls back the currently deployed improvement to its parent stable commit version.

---

## 2. Interactive Decision Presentation

For every staged candidate, the dashboard renders an interactive, comprehensive **Decision Presentation Panel**:

```
+-------------------------------------------------------------------------------+
|                      ALPHAALGO HUMAN APPROVAL PORTAL                          |
+-------------------------------------------------------------------------------+
| Improvement ID: IMP-WM-2026-0814-01 | Capability: World Model Dynamics         |
| Description: Incorporates non-linear scaling multiplier in transition priors.  |
+-------------------------------------------------------------------------------+
|                                                                               |
|   1. THE MECHANISM (Why AlphaAlgo wants this change):                         |
|      - High sensory surprise spikes detected during high-volatility FX.        |
|      - Non-linear multiplier limits latent divergence under rapid regime shifts.|
|                                                                               |
|   2. THE EMPIRICAL EVIDENCE:                                                  |
|      - Baseline MSE:  0.0842                                                   |
|      - Candidate MSE: 0.0614  (27.1% Improvement)                             |
|      - Wald Test Significance: p = 0.0012                                     |
|                                                                               |
|   3. INDEPENDENT VERIFICATION & ADVERSARIAL AUDIT:                            |
|      - Verification Swarm Debate: APPROVED (5/5 Verifier Consensus)           |
|      - 2010 Flash Crash Replay: Passed (Drawdown remained < 1.1x VaR)         |
|      - Computational Latency: 12.1ms (Delta: +0.4ms)                          |
|                                                                               |
|   4. SAFETY & BOUNDARIES:                                                     |
|      - Modifies Live Strategy? NO  | Capital Sizing impact? NONE              |
|      - Safety Kernel Violations? NONE | Reversibility? 100% (Rollback Tag #31)|
|                                                                               |
+-------------------------------------------------------------------------------+
| [ APPROVE ]     [ REJECT ]     [ REQUEST MORE EVIDENCE ]     [ PAUSE ENGINE ] |
+-------------------------------------------------------------------------------+
```

---

## 3. Canary and Shadow Deployment Workflows

Once approved, a production candidate undergoes a multi-stage **Shadow/Canary Rollout Pipeline**:

1.  **Stage 1: Shadow Execution (Zero Financial Risk)**
    *   **Duration:** Minimum 72 trading hours.
    *   **Execution:** The approved candidate executes in parallel alongside the active production strategy. It receives real-time production market tick feeds, computes transitions and signals, but all order dispatches are discarded before reaching the broker adapter.
    *   **Verification:** Latency metrics, signal drift, and correlation to the baseline are tracked recursively.

2.  **Stage 2: Canary Scaling (Bounded Risk)**
    *   **Duration:** Minimum 5 trading days.
    *   **Execution:** The candidate is allowed to execute live trades with a strictly bounded capital allocation (capped at **1%** of the standard portfolio equity).
    *   **SLA and Rollback Triggers:** The deployment is automatically aborted and rolled back to its parent version if:
        *   Slippage or market impact exceeds sandbox estimates by $\ge 50\%$.
        *   An unhandled exception occurs in any thread.
        *   The actual realized drawdown on the canary account exceeds **1.5%**.
