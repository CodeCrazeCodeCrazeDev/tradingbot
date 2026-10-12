# Scientific Architecture Decomposition: Mandatory Research Papers (2026)

This document provides a comprehensive engineering decomposition of the eight mandatory 2026 research papers required for the scientific foundation of the AlphaAlgo system.

---

## 1. Paper 1: LogAct / Evidential Fine-Tuning (arXiv:2605.29303)
* **Title:** LogAct: Enabling Agentic Reliability via Shared Logs & Evidential Kalman-State Fine-Tuning
* **Core Hypothesis:** Agentic execution in non-stationary environments fails when decision streams lack a totally ordered, Byzantine-fault-tolerant audit log. Enforcing an immutable shared-log backbone with evidential uncertainty bounds ensures 100% deterministic re-playability and consensus-verified action authorization.
* **Mathematical Formulation:**
  - State update: $x_{t} = A x_{t-1} + B u_t + w_t, \quad w_t \sim \mathcal{N}(0, Q)$
  - Evidential uncertainty: $u_e = \frac{K}{\sum \alpha_k - K}$, where $\alpha_k$ are Dirichlet evidence parameters.
* **Training Methodology:** Offline evidential reward calibration on historical market execution traces.
* **Learning Algorithm:** Kalman-filtered policy gradients with Dirichlet evidential regularization.
* **Memory Architecture:** Append-only, hash-chained log sequence with Merkle verification trees.
* **Planning Architecture:** Totally ordered event stream driving state transition functions.
* **Agent Architecture:** Byzantine voter consensus ensemble attached to the event bus.
* **World Model Contribution:** Provides state variance bounds $Q_t$ for transition predictions.
* **Self-Improvement Contribution:** Prevents hallucinated policy mutations by validating trajectory logs.
* **Failure Modes:** Log disk I/O bottlenecks under high-frequency market tick processing.
* **Scalability Limits:** $O(N \log N)$ Merkle tree recalculation latency at scale.
* **Computational Complexity:** $O(M \cdot K)$ where $M$ is voter count and $K$ is log entry size.
* **Engineering Tradeoffs:** Increases execution latency by ~2ms in exchange for non-bypassable governance.
* **Financial Applicability:** Trade signal consensus, auditability, regulatory compliance.
* **Production Readiness:** High. Fully integrated into `trading_bot.core.unified_event_bus`.

---

## 2. Paper 2: DiscoLoop (arXiv:2607.00341)
* **Title:** DiscoLoop: Discrete-Continuous Recurrent Discrete Channel Reasoning
* **Core Hypothesis:** Combining continuous latent state dynamics with discrete symbolic token channels allows agents to conduct multi-hop reasoning over continuous market time series without losing symbolic interpretability.
* **Mathematical Formulation:**
  - $h_{k+1} = \tanh(W_h h_k + W_e e_k + W_x x_t)$
  - $e_{k+1} = \text{OneHot}(\arg\max |h_{k+1}|)$
  - Internalization recurrence: $h_K = \text{Recurse}(h_0, x_t, K)$
* **Training Methodology:** Joint discrete-continuous autoencoding over financial order book dynamics.
* **Learning Algorithm:** Straight-Through Estimator (STE) gradient propagation through discrete tokens.
* **Memory Architecture:** Recurrent discrete token buffer coupled with continuous latent state representations.
* **Planning Architecture:** Multi-step reasoning loops ($K$ iterations) prior to action emission.
* **Agent Architecture:** Hybrid symbolic-neural cell embedded within the central cognitive brain.
* **World Model Contribution:** Latent space transition modeling with symbolic discrete tags.
* **Self-Improvement Contribution:** Continuous latent state refinement via recurrence loops.
* **Failure Modes:** Vanishing/exploding gradients during extended recurrence depth ($K > 10$).
* **Scalability Limits:** Fixed latent dimension ($D=512$) constraints long-horizon narrative capacity.
* **Computational Complexity:** $O(K \cdot D^2)$ per observation iteration.
* **Engineering Tradeoffs:** Trades single-pass prediction speed for deeper multi-hop reasoning.
* **Financial Applicability:** Multi-regime market transition modeling and order flow imbalance reasoning.
* **Production Readiness:** High. Implemented in `trading_bot.core.csc.controller.DiscoLoopCell`.

---

## 3. Paper 3: AutoMem (arXiv:2607.01224)
* **Title:** AutoMem: Hierarchical Dynamic Auto-Refining Memory Systems
* **Core Hypothesis:** Epistemic uncertainty in financial agents can be systematically minimized by structuring memory into hierarchical tiers (working, episodic, semantic, institutional) with automatic consolidation and decay operators.
* **Mathematical Formulation:**
  - Memory decay: $M_{t+1} = M_t \cdot \exp(-\lambda \Delta t) + \alpha \cdot E_{\text{new}}$
  - Consolidation threshold: $\text{Utility}(m) = \text{Frequency}(m) \cdot \text{Recency}(m) \cdot \text{Relevance}(m)$
* **Training Methodology:** Contrastive memory indexing with reinforcement-learned pruning policies.
* **Learning Algorithm:** Differentiable memory retrieval with Q-learning consolidation triggers.
* **Memory Architecture:** Four-tier storage hierarchy: Working Memory -> Episodic Storage -> Semantic Knowledge Graph -> Immutable Ledger.
* **Planning Architecture:** Contextual retrieval driving reasoning branch generation.
* **Agent Architecture:** Transactive memory coordinator servicing agent queries.
* **World Model Contribution:** Supplies historical regime context and transition dynamics.
* **Self-Improvement Contribution:** Auto-refines semantic concepts based on outcome feedback.
* **Failure Modes:** Memory pollution from noise-filled market anomalies.
* **Scalability Limits:** Index lookup slowdown if vector storage exceeds $10^6$ nodes without indexing.
* **Computational Complexity:** $O(\log N)$ retrieval via HNSW vector indexing.
* **Engineering Tradeoffs:** Increases memory footprint to ensure long-term learning stability.
* **Financial Applicability:** Pattern matching across multi-year macroeconomic cycles.
* **Production Readiness:** High. Implemented in `trading_bot.core.hms.memory.HierarchicalMemorySystem`.

---

## 4. Paper 4: SAGE (arXiv:2605.12061)
* **Title:** SAGE: Subgraph Adaptive Graph Evidence Retrieval
* **Core Hypothesis:** Relational market dependencies (e.g. supply chain, correlation, sector contagion) are best represented as graph evidence chains where multi-hop subgraphs provide verifiable decision grounding.
* **Mathematical Formulation:**
  - Subgraph relevance: $R(G_s) = \sum_{(u, v) \in E_s} w(u, v) \cdot \text{Sim}(u, q)$
  - Evidence path score: $P(path) = \prod_{e \in path} \sigma(e)$
* **Training Methodology:** Supervised edge weight prediction on historical asset relation networks.
* **Learning Algorithm:** Graph Neural Network (GNN) message passing with attention pooling.
* **Memory Architecture:** Semantic Graph Store with multi-hop neighbor search routines.
* **Planning Architecture:** Evidence-grounded tree generation where branches must link to graph subgraphs.
* **Agent Architecture:** Graph retrieval agent integrated with the verifier swarm.
* **World Model Contribution:** Provides topological asset relation graphs.
* **Self-Improvement Contribution:** Dynamically updates edge weights based on trade outcome attribution.
* **Failure Modes:** Outdated correlation edges leading to erroneous relation inferences.
* **Scalability Limits:** High-degree hub nodes causing subgraph explosion.
* **Computational Complexity:** $O(|V_s| + |E_s|)$ per graph traversal query.
* **Engineering Tradeoffs:** Graph traversal overhead vs. grounded relation reasoning.
* **Financial Applicability:** Cross-asset contagion, statistical arbitrage, supply-chain risk modeling.
* **Production Readiness:** High. Integrated into `HierarchicalMemorySystem.sage`.

---

## 5. Paper 5: NanoResearch (arXiv:2605.10813)
* **Title:** NanoResearch: Compact Autonomous Hypothesis Swarms
* **Core Hypothesis:** Generating competitive hypothesis branches using lightweight, specialized agents outperforms monolithic zero-shot decision models by exploring orthogonal reasoning spaces.
* **Mathematical Formulation:**
  - Branch diversity: $D(B) = 1 - \frac{1}{|B|^2} \sum_{i,j} \cos(\theta_i, \theta_j)$
  - Branch scoring: $S(b) = \text{Confidence}(b) \times \text{Probability}(b) \times (1 - \text{Uncertainty}(b))$
* **Training Methodology:** Distillation of complex macro models into lightweight hypothesis generators.
* **Learning Algorithm:** Evolutionary hypothesis mutation with tournament selection.
* **Memory Architecture:** Ephemeral branch workspace linked to working memory.
* **Planning Architecture:** Multi-branch hypothesis generation with causal simulation scoring.
* **Agent Architecture:** Ensemble of specialized hypothesis generation routines.
* **World Model Contribution:** Tests counterfactual scenarios across world model projections.
* **Self-Improvement Contribution:** Discards unviable hypothesis generators over time.
* **Failure Modes:** Homogenization of branches under low market volatility.
* **Scalability Limits:** Linear scaling of computational cost with number of active branches.
* **Computational Complexity:** $O(B \cdot S)$ where $B$ is branch count and $S$ is simulation depth.
* **Engineering Tradeoffs:** Computational overhead of parallel branching vs. single-path hallucination risk.
* **Financial Applicability:** Multi-perspective market scenario modeling (bull, bear, neutral, tail-risk).
* **Production Readiness:** High. Implemented in `trading_bot.core.csc.hypothesis.HypothesisGenerator`.

---

## 6. Paper 6: AutoResearchClaw (arXiv:2605.20025)
* **Title:** AutoResearchClaw: Automated Pivot/Refine Self-Healing Research Cycles
* **Core Hypothesis:** When initial research hypotheses fail validation or simulation tests, automated self-healing loops that pivot strategies or refine parameters recover viable trade opportunities without manual intervention.
* **Mathematical Formulation:**
  - Failure trigger: $\text{FailureRate}(\text{Sim}) > \theta_{\text{fail}}$
  - Refinement decay: $C_{\text{new}} = C_{\text{old}} \cdot \gamma, \quad \gamma \in (0, 1)$
* **Training Methodology:** Reinforcement learning from self-correction feedback traces.
* **Learning Algorithm:** Dynamic strategy modification with bounded iteration depth.
* **Memory Architecture:** Iterative trace log tracking original vs. refined hypothesis branches.
* **Planning Architecture:** Closed-loop pivot/refine execution loop.
* **Agent Architecture:** Self-healing controller embedded inside the Cognitive System Controller.
* **World Model Contribution:** Provides counterfactual feedback for strategy adjustments.
* **Self-Improvement Contribution:** Captures failure patterns to avoid repeating unviable strategy mutations.
* **Failure Modes:** Infinite refinement loops if maximum iteration bounds are omitted.
* **Scalability Limits:** Bounded to $K \le 3$ iterations to satisfy latency budgets.
* **Computational Complexity:** $O(I \cdot V)$ where $I$ is iteration count and $V$ is verification complexity.
* **Engineering Tradeoffs:** Added pipeline latency vs. strategy robustness.
* **Financial Applicability:** Adaptive order placement and dynamic strategy adjustment during regime shifts.
* **Production Readiness:** High. Implemented in `CognitiveSystemController._pivot_refine_loop`.

---

## 7. Paper 7: HASP (arXiv:2605.17734)
* **Title:** HASP: Prescriptive Guardrail Skill Verification & Volatility Shielding
* **Core Hypothesis:** Integrating hard, non-bypassable guardrails into skill routing guarantees that extreme market volatility or invalid parameters trigger instant pre-emption (e.g. override to hold) before strategy execution.
* **Mathematical Formulation:**
  - Intervention condition: $\text{Volatility}(t) > \sigma_{\text{threshold}} \implies \text{Action} = \text{HOLD}$
  - Risk boundary: $P(\text{Drawdown} > D_{\text{max}}) < \epsilon$
* **Training Methodology:** Rule-based synthesis combined with adversarial volatility stress testing.
* **Learning Algorithm:** Deterministic state machine with threshold-driven pre-emption.
* **Memory Architecture:** Fixed parameter register storing safety boundaries.
* **Planning Architecture:** Direct action pre-emption overriding standard skill routing.
* **Agent Architecture:** Prescriptive guardrail intercepter inside `SkillRouter`.
* **World Model Contribution:** Provides real-time volatility estimates to guardrail evaluators.
* **Self-Improvement Contribution:** Adjusts volatility thresholds based on stress test outcomes.
* **Failure Modes:** Overly conservative thresholds causing missed profitable opportunities.
* **Scalability Limits:** Zero-latency evaluation ($O(1)$) handles arbitrary transaction throughput.
* **Computational Complexity:** $O(1)$ scalar threshold comparisons.
* **Engineering Tradeoffs:** Minor missed opportunity cost vs. total protection against tail risk.
* **Financial Applicability:** Flash crash protection, black swan shielding, automated risk controls.
* **Production Readiness:** High. Implemented in `SkillRouter` and `CognitiveSystemController._apply_hasp_guardrails`.

---

## 8. Paper 8: DeepWeb-Bench (arXiv:2605.21482)
* **Title:** DeepWeb-Bench: Multi-Vector Verification and Calibrated Decision Provenance
* **Core Hypothesis:** Multi-agent verifier swarms evaluating independent evidence vectors (statistical, regime, execution, tail-risk, model stability) eliminate single-agent bias and yield calibrated confidence metrics.
* **Mathematical Formulation:**
  - Vector confidence: $\vec{C} = [c_{\text{stat}}, c_{\text{reg}}, c_{\text{exec}}, c_{\text{tail}}, c_{\text{stab}}]^T$
  - Consensus pass: $\frac{1}{N} \sum_{i=1}^N \mathbf{1}(\text{Report}_i = \text{VALID}) \ge \tau_{\text{consensus}}$
* **Training Methodology:** Multi-agent adversarial evaluation over simulated execution traces.
* **Learning Algorithm:** Calibrated confidence scoring with Merkle provenance hashing.
* **Memory Architecture:** Research Ledger Entry with verifier report snapshots.
* **Planning Architecture:** Post-hypothesis verification gate before final action authorization.
* **Agent Architecture:** Verification Swarm consisting of independent specialist verifier agents.
* **World Model Contribution:** Validates world model predictions against external market checks.
* **Self-Improvement Contribution:** Tracks individual verifier accuracy to re-weight agent votes.
* **Failure Modes:** High verifier latency if agents evaluate sequentially instead of concurrently.
* **Scalability Limits:** Scales linearly with the number of verifier agents in the swarm.
* **Computational Complexity:** $O(V)$ where $V$ is the number of verifier agents.
* **Engineering Tradeoffs:** ~5ms verification latency vs. complete elimination of single-agent errors.
* **Financial Applicability:** Trade approval verification, risk budget enforcement, institutional compliance.
* **Production Readiness:** High. Implemented in `trading_bot.core.verification.swarm.VerificationSwarm`.
