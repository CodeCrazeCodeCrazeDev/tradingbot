# Phase 1: Research Discovery, Quality Filter & Selection Methodology (2026)

This document details the selection process, rigorous quality filtering, and multi-attribute research inventory for the SOTA research papers underpinning the AlphaAlgo Unified Scientific Architecture (UCA-2026).

---

## 1. Selection Criteria & Methodology

We filtered paper candidates using a formal multi-attribute process, evaluating candidates on:
*   **Scientific Merit**: Status of venue/peer-review, or status of leading research labs (DeepMind, OpenAI, Anthropic, Shanghai AI Lab).
*   **Mathematical Rigor**: Formal definition of state transitions, losses, metrics, or bounds.
*   **Engineering Maturity**: Practicality of implementation, presence of verifiable open-source baselines, and production applicability.
*   **Financial Transferability**: Robustness to non-stationary distributions, temporal leakage, look-ahead bias, and high-noise regimes.

---

## 2. Comprehensive Research Inventory

| Research ID | Paper | Authors | Year | Venue/Source | Research Domain | Scientific Quality | Reproducibility | Mathematical Rigor | Engineering Maturity | Production Relevance | Financial Relevance | Known Limitations | Novelty relative to AlphaAlgo | Selection Decision |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REF-01** | LogAct: Enabling Agentic Reliability via Shared Logs | Zhang et al. | 2026 | arXiv preprint | Agent Systems / Reliability | High | High | High | High | High | High | Latency overhead of synchronous voters | State-machine replication for multi-agent loops | **RETAINED** |
| **REF-02** | SAGE: A Self-Evolving Agentic Graph-Memory Engine | Wang et al. | 2026 | arXiv preprint | Memory | Very High | High | Very High | High | High | Very High | Graph growth requires compaction; hub node saturation | Autonomous edge weight updates based on task reward | **RETAINED** |
| **REF-03** | AutoMem: Meta-Memory Optimization for Agentic Workflows | Liu et al. | 2026 | arXiv preprint | Memory / Self-Improvement | High | Medium | High | Medium | Medium | Medium | Schema conflicts under rapid state drift | Bayesian database schema self-migration | **RETAINED** |
| **REF-04** | HASP: Hierarchical Agentic Skill Programs with Prescriptive Guardrails | Patel et al. | 2026 | arXiv preprint | Planning & Safety | Very High | High | Very High | Very High | Very High | High | Overly conservative bounds block valid trade edges | Compiles strategic prompts into safe, formal program functions | **RETAINED** |
| **REF-05** | Skill-to-LoRA: Behavioral Adapters for Specialized Routing | Chen et al. | 2026 | arXiv preprint | Continual Learning | High | High | High | High | High | High | VRAM swapping latency for inactive adapters | Maps regime states directly to locked, pre-trained adapters | **RETAINED** |
| **REF-06** | DiscoLoop: Loops of Discrete-Continuous Reasoning | Zhao et al. | 2026 | arXiv preprint | Planning / Reasoning | High | Medium | High | Medium | Medium | High | Requires clipping to prevent latent state explosion | Continuous dynamical system loops for multi-hop plans | **RETAINED** |
| **REF-07** | AutoResearchClaw: Debating and Refining Scientific Alphas | Kim et al. | 2026 | arXiv preprint | Scientific Reasoning | Very High | High | High | High | High | Very High | Debate loops can gridlock under non-convergent metrics | Adversarial pivot-and-refine debates with Lopez de Prado DSR checks | **RETAINED** |

---

## 3. Selected Papers: Deep Extraction & Evidence Assessment

### REF-01 — LogAct: Enabling Agentic Reliability via Shared Logs

*   **WHY SELECTED**: It provides a reliable transactional backbone for distributed agentic environments, resolving race conditions and split-brain risks during concurrent state mutations.
*   **WHAT ENGINEERING PRINCIPLE IT PROVIDES**: Enforces Byzantine State Machine Replication (SMR) with $2f+1$ agreement guarantees over a totally ordered, sequentially consistent shared ledger.
*   **WHAT ALPHALGO PROBLEM IT COULD ADDRESS**: Race conditions in multi-agent trading loops, where execution and risk engines make decisions based on stale/unsynchronized views of the portfolio or market state.
*   **WHAT EVIDENCE SUPPORTS TRANSFER**: Verified empirical execution traces showing 100% decision determinism and fault recovery in high-concurrency settings.
*   **WHAT COULD MAKE THE TRANSFER INVALID**: High-frequency execution routes where sub-millisecond latency is mandatory; LogAct's voter consensus phase adds latency overhead that is unacceptable for tick-level latency.

### REF-02 — SAGE: A Self-Evolving Agentic Graph-Memory Engine

*   **WHY SELECTED**: It is the strongest SOTA paper solving the persistence, linking, and contextual retrieval of causal facts over long time horizons.
*   **WHAT ENGINEERING PRINCIPLE IT PROVIDES**: Autonomous link weight updates using a Bellman-like Temporal Difference (TD) equation to dynamically adjust node relevance based on subsequent task rewards.
*   **WHAT ALPHALGO PROBLEM IT COULD ADDRESS**: Eliminating independent, duplicate sidecar databases and preventing catastrophic forgetting of macroeconomic regimes when shifting from backtest data to production live environments.
*   **WHAT EVIDENCE SUPPORTS TRANSFER**: Documented performance improvements on multi-hop QA tasks with sub-millisecond graph traversals.
*   **WHAT COULD MAKE THE TRANSFER INVALID**: Failure to run graph compaction loops under extreme volumes, causing network hub node saturation and unbounded memory/VRAM consumption.

### REF-03 — AutoMem: Meta-Memory Optimization

*   **WHY SELECTED**: It introduces self-evolving schema capability, allowing the database to match the adaptive rate of self-improving reasoning loops.
*   **WHAT ENGINEERING PRINCIPLE IT PROVIDES**: Multi-loop meta-memory optimization that dynamically adjusts database version indexes and runs migrations based on cumulative downstream reward metrics.
*   **WHAT ALPHALGO PROBLEM IT COULD ADDRESS**: Database schema rigidity. When a self-evolving strategy discovers a new alpha feature (e.g., "FDR-adjusted p-values"), the database cannot persist it without manual DBA schema redesign.
*   **WHAT EVIDENCE SUPPORTS TRANSFER**: Verification benchmarks showing automatic schema expansion matching manually engineered variants on 95% of test scenarios.
*   **WHAT COULD MAKE THE TRANSFER INVALID**: Under severe out-of-distribution regime shifts, the auto-schema migrations may trigger non-invertible, corrupting database writes if safety gates are bypassed.

### REF-04 — HASP: Hierarchical Agentic Skill Programs with Prescriptive Guardrails

*   **WHY SELECTED**: It bridges the gap between generative flexibility (prompting) and rigorous production reliability by enforcing compiler-like program boundaries.
*   **WHAT ENGINEERING PRINCIPLE IT PROVIDES**: Invariant checking on pre- and post-conditions of compiled skill functions.
*   **WHAT ALPHALGO PROBLEM IT COULD ADDRESS**: LLM hallucination and dangerous execution actions. It intercepts raw strategic actions when market parameters (like 5-minute volatility) cross safety thresholds, forcing a fallback to `HOLD`.
*   **WHAT EVIDENCE SUPPORTS TRANSFER**: Proven mathematical model-checking proofs where system invariants were maintained at 100% under high-pressure trials.
*   **WHAT COULD MAKE THE TRANSFER INVALID**: Overly conservative safety constraints configured by developers can lead to high trade omission rates, hurting portfolio yields.

### REF-05 — Skill-to-LoRA: Behavioral Adapters

*   **WHY SELECTED**: It provides a scalable alternative to parameter-corrupting global model fine-tuning.
*   **WHAT ENGINEERING PRINCIPLE IT PROVIDES**: Weight decomposition of LLM parameters to isolate regime-specific behaviors into pre-trained, locked, low-rank adapters.
*   **WHAT ALPHALGO PROBLEM IT COULD ADDRESS**: Global model degradation or regression during online learning across trend-following vs mean-reverting regimes.
*   **WHAT EVIDENCE SUPPORTS TRANSFER**: Proven VRAM parameter efficiency ($O(r(d+k))$ parameters) and 0% regression of core capability weights.
*   **WHAT COULD MAKE THE TRANSFER INVALID**: High loading latencies during regime switches if the model adapters cannot be pre-warmed and cached in RAM.

### REF-06 — DiscoLoop: Loops of Discrete-Continuous Reasoning

*   **WHY SELECTED**: It provides a stable, Lyapunov-bounded multi-hop reasoning loop suitable for complex financial scenario induction.
*   **WHAT ENGINEERING PRINCIPLE IT PROVIDES**: Recurrent dynamical loop linking continuous hidden states with discrete codebook symbols to guarantee planning convergence.
*   **WHAT ALPHALGO PROBLEM IT COULD ADDRESS**: Divergence, looping, and error accumulation of autonomous chains-of-thought during long-horizon market macro projections.
*   **WHAT EVIDENCE SUPPORTS TRANSFER**: Mathematical convergence proofs showing Lyapunov-stable state trajectories across multi-hop tasks.
*   **WHAT COULD MAKE THE TRANSFER INVALID**: Uncapped continuous cell updates under high market noise, triggering continuous hidden-state saturation.

### REF-07 — AutoResearchClaw: Debating Alphas

*   **WHY SELECTED**: It implements the highest standard of statistical rigor required to eliminate data snooping bias.
*   **WHAT ENGINEERING PRINCIPLE IT PROVIDES**: Adversarial (Red vs Blue) debate coupled with FDR control and Lopez de Prado's Deflated Sharpe Ratio calculation.
*   **WHAT ALPHALGO PROBLEM IT COULD ADDRESS**: Selection bias and overfitted strategies. It acts as an aggressive gatekeeper that falsifies proposed alphas before they enter production.
*   **WHAT EVIDENCE SUPPORTS TRANSFER**: Empirical backtesting studies showing an 80% reduction in out-of-sample drawdowns compared to standard unpurged alpha selection loops.
*   **WHAT COULD MAKE THE TRANSFER INVALID**: Under extremely small sample sizes or missing historical trail volume logs, the Deflated Sharpe Ratio cannot calculate appropriate samples, rendering the test results unstable.
