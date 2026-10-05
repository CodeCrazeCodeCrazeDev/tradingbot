# Phase 1: Mandatory and Extended Papers Engineering Decomposition (2026)

This document provides a thorough, zero-loss engineering decomposition for each of the eight mandatory papers and key extended citations to serve as the blueprint for AlphaAlgo.

---

## 1. EKSFT: Entropy-KL Selective Fine-Tuning
* **Reference**: arXiv:2605.29303 (2026)
* **Core Hypothesis**: Standard Supervised Fine-Tuning (SFT) overfits models to specific historical token sequences, causing entropy collapse and distribution sharpening. Selecting tokens based on high entropy $H(t)$ or high KL-divergence $D_{KL}(P_{\theta} \parallel P_{ref})$ for selective masking preserves policy exploration capacity.
* **Mathematical Formulation**:
  - Masking Set: $\mathcal{M} = \{t \mid H(t) > \tau_H \lor D_{KL}(P_{\theta}(t) \parallel P_{ref}(t)) > \tau_{KL}\}$
  - Loss Function: $\mathcal{L}_{EKSFT} = \frac{1}{|\mathcal{D} \setminus \mathcal{M}|} \sum_{t \notin \mathcal{M}} \mathcal{L}_{CE}(t) - \lambda_H H(t) + \lambda_{KL} D_{KL}(P_{\theta}(t) \parallel P_{ref}(t))$
* **Training Methodology**: Dual-model autoregressive fine-tuning using an active policy model and a frozen baseline reference model.
* **Learning Algorithm**: AdamW optimizer with dynamic cosine learning rate annealing over unmasked token indices.
* **Memory Architecture**: Parametric weights bounded by reference distribution anchor.
* **Planning Architecture**: Action generation step masking.
* **Agent Architecture**: Post-training alignment adapter.
* **World Model Contribution**: Protects stochastic transition predictions from over-fitting to noisy historical regimes.
* **Self-Improvement Contribution**: Prevents self-reinforcing delusion loops in recursive self-rewriting.
* **Failure Modes**: Over-masking (>35% token suppression) leads to underfitting.
* **Scalability Limits**: $\mathcal{O}(2 \cdot N_{params})$ VRAM memory footprint during training.
* **Computational Complexity**: Linear in sequence length and vocabulary size.
* **Engineering Tradeoffs**: Bounded policy drift at the cost of 2x parameter memory requirement during training.
* **Financial Applicability**: Prevents trading agents from memorizing specific market paths while learning generalized regime-aware reasoning.
* **Production Readiness**: Production ready; implemented via EKSFT compliance checks in `EvolutionGate`.

---

## 2. DiscoLoop: Discrete Embeddings and Continuous Hidden States
* **Reference**: arXiv:2607.00341 (2026)
* **Core Hypothesis**: Coupling discrete symbolic embedding channels with continuous hidden states inside a recurrent loop allows models to internalize multi-step causal reasoning without context window bloat.
* **Mathematical Formulation**:
  - Continuous Recurrence: $h_{k+1} = \tanh(W_h h_k + W_e e_k + W_x x)$
  - Discrete Token Selection: $e_{k+1} = \text{Quantize}(W_d h_{k+1})$
  - Dual State: $S_k = [h_k ; e_k]$
* **Training Methodology**: Straight-Through Estimator (STE) gradient pass for discrete quantization.
* **Learning Algorithm**: Recurrent vector-quantized variational optimization.
* **Memory Architecture**: Split-channel working memory (discrete symbolic channel + continuous latent state).
* **Planning Architecture**: Loop-based multi-hop internal sub-planning.
* **Agent Architecture**: Epistemic core executing internal reflection before external action.
* **World Model Contribution**: Captures continuous dynamics while discretizing regime transition boundaries.
* **Self-Improvement Contribution**: Supports internal virtual rollouts.
* **Failure Modes**: Quantization drift over $k > 10$ steps.
* **Scalability Limits**: Linear in loop depth $k$.
* **Computational Complexity**: $\mathcal{O}(k \cdot D^2)$ per decision cycle.
* **Engineering Tradeoffs**: Higher reasoning depth vs additional CPU/GPU cycle latency.
* **Financial Applicability**: Enables fast multi-hop causal reasoning (News Event $\to$ Sector Shift $\to$ Order Flow Impact).
* **Production Readiness**: Implemented via `DiscoLoopCell` in `CognitiveSystemController`.

---

## 3. AutoMem: Automated Learning of Memory as a Cognitive Skill
* **Reference**: arXiv:2607.01224 (2026)
* **Core Hypothesis**: Memory operations (Write, Read, Condense, Purge) should be treated as dynamic, learnable metamemory skills rather than static DB retrievals.
* **Mathematical Formulation**:
  - Metamemory Policy: $\pi_{\phi}(a_m \mid s)$
  - Schema Optimization: $\max_{\phi} \mathbb{E}_{\tau} [R(\tau) - \beta \cdot \text{Cost}(\mathcal{M}_{\phi})]$
* **Training Methodology**: RL over structured memory manipulation actions.
* **Learning Algorithm**: Dual-loop policy iteration (Loop 1: schema revision, Loop 2: execution proficiency).
* **Memory Architecture**: Dynamic hierarchical storage (Working, Episodic, Semantic, Institutional).
* **Planning Architecture**: Feeds historical plan templates into active planning context.
* **Agent Architecture**: Metamemory-augmented cognitive controller.
* **World Model Contribution**: Indexes verified causal triplets to update world model transition matrices.
* **Self-Improvement Contribution**: Eliminates stale or low-utility memory nodes.
* **Failure Modes**: Over-aggressive pruning during regime shifts.
* **Scalability Limits**: Bounded by graph indexing limits.
* **Computational Complexity**: $\mathcal{O}(\log N)$ retrieval, $\mathcal{O}(N)$ optimization.
* **Engineering Tradeoffs**: Dynamic schema adaptability vs memory lock overhead.
* **Financial Applicability**: Learns which trading experiences are worth persisting in the Research Ledger.
* **Production Readiness**: Implemented in `HierarchicalMemorySystem`.

---

## 4. SAGE: Self-evolving Agentic Graph-memory Engine
* **Reference**: arXiv:2605.12061 (2026)
* **Core Hypothesis**: Knowledge should be stored in a dynamic, self-evolving evidence graph where edge weights adapt based on execution rewards.
* **Mathematical Formulation**:
  - Edge Weight Update: $W_{t+1}(u, v) = W_t(u, v) + \eta \cdot (\text{Reward}_{feedback} - W_t(u, v))$
  - Subgraph Relevance: $R(n) = \text{Sim}(q, n) + \sum_{m \in \mathcal{N}(n)} w_{nm} \cdot \text{Sim}(q, m)$
* **Training Methodology**: Online Hebbian-style weight updates + offline compaction.
* **Learning Algorithm**: Autonomous weight evolution with low-utility edge pruning ($W < 0.1$).
* **Memory Architecture**: Causal Evidence Knowledge Graph.
* **Planning Architecture**: Graph traversal path planning.
* **Agent Architecture**: Graph-native reasoning engine.
* **World Model Contribution**: Maps causal connections between market variables.
* **Self-Improvement Contribution**: Continuous structural refinement of domain knowledge.
* **Failure Modes**: Monopoly node formation (dense clusters causing retrieval bias).
* **Scalability Limits**: Efficient up to $10^5$ nodes in NetworkX.
* **Computational Complexity**: $\mathcal{O}(V + E)$ multi-hop traversal.
* **Engineering Tradeoffs**: Contextually rich retrieval vs graph write-lock overhead.
* **Financial Applicability**: Tracks non-stationary relationships across global macro assets.
* **Production Readiness**: Implemented in `SAGEGraphMemory` within `HMS`.

---

## 5. NanoResearch: Tri-level Co-evolving Research Automation
* **Reference**: arXiv:2605.10813 (2026)
* **Core Hypothesis**: Research automation requires co-evolution across three distinct planes: Skill Bank (procedural rules), Memory Module (experience), and Policy (preference internalization).
* **Mathematical Formulation**: $\max_{\theta, \mathcal{S}, \mathcal{M}} \mathcal{U}(\theta, \mathcal{S}, \mathcal{M})$
* **Training Methodology**: DPO + evolutionary rule discovery.
* **Memory Architecture**: Co-evolving experience ledger.
* **Financial Applicability**: Customizes strategies to institutional risk mandates.
* **Production Readiness**: Integrated into `SkillRouter` and `EvolutionGate`.

---

## 6. AutoResearchClaw: Self-Reinforcing Autonomous Research
* **Reference**: arXiv:2605.20025 (2026)
* **Core Hypothesis**: Autonomous discovery requires iterative self-healing loops (Pivot/Refine) and structured multi-agent adversarial debate.
* **Mathematical Formulation**: Pivot trigger: $\mathbb{P}(\text{Failure} \mid \text{Critique}) > \tau_{pivot} \implies \text{Pivot}(\text{Strategy})$
* **Training Methodology**: Self-play with adversarial red-teaming.
* **Financial Applicability**: Pivots trade execution mid-flight when slippage or risk spikes occur.
* **Production Readiness**: Implemented via `_pivot_refine_loop` in `CSC` and `MultiAgentDebateSystem`.

---

## 7. HASP: Harnessing LLM Agents with Skill Programs
* **Reference**: arXiv:2605.17734 (2026)
* **Core Hypothesis**: Natural language guardrails are advisory; agents require executable Program Functions (PFs) that intercept and override invalid states.
* **Mathematical Formulation**: $a_{final} = \text{PF}(a_{agent}, s_t) \text{ if } \text{Trigger}(s_t) = 1 \text{ else } a_{agent}$
* **Training Methodology**: Deterministic invariant synthesis.
* **Financial Applicability**: Hard risk guardrails that override trade orders during high volatility.
* **Production Readiness**: Implemented in `SkillRouter` and `HASPExecutor`.

---

## 8. DeepWeb-Bench: Massive Cross-Source Evidence Benchmark
* **Reference**: arXiv:2605.21482 (2026)
* **Core Contribution**: Benchmark revealing that 70% of reasoning failures stem from derivation and calibration errors.
* **Mathematical Formulation**: $\text{ECE} = \sum_{b=1}^B \frac{|B_b|}{N} | \text{acc}(B_b) - \text{conf}(B_b) |$
* **Financial Applicability**: Calibrates confidence scores against true historical win probabilities.
* **Production Readiness**: Implemented in `EvolutionGate` (`compute_ece`).
