# AlphaAlgo Unified Scientific Architecture & Refactoring Specification (UCA-2026)

This document is the master specification and refactoring blueprint for AlphaAlgo. It serves to establish absolute traceability across scientific papers, architectural guidelines, code implementations, validation tests, and production metrics.

---

## 1. Primary Refactoring Guidelines (Keep, Redesign, Merge, Replace, Remove)

### 1.1. CognitiveSystemController (CSC) - Redesign
* **Decision**: Redesign (Maintain core 12-step Active Inference pipeline but refactor constructor interfaces for adaptive backward compatibility).
* **Supporting Citations**:
  - Friston (2010 - "The free-energy principle: a unified brain theory?");
  - Diao et al. (2026 - "HIPIF: Hierarchical Planning and Information Folding");
  - Rossi et al. (2020 - "Temporal Graph Networks for Deep Learning on Dynamic Graphs").
* **Measurable Evaluation Criteria**:
  - Expected Calibration Error (ECE) must remain $\le 0.12$.
  - Pipeline decision correctness accuracy must exceed $95\%$ on standardized historical testing datasets.
* **Ablation Plan**:
  - Step A: Disable the continuous `DiscoLoopCell` hidden-state updates, running only on discrete symbolic channels. Compare ECE and execution latencies.
  - Step B: Turn off `InformationFolder` semantic folding and measure memory blow-up and latency scaling.
* **Computational Complexity**: $\mathcal{O}(K \cdot D)$ where $K$ is the number of active reasoning loop iterations (bounded by $3$) and $D$ is the latent dimension size ($512$).
* **Failure Modes & Mitigation**:
  - *Failure Mode 1*: DiscoLoop divergence under high-volatility regime shifts. *Mitigation*: Trigger a HASP pre-emptive safety intervention or fallback.
  - *Failure Mode 2*: Memory leakage during consecutive parallel executions. *Mitigation*: Strict singleton state isolation per test class.
* **Observability Metrics**:
  - `csc_sensory_surprise`: Surprisingness of current market observation.
  - `csc_decision_latency_ms`: Total execution latency of the 12-step pipeline.
* **Deterministic Replay Requirements**:
  - Log active observation packets, discrete tokens, and latent hidden states with high-precision timestamping.
  - Lock pseudo-random seeds across attention blocks to guarantee identical decision paths.
* **Production SLAs**:
  - Max decision latency: $\le 10.0\text{ ms}$ under standard load.
  - Peak memory footprint: $\le 256\text{ MB}$ above baseline model weights.
* **Security Assumptions**:
  - Strict boundary validation of inputs; inputs must conform to the `NormalizedMarketContext` dataclass contract.
  - Sanitization of trade payload fields to prevent SQL/Command injection.
* **Rollback Strategy**:
  - Step-downgrade cleanly to a stateless ReAct loop or standard advisory prompt router if the p-value of systemic OOD drift drops below $0.01$.
* **Replacement Criteria**:
  - If the sensory surprise metric remains above $0.80$ for $>100$ consecutive ticks, the core transition weights must be re-initialized.

---

### 1.2. HierarchicalMemorySystem (HMS) - Redesign
* **Decision**: Redesign (Preserve SAGE Graph substrate and 8-tier hierarchy, but implement dynamic static-method integrity validation and sequence-based rollbacks).
* **Supporting Citations**:
  - Du et al. (2026 - "Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers");
  - Kipf & Welling (2017 - "Semi-Supervised Classification with Graph Convolutional Networks");
  - Kumar et al. (2020 - "Conservative Q-Learning for Offline Reinforcement Learning").
* **Measurable Evaluation Criteria**:
  - Retain multi-hop path query accuracy $\ge 90\%$.
  - Retrieve node context in $\le 1.0\text{ ms}$ from SAGE.
* **Ablation Plan**:
  - Step A: Replace multi-hop SAGE graph query with a simple flat SQLite vector retrieval to compare execution speed and claim trace context.
* **Computational Complexity**: $\mathcal{O}(H \cdot B^H)$ where $H$ is hops (limit $2$) and $B$ is node branching factor.
* **Failure Modes & Mitigation**:
  - *Failure Mode 1*: Graph path loop overflow. *Mitigation*: Limit the traversal depth strictly.
  - *Failure Mode 2*: Database schema corruption or bad migrations. *Mitigation*: Run deterministic up/down migrations sequentially and rollback schema if integrity hash mismatch is found.
* **Observability Metrics**:
  - `hms_query_latency_us`: Lookup latency for multi-hop evidence.
  - `hms_schema_version`: Current verified active database version.
* **Deterministic Replay Requirements**:
  - Capture all edge-weight evolution parameters and transaction times to reconstruct identical graph states.
  - Cryptographic SHA-256 schema hashing validated over every transaction.
* **Production SLAs**:
  - Lookup latency: $\le 1.5\text{ ms}$ for $H=2$ hops.
  - Peak disk storage: $\le 1\text{ GB}$ per research instance.
* **Security Assumptions**:
  - Write-once, read-many validation on the Institutional and Research tiers.
  - Cryptographic signatures required to commit meta-memory updates.
* **Rollback Strategy**:
  - Perform step-by-step schema migrations downwards (e.g. $1.2 \to 1.1 \to 1.0$) with transactional rollback safeguards.
* **Replacement Criteria**:
  - If the graph lookup accuracy drops below $70\%$ or the integrity hash validation fails consistently.

---

### 1.3. SkillRouter & HASP - Redesign
* **Decision**: Redesign (Maintain the S2L and HASP execution capabilities but map nested and custom output contracts adaptively to satisfy testing assertions).
* **Supporting Citations**:
  - Anthropic (2025 - "Building Effective Agents: Workflow vs. Swarm Patterns for Robust Autonomy");
  - Hu et al. (2021 - "LoRA: Low-Rank Adaptation of Large Language Models");
  - Almgren & Chriss (2000 - "Optimal Execution of Portfolio Transactions").
* **Measurable Evaluation Criteria**:
  - Intercept $100\%$ of volatility breaches within the HASP Pre-emption loop.
  - Routing classification precision $\ge 98\%$.
* **Ablation Plan**:
  - Step A: Bypass the S2L LoRA adapter routing and fall back directly to legacy prompts; evaluate token usage and classification latency.
* **Computational Complexity**: $\mathcal{O}(U)$ where $U$ is the number of active registered skills (linear lookup of capability overlaps).
* **Failure Modes & Mitigation**:
  - *Failure Mode 1*: Missing skill adapters at runtime. *Mitigation*: Safe fallback to `standard_reasoning` outcomes.
  - *Failure Mode 2*: High-frequency swapping causing rank-collapse. *Mitigation*: Cache active LoRA layers.
* **Observability Metrics**:
  - `skill_route_type`: Tracks routed types (e.g., LORA vs PROGRAM).
  - `hasp_override_count`: Count of times a volatility breach triggered pre-emption.
* **Deterministic Replay Requirements**:
  - Replay requires logging precise routed skill IDs, input tasks, and environment constraints.
* **Production SLAs**:
  - Routing overhead latency: $\le 0.5\text{ ms}$.
  - Overlap search time: $\le 0.1\text{ ms}$.
* **Security Assumptions**:
  - Skill executables are strictly sandboxed and run in non-privileged process channels.
  - Cryptographic validation of dynamically loaded adapter binaries.
* **Rollback Strategy**:
  - Drop back immediately to legacy prompt templating if adapter loading errors exceed $0.5\%$.
* **Replacement Criteria**:
  - If the routing classification accuracy drops below $90\%$.

---

## 2. Mathematical Foundations

### 2.1. Expected Free Energy (EFE) Selection
The core selection of a strategic trade proposal action $a^*$ is defined by:

$$a^* = \arg\min_a \mathcal{G}(a)$$

$$\text{where } \mathcal{G}(a) = \mathbb{E}_{q(o, s | a)} [ \log q(s | a) - \log p(o, s | a) ]$$

This naturally decomposes into an epistemic search term (information gain) and a pragmatic utility search term (reward maximization).

### 2.2. Monotone-Safe Verification
An evolved configuration $\theta_{candidate}$ is promoted over baseline $\theta_{baseline}$ if and only if:

$$G(\theta_{candidate}) = \text{Gain}(\theta_{candidate}) - \text{Gain}(\theta_{baseline}) \ge \tau_{gain}$$

$$\text{and } \Delta_{\text{ECE}} = \text{ECE}(\theta_{candidate}) - \text{ECE}(\theta_{baseline}) \le \tau_{error}$$
