# AlphaAlgo: Unified Adaptive Cognitive Architecture
## Master Engineering & Validation Specification

---

## Executive Summary
This document defines the final, validated, closed-loop cognitive architecture for **AlphaAlgo**, a research-grade unified autonomous financial intelligence system. It transitions the codebase from a collection of isolated, simulated, or duplicated agent modules to a single, mathematically grounded, feedback-driven cognitive processor.

---

## Phase 0 — Adversarial Review & Architectural Pruning

This section presents an adversarial, peer-review style critique of every major subsystem to prove its necessity, merge redundant layers, or eliminate "intelligence theatre" (mocked loops).

### 1. Subsystem: `autonomous_superintelligence`
*   **Adversarial Challenge**: Is this module a real superintelligence, or is it an empty wrapper containing disjointed background loops and mock resource management? Can this capability be removed or fully absorbed?
*   **Verdict**: **Deprecate and Reallocate**.
*   **Pruning / Merge Action**: The directory `trading_bot/autonomous_superintelligence/` is deprecated. Its global orchestrator and background threads are consolidated entirely into the `IntegratedAgentSystem` (IAS). Real resource controller limits (compute, capital) are merged into the shared IAS framework to prevent duplicate thread loops and simulated noise.

### 2. Subsystem: `apex_fi`
*   **Adversarial Challenge**: `apex_fi` represents "institutional financial reasoning". Why does it exist independently of the core decision systems or quant engines? Is there duplicated reasoning or overlapping models?
*   **Verdict**: **Retain but Hard-Bound to Cognitive Execution**.
*   **Justification**: Structured decision governance, institutional cross-regime consensus, and model parliaments require a separate immutable consensus layer to validate signals prior to portfolio architecturing. It is refactored from a standalone daemon into a pure synchronous/asynchronous logic engine evaluated by the IAS Decision Layer.

### 3. Subsystem: `neuros_fi`
*   **Adversarial Challenge**: `neuros_fi` attempts to model biological brain structures (thalamus, neocortex, etc.). Is this biological analogy a source of high-entropy code duplication, or does it deliver unique predictive alpha?
*   **Verdict**: **Consolidate & Ground**.
*   **Pruning / Merge Action**: It is pruned of mock "sleep/awake" simulations. It is redesigned as the **Cognitive Brain Layer** of IAS, representing multi-horizon predictive processing. `Region1` (Neocortex) acts as spatial-temporal state feature mapper, while `Region2` (Prefrontal) provides action-critique planning.

### 4. Subsystem: `deepchart`
*   **Adversarial Challenge**: Can technical-indicator-based chart engines be replaced by standard quantitative signal pipelines?
*   **Verdict**: **Redesign as Latent State Representation Engine**.
*   **Justification**: Raw time-series signals suffer from low signal-to-noise ratios. Deepchart is refactored into a **Variational Latent Space (VLS)** state representation engine (DreamerV3/JEPA paradigm) mapping high-dimensional liquidity, friction, and entropy dimensions into a compressed transition state.

### 5. Subsystem: `self_healing_ai` and `self_diagnostic`
*   **Adversarial Challenge**: Why do we have separate healing and diagnostics?
*   **Verdict**: **Merge into Safety & Diagnostics Infrastructure**.
*   **Consolidation**: `self_diagnostic` and `self_healing_ai` are merged. Diagnostics acts as the telemetry provider (detector), while Healing acts as the non-destructive remediation engine (proposer) acting via the RSIE code improvement branch framework.

---

## Phase 1 — Capability Ownership Matrix

To eliminate overlapping orchestrators, multiple planners, or split research engines, we establish a strict single-owner matrix for all Tier-0 and Tier-1 capabilities.

| Capability Class | Authoritative Owner | Deprecated / Merged Modules |
| :--- | :--- | :--- |
| **Planning** | `IntegratedAgentSystem.PlannerAgent` | `autonomous_superintelligence/agent_coordinator`, `self_assembly_ai/master_orchestrator` |
| **World Modeling** | `deepchart.latent_state_engine` | `SelfPlayLoop` synthetic generators, random-walk simulators |
| **Financial Reasoning**| `apex_fi.model_parliament` | Legacy agents, redundant rule-based indicators |
| **Research** | `autonomous_research_organism` | `autonomous_superintelligence/research_engine` |
| **Memory** | `trading_bot.memory.cognitive_store` | Fragmented file-based metrics JSONs, independent DBs |
| **Learning** | `neuros_evolution.meta_learning_loop`| Independent `self_learning_concepts` |
| **Evolution** | `neuros_evolution.evolution_engine` | `self_modification_engine`, `code_genetics`, `self_mastery/code_evolver` |
| **Governance** | `trading_bot.security.governance` | Simulated safety gates |
| **Verification** | `self_healing_ai.validators` | Fragmented validation scripts |
| **Execution** | `trading_bot.execution.trade_executor` | Simulated trading loops |
| **Scheduling** | `IntegratedAgentSystem.Scheduler` | Multi-threaded polling loops |
| **Coordination** | `trading_bot.swarm.SwarmController` | `self_coordinating_ai/orchestrator` |
| **Diagnostics** | `self_diagnostic.diagnostic_engine` | Multi-system logs, unstructured error dumps |
| **Self-Model** | `self_concepts.self_concept_engine` | Simulated capability scores |
| **Evaluation** | `trading_bot.evaluation.evaluation_pipeline`| Mock backtesters |

---

## Phase 2 — Scientific & Research Validation

Every major architectural choice is anchored in established machine learning, cognitive science, and financial mathematics research.

### 1. World Modeling: Latent State Dynamical Systems (DreamerV3, JEPA)
*   **Supporting Research**: Hafner et al. (2023) "Mastering Diverse Domains through World Models", LeCun (2022) "A Path Towards Autonomous Machine Intelligence".
*   **Contradictory Research**: Raw time-series architectures (e.g. standard Transformers, Informer, PatchTST) argue that latent state transition models suffer from cumulative error drift during planning horizons.
*   **Trade-off & Synthesis**: We utilize **Triangulated Latent Consistency**—the latent state must match short-term autoregressive price forecasting, mid-term order flow imbalances, and long-term macroeconomic indicators to bound cumulative drift.
*   **Implementation Cost**: Medium-High (requires continuous auto-encoding pre-training).
*   **Capability Gain**: Extreme reduction in input dimensionality; allows planning inside low-dimensional latent space.

### 2. Multi-Agent Consensus: Model Parliament & Sovereign Voting
*   **Supporting Research**: Arrow's Impossibility Theorem & Ensemble Theory.
*   **Contradictory Research**: Uniform RL optimization argues that multi-agent voting results in sub-optimal agent compromises compared to a single end-to-end deep policy network.
*   **Trade-off & Synthesis**: Standard voting fails in financial regimes due to correlation. We implement a **regime-weighted Borda count** where each agent’s vote weight is dynamically scaled by its out-of-sample historical performance under the current latent market regime.

---

## Phase 3 — Closed-Loop Cognitive Architecture

The system forms one continuous, zero-loss cognitive cycle. Every subsystem participates in this loop.

```
                  [ Observation ] (Market ticks, Order books)
                         │
               [ Memory Construction ] (Data Fabric, Episodic Memory)
                         │
               [ World Model Update ] (Deepchart Latent State VAE)
                         │
             [ Hypothesis Generation ] (Research Organism / Symbolic)
                         │
                   [ Simulation ] (World Model Latent Trajectory)
                         │
                  [ Verification ] (Constitutional/Safety Boundary)
                         │
                     [ Planning ] (Prefrontal Region / Action Selection)
                         │
                     [ Decision ] (Model Parliament / Swarm Consensus)
                         │
                    [ Execution ] (Trade Executor / Broker Bridge)
                         │
               [ Outcome Measurement ] (Real-time PnL & Slippage Tracking)
                         │
                     [ Learning ] (Meta-Learning Policy Gradient)
                         │
             [ Knowledge Consolidation ] (Concepts, Knowledge Fabric)
                         │
                  [ Self-Assessment ] (Self-Diagnostic Telemetry)
                         │
             [ Improvement Proposal ] (RSIE Loop / Code Evolution Engine)
                         │
                    [ Evaluation ] (Sandbox Backtest & Safety Check)
                         │
                [ Promotion/Rejection ] (Governance Controller Gate)
                         │
             [ Updated Cognitive System ] ──────────────────┐
                         ▲                                  │
                         └──────────────────────────────────┘
```

---

## Phase 4 — Evidence-Driven Self-Improvement

No subsystem can modify itself directly. All improvements undergo the strict six-gate RSIE (Recursive Self-Improvement Engine) validation pipeline.

```
[ Weakness Detected ] (Diagnostics logs a calibration or execution anomaly)
         │
[ Root Cause Analysis ] (Information Bottleneck pinpoints parameter/logic)
         │
[ Hypothesis Formulated ] (Research Organism generates genetic or parametric variant)
         │
[ Sandbox Experiment ] (Isolated execution in Shadow Sandbox)
         │
[ Statistical Validation ] (P-value < 0.05, effect size > 0.3)
         │
[ Security & Compliance Check ] (Safety core & Code safety scanner approval)
         │
[ Human-in-the-Loop Approval ] (Aletheia/Governance Controller write to pending_approvals.json)
         │
[ Promotion & Deployment ] (Hot swap of active strategy/parameter)
         │
[ Continuous Telemetry ] (Immediate rollback triggered if latency/drawdown breaches boundaries)
```

---

## Phase 5 — Research Integration Corpus

To guarantee the engineering-to-research traceability, major research principles are mapped to capability owners.

1.  **Information Bottleneck Principle (Tishby et al.)**
    *   *Principle*: Compress input representation to preserve maximum mutual information with the target (future return) while minimizing information about noise.
    *   *Owner*: `deepchart.latent_state_engine`
2.  **Epistemic vs. Aleatoric Uncertainty (Kendall & Gal)**
    *   *Principle*: Separate market noise (aleatoric) from system ignorance (epistemic). Scale down position size when epistemic uncertainty is high.
    *   *Owner*: `apex_fi.risk_governance` (Kelly Sizing Calculator)
3.  **Active Inference (Friston et al.)**
    *   *Principle*: Minimize free energy by continuously adjusting internal world models or acting on the environment to match expectations.
    *   *Owner*: `neuros_fi` brain stem & cortical layers.

---

## Phase 6 — Benchmark Specification

Every validated subsystem is bound to measurable success criteria.

| Subsystem | Metric Name | Metric Definition | Target Target |
| :--- | :--- | :--- | :--- |
| **Financial Intelligence**| Sharpe Ratio | Annualized return over annualized volatility | > 2.0 (OOS) |
| | Max Drawdown | Maximum peak-to-trough equity reduction | < 10% |
| | Calibration Error| $|Expected Confidence - Actual Win Rate|$ | < 0.05 |
| **World Model** | Reconstruction MSE | L2 reconstruction error of latent space features | < 0.001 |
| | Prediction Accuracy| Sign prediction of t+1 midprice from latent transition | > 58% |
| **Research Organism** | Hypothesis Throughput| Number of complete valid hypothesis tests per hour | > 100 / hr |
| | Reproducibility Rate| % of experiments matching simulated return in OOS | > 95% |
| **Memory** | Latency | Time to retrieve historical regime experiences | < 5ms |
| **Planning** | Horizon Completion| Execution of 5-step strategy goals without replan | > 90% |
| **Evolution** | Regression Rate | % of promoted strategies causing degradation | < 2% |
| **Engineering** | System Latency | End-to-end processing (tick input to order output) | < 15ms |

---

## Phase 7 — Incremental Implementation Roadmap

We define 4 verifiable, isolated integration slices. Each slice must undergo an ablation study and regression validation before promotion.

### Slice 1: Orchestration Consolidation & Redundancy Removal
*   **Goal**: Deprecate `agents 2`, `trading_bot/agents`, `autonomous_superintelligence`, and merge orchestration into `IntegratedAgentSystem`.
*   **Validation**: Complete end-to-end main initialization and zero-error system startup under SOA Layer 0-7.

### Slice 2: Grounding and Reality Verification
*   **Goal**: Replace all synthetic `np.random` price generators in learning and simulation loops with historical database tick replays.
*   **Validation**: Backtest comparison showing exact match between simulator performance and dry-run performance.

### Slice 3: Latent World Model Upgrade (Deepchart VLS)
*   **Goal**: Refactor `deepchart` into a true latent state autoencoder with continuous online reconstruction.
*   **Validation**: Reconstruction error < 0.001, sign prediction accuracy > 55%.

### Slice 4: Self-Healing & Closed-Loop Remediator
*   **Goal**: Implement diagnostic telemetry triggers that automatically dispatch proposals to the RSIE loop to patch code, validate, and roll back if necessary.
*   **Validation**: Inject an anomalous file configuration or parameter corruption; verify system auto-heals within 60 seconds without human intervention.
