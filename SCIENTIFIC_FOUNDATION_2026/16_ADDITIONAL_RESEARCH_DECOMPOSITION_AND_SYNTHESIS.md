# 16. Additional Research Decomposition and Synthesis: AlphaAlgo Scientific Foundation (2026)

This document presents the complete 6-phase scientific integration, paper decomposition, and gap synthesis for the 8 mandatory research papers required for the Unified Cognitive Architecture (UCA V5) refactoring of AlphaAlgo.

---

## Phase 1 — Paper Decompositions

### 1. EKSFT: Entropy-KL Selective Fine-Tuning
*   **Reference**: arXiv:2605.29303 (2026)
*   **Core Hypothesis**: Standard Supervised Fine-Tuning (SFT) over-memorizes training tokens, leading to mode collapse and "distribution sharpening" (loss of exploration entropy). Restricting SFT updates to tokens with high task-relevant information (measured by entropy and KL divergence) activates latent capabilities without destroying the policy's exploration capabilities.
*   **Mathematical Formulation**:
    Let $P_{\theta}(t | x)$ be the target model and $P_{ref}(t | x)$ be a reference model.
    A token $t$ is included in the SFT update mask $\mathcal{M}$ if it falls into the top-K percentile of:
    $$\mathcal{M}_H = \{ t : -\sum_j P(t_j) \log P(t_j) > \gamma_H \}$$
    $$\mathcal{M}_{KL} = \{ t : D_{KL}(P_{\theta}(t|x) \parallel P_{ref}(t|x)) > \gamma_{KL} \}$$
    The union set $\mathcal{M} = \mathcal{M}_H \cup \mathcal{M}_{KL}$ determines the loss mask:
    $$\mathcal{L}_{EKSFT} = \sum_{t \in \mathcal{M}} - \log P_{\theta}(t | x) - \lambda_H \mathcal{H}(P_{\theta}) + \lambda_{KL} \mathcal{L}_{KL}^{mask}$$
*   **Training Methodology & Learning Algorithm**: Gradient descent with dynamic masking over the sequence. Evaluates KL drift against reference model checkpoints.
*   **Memory Architecture**: Requires a dual-checkpoint reference policy memory.
*   **Planning Architecture**: Constrains action priors, protecting reasoning steps from over-optimization.
*   **Agent Architecture**: Applied during post-training behavioral alignment.
*   **World Model Contribution**: Protects predictive world model distributions from narrowing down (retaining multi-scenario imagination).
*   **Self-Improvement**: Prevents RL from getting trapped in "delusion loops" by guaranteeing a minimum exploration entropy.
*   **Failure Modes**: Over-masking ($\rho > 0.35$) causes training divergence; under-masking reverts to standard SFT.
*   **Scalability Limits / Computational Complexity**: Requires a reference model forward pass, doubling training cost ($O(2N)$ compute).
*   **Engineering Tradeoffs**: Trading raw sample throughput for higher alignment quality and downstream RL stability.
*   **Financial Applicability**: Prevents a trading agent from memorizing specific price paths, learning general market logic instead.
*   **Production Readiness**: Highly ready. Easily integrated into standard SFT pipelines.

---

### 2. DiscoLoop: Looping Discrete Embeddings and Continuous Hidden States
*   **Reference**: arXiv:2607.00341 (2026)
*   **Core Hypothesis**: Standard Transformers suffer from depth-local storage limits and cannot easily do multi-hop causal inference in a single pass. Mixed-channel looping (Discrete Symbolic Tokens + Continuous Hidden Embeddings) solves this representational bottleneck.
*   **Mathematical Formulation**:
    At loop step $k$:
    $$S_k = [h_k; e_k]$$
    $$h_{k+1} = \tanh(W_h h_k + W_e e_k + b_h)$$
    $$e_{k+1} = \text{gumbel-softmax}(W_d h_{k+1} + b_d)$$
    where $h_k$ is the continuous state and $e_k$ is the discrete symbolic token embedding.
*   **Training Methodology & Learning Algorithm**: BPTT (Backpropagation Through Time) over a fixed unrolled loop size ($K \le 5$). Includes a training-free realignment intervention step to close generalization gaps.
*   **Memory Architecture**: Integrated short-term working memory recurrence.
*   **Planning Architecture**: Provides a multi-step "thinking space" within a single strategic execution block.
*   **Agent Architecture**: The core strategic reasoning backbone.
*   **World Model Contribution**: Loops continuous latent states (market regimes) alongside discrete events (news, blocks).
*   **Self-Improvement**: The loop depth $K$ can be dynamically scaled based on the calculated surprise.
*   **Failure Modes**: Vanishing/exploding gradients over deep loops; token collapse in the discrete channel.
*   **Scalability Limits / Complexity**: Scales linearly with loop depth $O(K \cdot d^2)$.
*   **Engineering Tradeoffs**: Adds local latency but reduces context-window usage significantly.
*   **Financial Applicability**: Allows real-time correlation tracing (e.g., USD rise $\to$ Gold drop $\to$ Hedging active) within a single execution sweep.
*   **Production Readiness**: High. Replaces pure textual chains of thought with fast, structured numerical loops.

---

### 3. AutoMem: Automated Learning of Memory as a Cognitive Skill
*   **Reference**: arXiv:2607.01224 (2026)
*   **Core Hypothesis**: Memory management should not be governed by hardcoded heuristic algorithms. Memory must be treated as an independently learnable cognitive skill (metamemory) optimized via reinforcement learning.
*   **Mathematical Formulation**:
    Exposes read, write, and schema update operations as first-class actions $a_m \in \mathcal{A}$.
    The objective function maximizes downstream task success reward:
    $$J(\theta_{mem}) = \mathbb{E}_{\tau \sim \pi_{\theta}} \left[ \sum_{t} \gamma^t R(s_t, a_t) \right]$$
*   **Training Methodology & Learning Algorithm**: Dual-loop optimization. Loop 1 parses trajectories to identify schemas; Loop 2 behaviorally clones memory decisions.
*   **Memory Architecture**: Operates directly on the 6-tier hierarchical memory system.
*   **Planning Architecture**: Agents plan *how* and *when* to record evidence.
*   **Agent Architecture**: Enhances the agent with a dedicated memory control unit.
*   **World Model Contribution**: Records causal connections to improve predictive accuracy.
*   **Self-Improvement**: The agent dynamically alters its retrieval schema over time based on actual utility.
*   **Failure Modes**: Memory "cluttering" (over-storing noise); deletion of high-importance long-term context.
*   **Scalability Limits / Complexity**: $O(N \log N)$ where $N$ is the number of stored memories.
*   **Engineering Tradeoffs**: Code complexity vs. optimal retrieval density.
*   **Financial Applicability**: Learns to index specific regime transitions and ignore daily price fluctuations.
*   **Production Readiness**: Ready. Already aligned with HMS V5.

---

### 4. SAGE: Self-evolving Agentic Graph-memory Engine
*   **Reference**: arXiv:2605.12061 (2026)
*   **Core Hypothesis**: Flat RAG databases cannot capture non-stationary topological relationships. SAGE couples an incremental Memory Writer (graph construction) with a Graph Foundation Model (GFM) Memory Reader (feedback to prune and merge) to achieve a self-evolving memory substrate.
*   **Mathematical Formulation**:
    Graph $G = (V, E)$. Let each edge $e = (u, v, r, c)$ have relationship $r$ and validity context $c$.
    Topology updates are triggered when validation accuracy falls below threshold:
    $$\text{Prune}(e) \iff \text{Utility}(e) < \gamma_p$$
    $$\text{Merge}(u, v) \iff \text{Cosine}(h_u, h_v) > \gamma_m$$
*   **Training Methodology & Learning Algorithm**: Active topological pruning. Relies on an explicit evaluation feedback matrix.
*   **Memory Architecture**: Replacing flat memory with a directed MultiDiGraph.
*   **Planning Architecture**: Generates causal reasoning graphs that map to actual trade constraints.
*   **Agent Architecture**: Provides a rich network of relations to specialist agents.
*   **World Model Contribution**: Operates as the structural backbone of the world model's causal assumptions.
*   **Self-Improvement**: Dynamically prunes obsolete market relationships (e.g., stale correlations).
*   **Failure Modes**: Infinite contraction of nodes (collapsing the graph into a single node); massive cycles.
*   **Scalability Limits / Complexity**: Graph traversal complexity is bounded at $O(|V| + |E|)$ via K-hop lookups.
*   **Engineering Tradeoffs**: Higher retrieval latency vs. structured and robust context delivery.
*   **Financial Applicability**: Allows AlphaAlgo to maintain an evolving correlation map of currency and crypto pairs.
*   **Production Readiness**: Fully ready. Utilizes python's `networkx` for fast local subgraphs.

---

### 5. NanoResearch: Tri-level Co-evolving Research Automation
*   **Reference**: arXiv:2605.10813 (2026)
*   **Core Hypothesis**: Autonomous quantitative research is not a single-agent task; it requires tri-level co-evolution of procedural Skills (Bank), experiences (Memory), and behavioral Policies.
*   **Mathematical Formulation**:
    Let $S$ be the skill set, $M$ the memory pool, and $\pi_{\theta}$ the policy.
    The co-evolution loop maximizes target portfolio metrics via:
    $$\max_{S, M, \pi_{\theta}} \mathcal{U}(S, M, \pi_{\theta})$$
*   **Training Methodology & Learning Algorithm**: Iterative reinforcement learning and schema-based skill discovery.
*   **Memory Architecture**: Connects short-term execution logs directly with institutional recommendations.
*   **Planning Architecture**: High-level task breakdown with independent specialist execution.
*   **Agent Architecture**: A fleet of specialist agents (e.g., London Session Specialist, Risk Agent).
*   **World Model Contribution**: Evaluates synthetic market environments.
*   **Self-Improvement**: Automatically discovers, refines, and stores new programmatic functions (Skills).
*   **Failure Modes**: Over-optimization of narrow trading skills resulting in extreme tail-risk exposure.
*   **Scalability Limits / Complexity**: Bounded by available compute.
*   **Engineering Tradeoffs**: Generality vs. absolute specialisation.
*   **Financial Applicability**: Supports automated strategy parameter discovery and optimization.
*   **Production Readiness**: Moderate. Best utilized as an offline research coordinator.

---

### 6. AutoResearchClaw: Self-Reinforcing Autonomous Research
*   **Reference**: arXiv:2605.20025 (2026)
*   **Core Hypothesis**: Quantitative execution is failure-prone due to API shifts and market volatility. Integrating a "Pivot/Refine" decision loop allows the system to dynamically self-heal mid-flight.
*   **Mathematical Formulation**:
    Let $P$ be a proposed plan. If verifiers return negative feedback $F$, trigger pivot operator:
    $$\text{Pivot}(P, F) \to P' \text{ s.t. } \text{Match}(P', F) = \emptyset$$
*   **Training Methodology & Learning Algorithm**: Multi-perspective debate and evolutionary planning refinement.
*   **Memory Architecture**: Feeds plan failures directly into the failure database.
*   **Planning Architecture**: Hierarchical execution with dynamic fallback routes.
*   **Agent Architecture**: Incorporates an adversarial verifier swarm.
*   **World Model Contribution**: Simulates hypothetical alternative scenarios when a veto is triggered.
*   **Self-Improvement**: Directly heals coding or planning bugs.
*   **Failure Modes**: Deadlock loops where plan $P \to P' \to P$ repeats infinitely. Bounded at 3 iterations max.
*   **Scalability Limits / Complexity**: $O(I \cdot B)$ where $I$ is iterations and $B$ is verifier branches.
*   **Engineering Tradeoffs**: Slightly increased processing latency during high-conflict debates.
*   **Financial Applicability**: Allows mid-flight trade adaptation when execution parameters (slippage, liquidity) degrade.
*   **Production Readiness**: Extremely high. Already utilized in CSC V5.

---

### 7. HASP: Harnessing LLM Agents with Skill Programs
*   **Reference**: arXiv:2605.17734 (2026)
*   **Core Hypothesis**: Advisory textual prompts are easily bypassed or ignored by agents under stress. Agents require non-bypassable, executable `ProgramFunctions` (PFs) that activate on safety-critical states.
*   **Mathematical Formulation**:
    Let $s \in \mathcal{S}$ be the current system state.
    $$A(s) = \begin{cases} \text{PF}_i(s) & \text{if } \text{Trigger}_i(s) = \text{True} \\ \pi_{\theta}(s) & \text{otherwise} \end{cases}$$
*   **Training Methodology**: Direct software integration of programmatic contracts.
*   **Memory Architecture**: Skill programs are registered in the authoritative procedural memory tier.
*   **Planning Architecture**: Short-circuits regular LLM planning when safety limits are approached.
*   **Agent Architecture**: Upgrades the agent with an executable guardrail registry.
*   **World Model Contribution**: Operates as hard boundaries in simulation loops.
*   **Self-Improvement**: Generates new PFs when repeated policy mistakes are identified.
*   **Failure Modes**: Stale triggers causing unnecessary lockouts; flawed PFs crashing the process.
*   **Scalability Limits / Complexity**: $O(1)$ constant-time trigger checks.
*   **Engineering Tradeoffs**: Hard safety guarantees vs. flexibility.
*   **Financial Applicability**: Absolute enforcement of draw-down and volatility trade blocks.
*   **Production Readiness**: Excellent. Safe and deterministic.

---

### 8. DeepWeb-Bench: Massive Cross-Source Evidence Benchmark
*   **Reference**: arXiv:2605.21482 (2026)
*   **Core Hypothesis**: The primary bottleneck of complex agent reasoning is not retrieval itself, but derivation, synthesis, and confidence calibration. Systems must be tested against multi-dimensional benchmark tasks.
*   **Mathematical Formulation**:
    Evaluates agents across four core metrics:
    $$\text{Score} = w_r \cdot R + w_d \cdot D + w_c \cdot C + w_a \cdot A$$
    where $R$ is retrieval, $D$ is derivation, $C$ is calibration, and $A$ is accuracy.
*   **Training Methodology**: Post-training calibration alignment.
*   **Memory Architecture**: Feeds complex multi-hop evidence tables to the agent.
*   **Planning Architecture**: Long-horizon reasoning validation.
*   **Agent Architecture**: Evaluates agent capability levels.
*   **World Model Contribution**: Stresses world-model prediction accuracy.
*   **Self-Improvement**: Benchmarks learning velocity.
*   **Failure Modes**: Evaluates calibration errors.
*   **Financial Applicability**: Evaluates the correctness of trading hypotheses before committing capital.
*   **Production Readiness**: Diagnostic suite. Highly ready.

---

## Phase 2 — Gap Analysis Matrix

Comparing AlphaAlgo's current implementation against these principles yields the following gap matrix:

| Principle / Paper | Implementation Status | AlphaAlgo Current Code | Required Upgrade (UCA V5) |
| :--- | :--- | :--- | :--- |
| **Entropy-KL SFT** (EKSFT) | **Missing entirely** | Standard PyTorch stubs in risk/ML modules. | Add dynamic Entropy-KL masking inside post-training pipelines and stubs. |
| **Discrete-Continuous Loops** (DiscoLoop) | **Partially implemented** | Flat iterative loop in CSC `controller.py`. | Fully integrate continuous state embeddings and Gumbel-Softmax discrete tokens. |
| **Metamemory Skills** (AutoMem) | **Partially implemented** | Static memory tiers in HMS `memory.py`. | Promote schema changes and optimizations to first-class actions. |
| **Self-Evolving Graph-Memory** (SAGE) | **Partially implemented** | NetworkX stubs with basic write functionality. | Implement actual pruning, merging, and context-dependent validity logic. |
| **Pivot/Refine Decisions** (AutoResearchClaw) | **Partially implemented** | Mocked loop in `controller.py`. | Ensure the Pivot/Refine loop handles actual verifier feedback and re-routes. |
| **Skill Programs (PFs)** (HASP) | **Partially implemented** | Hardcoded volatility check in `controller.py`. | Upgrade `SkillRouter` to strictly register and execute PFs under nested result envelopes. |

---

## Phase 3 — Scientific Synthesis (Unified Architecture)

The Unified Cognitive Architecture (UCA V5) synthesizes these principles into a single, high-performance system:

1.  **Dual-Channel Reasoning**: The strategic brain (`controller.py`) loops symbolic tokens and continuous representations using the **DiscoLoop** architecture, minimizing Surprises.
2.  **Safety-First Guardrails**: text-based LLM recommendations are verified by **HASP** executable programs registered in `router.py`. High-volatility states trigger instant non-bypassable overrides.
3.  **Active Memory Evolution**: Stored evidence is structured as a Directed MultiDiGraph in the **SAGE** engine. Stale market correlations are actively pruned, and similar nodes are merged based on semantic similarity.
4.  **Self-Healing Executive Loop**: If the **Verifier Swarm** rejects a trading plan, the system uses the **Pivot/Refine** loop to generate an alternative hypothesis before execution is aborted.

---

## Phase 4 — Refactoring Plan

### 1. Dependency Graph
```
[SkillRouter (HASP/S2L)] ──> [CognitiveSystemController (DiscoLoop)]
                                     │
                                     ▼
                      [HierarchicalMemorySystem (SAGE/AutoMem)]
```

### 2. Migration Graph
1.  **Step 1**: Align `SkillRouter` return structures with nested `"result"` envelopes.
2.  **Step 2**: Enhance `HierarchicalMemorySystem` with SAGE edge pruning and AutoMem optimizations.
3.  **Step 3**: Connect the CSC controller to short-circuit instantly on HASP overrides.
4.  **Step 4**: Verify all v5 unit tests (`test_csc_v5.py`, `test_router_v5.py`, `test_hms_v5.py`).

### 3. Risk & Rollback Strategy
*   **Risk**: Complex loop structures increasing execution latency.
*   **Mitigation**: Limit DiscoLoop depth to $K \le 3$.
*   **Rollback**: Standard git-reversion of modified files in `trading_bot/core/`.

---

## Phase 5 & 6 — Implementation and Verification

The code changes and unit tests are comprehensively implemented, aligned, and verified green in the AlphaAlgo system.
