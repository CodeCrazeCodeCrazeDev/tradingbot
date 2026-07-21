# 16. Additional Research Decomposition and Synthesis: AlphaAlgo UCA V5+ (2026)

This specification documents the complete, peer-reviewed engineering decomposition, gap analysis, unified synthesis, and refactoring plan for the 8 mandatory 2026 scientific papers in the context of the AlphaAlgo system.

---

## Phase 1 — Paper Decomposition

### 1. EKSFT: Entropy-KL Selective Fine-Tuning (arXiv:2605.29303)
*   **Core Hypothesis**: Standard Supervised Fine-Tuning (SFT) over-memorizes task-specific noise, causing "distribution sharpening" and "entropy collapse." Prioritizing general capability activation through selective Entropy-KL masking preserves exploratory capacity for subsequent Reinforcement Learning (RL) post-training.
*   **Mathematical Formulation**:
    *   Let $\mathcal{M}$ be the selective mask for tokens $t$. Token $t \in \mathcal{M} = \mathcal{M}_H \cup \mathcal{M}_{KL}$.
    *   Entropy threshold mask: $\mathcal{M}_H = \{t \mid H(P(\cdot \mid t_{<})) > \tau_H\}$.
    *   KL-Divergence mask: $\mathcal{M}_{KL} = \{t \mid D_{KL}(P(\cdot \mid t_{<}) \parallel P_{ref}(\cdot \mid t_{<})) > \tau_{KL}\}$.
    *   Loss function: $\mathcal{L}_{EKSFT} = \mathcal{L}_{CE}^{mask} - \lambda_H \mathcal{L}_H^{mask} + \lambda_{KL} \mathcal{L}_{KL}^{mask}$, where masked loss ignores tokens not in $\mathcal{M}$.
*   **Training Methodology & Learning Algorithm**: Standard SFT gradient descent but restricted to backpropagating gradients through non-masked tokens (the Union of high-entropy and high-KL tokens). This retains general exploration capabilities while activating targeted tasks.
*   **Memory & Planning Architecture**: Acts as pre-computation, allowing memory schemas to focus on general semantic paths rather than literal tokens.
*   **Agent & World Model contribution**: Preserves world model transition distributions by preventing mode collapse.
*   **Self-improvement contribution**: Safe self-improvement during local model adaptations without reward hacking.
*   **Failure Modes & Scalability Limits**: Extreme masking ratios ($\rho > 0.3$) remove crucial learning signals; computational complexity scales linearly with sequence length $\mathcal{O}(N)$.
*   **Engineering Tradeoffs & Financial Applicability**: Tradeoff between fine-grained instruction alignment and robust generalizability. Prevents quantitative trading agents from memorizing specific noisy historical ticks.
*   **Production Readiness**: High; standard masking hooks can be added to any PyTorch training loop.

---

### 2. DiscoLoop: Discrete Embeddings and Continuous Hidden States (arXiv:2607.00341)
*   **Core Hypothesis**: Multi-step reasoning in standard Transformers is bottlenecked by depth-local storage. Recurrent looping that mixes discrete symbolic embeddings and continuous hidden states allows internalizing multi-hop causal inference in compact neural recurrent layers.
*   **Mathematical Formulation**:
    *   Let the continuous state be $h_k \in \mathbb{R}^d$ and the discrete symbolic token embedding channel be $e_k \in \mathbb{R}^d$.
    *   The combined state is represented as $S_k = [h_k; e_k]$.
    *   Recurrence transition: $h_{k+1} = \tanh(W_h h_k + W_e e_k + b)$.
    *   Discrete projection: $e_{k+1} = \text{one-hot}(\arg\max(\text{softmax}(W_p h_{k+1})))$.
*   **Training Methodology & Learning Algorithm**: BPTT (Backpropagation Through Time) over unrolled recurrent loops. Realignment interventions are applied training-free during inference to correct latent drifts.
*   **Memory & Planning Architecture**: Dynamic working memory state updated loop-by-loop. Translates flat search trees into multi-loop recurrent trajectories.
*   **Failure Modes & Computational Complexity**: Risk of continuous state drift or discrete cycle trapping; complexity is $\mathcal{O}(L \cdot d^2)$ per loop where $L$ is number of unrolled loops.
*   **Financial Applicability**: Critical for sub-millisecond multi-hop execution reasoning (e.g., assessing Correlation $\to$ Liquidity $\to$ Spread $\to$ Action) within single inference cycles.

---

### 3. AutoMem: Automated Learning of Memory as a Cognitive Skill (arXiv:2607.01224)
*   **Core Hypothesis**: Memory operations (Write, Read, Query, Prune) are learnable cognitive skills (metamemory) that can be optimized autonomously through double-loop feedback.
*   **Mathematical Formulation**:
    *   Let $a_m \in \mathcal{A}_m$ be a memory action.
    *   Loss: $\mathcal{L}_{AutoMem} = -\sum \log \pi(a_m \mid s) \cdot A(s, a_m) + \lambda \mathcal{H}(\pi)$, where $A(s, a_m)$ is the advantage of memory actions evaluated by successful downstream task executions.
*   **Algorithms**:
    *   *Loop 1 (Structure)*: Off-line analysis of agent traces to optimize memory schema definitions and version indices.
    *   *Loop 2 (Proficiency)*: Behavior cloning of successful memory recall decisions directly into the policy.
*   **Financial Applicability**: Instructs AlphaAlgo on which macro events or microstructural trades are worth logging into the Research Ledger, and how to query them dynamically.

---

### 4. SAGE: Self-evolving Agentic Graph-memory Engine (arXiv:2605.12061)
*   **Core Hypothesis**: Static Knowledge Graphs or RAG systems fail to capture dynamic, contextual market non-stationarity. Graph memory must be a self-evolving substrate governed by a Reader-Writer feedback loop.
*   **Mathematical Formulation**:
    *   Graph $G = (V, E)$. Nodes $v \in V$ represent claims, hypotheses, or assets. Edges $e = (u, r, v, w) \in E$ represent relations with dynamic weights $w \in [0, 1]$.
    *   Weight evolution: $w_{t+1} = (1 - \alpha) w_t + \alpha \cdot \text{Feedback}(u, r, v)$.
*   **Algorithms**: Parallel incremental graph writing (triplet extraction) coupled with online pruning (low-weight edge removal) and node merging (semantic clustering).
*   **Financial Applicability**: Dynamically constructs a market relation graph (e.g., asset correlations, lead-lag indicators) that adapts as market regimes change.

---

### 5. NanoResearch: Tri-level Co-evolving Research Automation (arXiv:2605.10813)
*   **Core Hypothesis**: Successful quantitative research requires co-evolution across three levels: compact Skill Programs (procedural), Project Memory (episodic/contextual), and Execution Policy.
*   **Mathematical Formulation**:
    *   Skill Space $\mathcal{S}$, Memory Space $\mathcal{M}$, Policy Space $\mathcal{P}$.
    *   Objective: $\max_{\mathcal{S}, \mathcal{M}, \mathcal{P}} \mathbb{E}_{\tau \sim \mathcal{P}(\cdot \mid \mathcal{S}, \mathcal{M})} [R(\tau)]$.
*   **Financial Applicability**: Allows AlphaAlgo to adapt its quantitative research generation and trading behavior to match localized execution constraints without full system recompilation.

---

### 6. AutoResearchClaw: Self-Reinforcing Autonomous Research (arXiv:2605.20025)
*   **Core Hypothesis**: Autonomous scientific research must be robust to failures and unexpected constraints; this is achieved through a structured Multi-Agent Debate and a self-healing Pivot/Refine loop.
*   **Mathematical Formulation**:
    *   Let $H_0$ be the initial hypothesis. Let $C(H)$ be the critic board evaluation.
    *   If $C(H) = \text{FAIL}$, the Pivot/Refine operator generates $H_{new} = \text{Pivot}(H, C(H))$ such that $\text{Sim}(H_{new}, H) < \delta$ (strategic divergence) to prevent endless repetitive loops.
*   **Financial Applicability**: Ensures trading agents handle sudden API disconnects, high slippage, or data anomalies by dynamically pivoting execution strategies.

---

### 7. HASP: Harnessing LLM Agents with Skill Programs (arXiv:2605.17734)
*   **Core Hypothesis**: Natural language guidance is too soft and failure-prone for high-stakes execution. Agents must be bounded by hard-coded, executable guardrails (Program Functions / PFs) that trigger automatically.
*   **Mathematical Formulation**:
    *   Let $s$ be the agent state. Let $PF_i(s)$ be a boolean trigger function.
    *   State intervention: If $PF_i(s) = \text{TRUE}$, policy action is overridden by $a = \pi_{PF_i}(s)$.
*   **Financial Applicability**: Hard-coded volatility overrides, exposure limits, or leverage caps that immediately preempt and override soft LLM-based trade proposals.

---

### 8. DeepWeb-Bench: Massive Cross-Source Evidence Benchmark (arXiv:2605.21482)
*   **Core Contribution**: Highlights that information retrieval is rarely the primary bottleneck in autonomous reasoning; 70% of reasoning failures result from poor derivation and low confidence calibration.
*   **Financial Applicability**: Justifies AlphaAlgo's "Evidence-First" architecture, demanding strict verification and multi-hop mathematical proof of trade expectancies before approving risk capital.

---

## Phase 2 — Gap Analysis

| Principle / Mechanism | mandatory Paper | Status in AlphaAlgo | Assessment & Gap Details |
| :--- | :--- | :--- | :--- |
| **Entropy-KL SFT Masking** | EKSFT (arXiv:2605.29303) | **Partially Implemented** | Standard SFT is present but without strict token-level Entropy-KL Union masking to protect exploratory capacity. |
| **Discrete-Continuous Recurrence** | DiscoLoop (arXiv:2607.00341) | **Already Implemented** | Implemented in `CognitiveSystemController` via `DiscoLoopCell` state looping. |
| **Automated Metamemory Optimization** | AutoMem (arXiv:2607.01224) | **Already Implemented** | Implemented via HMS `optimize_metamemory` schema version increments. |
| **Reader-Writer Graph Substrate** | SAGE (arXiv:2605.12061) | **Already Implemented** | Implemented in HMS via `SAGEGraphMemory` graph persistence and evolution. |
| **Skill-Memory-Policy Co-evolution**| NanoResearch (arXiv:2605.10813)| **Partially Implemented** | Core systems are co-evolving, but lacks full label-free parameter adaptation. |
| **Pivot/Refine Self-Healing** | AutoResearchClaw (2605.20025)| **Already Implemented** | Implemented in the CSC execution loop via `_refine_strategy`. |
| **Executable Program Functions** | HASP (arXiv:2605.17734) | **Already Implemented** | Implemented in `SkillRouter` via executable `volatility_guardrail` PFs. |
| **Calibrated Evidence Validation** | DeepWeb-Bench (2605.21482) | **Already Implemented** | Checked via `EvidenceGraphGate` demanding $\ge 80\%$ consensus. |

---

## Phase 3 — Scientific Synthesis: The UCA V5+ Unified Design

The **Unified Cognitive Architecture V5+ (UCA V5+)** integrates these eight papers into a single, high-performance strategic framework:

```
[ Market Observation ]
          │
          ▼
┌────────────────────────────────────────────────────────┐
│  Stage 0: HASP Volatility & Microstructure PFs        │  <── (Hard Guardrail Preemption)
└─────────────────────────┬──────────────────────────────┘
          │ (Passes)
          ▼
┌────────────────────────────────────────────────────────┐
│  SAGE Graph-Memory Query & Evidence Chain Retrieval    │  <── (Contextual Substrate)
└─────────────────────────┬──────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│  DiscoLoop Cell (Dual-Channel Recurrent Reasoning)     │  <── (Multi-Hop Latent Inference)
│  S_k = [h_k; e_k]                                      │
└─────────────────────────┬──────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│  Multi-Hypothesis & Scenario Simulation (CWMI)        │  <── (Exploration Space)
└─────────────────────────┬──────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│  Verification Swarm & Pivot/Refine Gate                │  <── (Self-Healing Consensus)
│  Demand >= 80% peer-review consensus                  │
└─────────────────────────┬──────────────────────────────┘
          │ (Approved)
          ▼
┌────────────────────────────────────────────────────────┐
│  LogAct Total-Ordered Shared Log (Execution Consensus) │  <── (Immutable Governance)
└────────────────────────────────────────────────────────┘
```

### Contradiction Resolution
*   *Soft Advisory vs. Hard Control*: Solved by placing HASP `ProgramFunctions` as Stage 0 pre-filters, while letting DiscoLoop soft reasoning handle complex trade patterns only in safe states.
*   *Static Context vs. Infinite Context*: Solved by utilizing AutoMem schema optimization and SAGE edge pruning, keeping the context window dense and relevant.

---

## Phase 4 — Refactoring Plan

### 1. Dependency Graph
```
[conftest.py] ──────────> [test_csc_v5.py]
                                │
                                ▼
[router.py] ────────────> [controller.py] <──────────── [memory.py]
```

### 2. Migration Graph
1.  **Stage 1**: Standardize types (`CoreDecision` defaults) in `alphaalgo_core_engine.py` to prevent positional parameter crashes.
2.  **Stage 2**: Implement nested wrapping inside `router.py` to support `test_router_v5.py` and prevent schema mismatching.
3.  **Stage 3**: Update `memory.py` to support programmatic version increments for `test_hms_v5.py`.
4.  **Stage 4**: Clean and unify parallel/duplicate execution pipelines inside `controller.py`.

### 3. Risk Analysis & Rollback Strategy
*   *Risk*: Multi-threaded execution locks or timeout hangs during LogAct consensus checks.
*   *Mitigation*: Restrict `wait_for_decision` mock to targeted test folders to prevent integration suite side effects.
*   *Rollback*: `git checkout HEAD -- trading_bot/core/csc/ controller.py` restores complete state.

### 4. Benchmark & Validation Plan
*   Execute the 6-part test suite inside `tests/uca_v5/` daily.
*   Performance Target: Consensus overhead < 2ms, memory footprint < 10MB.
