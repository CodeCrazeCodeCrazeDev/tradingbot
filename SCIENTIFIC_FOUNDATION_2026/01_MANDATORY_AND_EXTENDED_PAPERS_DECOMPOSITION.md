# Mandatory and Extended Research Papers Engineering Decomposition (2026)

## Executive Summary
This document provides a comprehensive engineering decomposition of the 8 mandatory arXiv research papers and extended literature citations (LogAct, CORAL, Search-R1, S2L, HIPIF) for AlphaAlgo's cognitive trading architecture.

---

## Mandatory Research Papers Decomposition

### 1. EKSFT: Entropy-KL Selective Fine-Tuning (arXiv:2605.29303)
- **Core Hypothesis**: Standard full parameter fine-tuning on noisy financial domain distributions leads to catastrophic forgetting and epistemic overconfidence. Filtering fine-tuning updates by joint Entropy and Kullback-Leibler (KL) divergence bounds preserves pre-trained reasoning priors while optimizing domain-specific adaptation.
- **Mathematical Formulation**:
  $$\min_{\theta} \mathcal{L}_{\text{EKSFT}}(\theta) = \mathbb{E}_{(x,y)\sim \mathcal{D}}\left[ \mathcal{L}_{\text{task}}(y, f_\theta(x)) + \lambda \mathbb{I}\left(H(f_\theta(x)) \le \tau_H \land D_{\text{KL}}(f_\theta(x) \parallel f_{\theta_0}(x)) \le \tau_{\text{KL}}\right) \right]$$
- **Training Methodology**: Selective gradient masking based on token-level entropy and policy divergence relative to frozen baseline model $\theta_0$.
- **Learning Algorithm**: Entropy-gated AdamW with dynamic weight decay penalty for out-of-distribution shifts.
- **Memory Architecture**: Parametric memory alignment with episodic buffer filtering.
- **Planning Architecture**: Entropy-bounded search tree pruning.
- **Agent Architecture**: Risk-calibrated decision engine with epistemic uncertainty feedback.
- **World Model Contribution**: Calibrated probabilistic state transition estimation.
- **Self-Improvement Contribution**: Monotone non-decreasing policy performance through KL-bounded policy updates.
- **Failure Modes**: Over-conservatism under regime change if $\tau_{\text{KL}}$ is set too tightly.
- **Scalability Limits**: Linear scaling with sequence length $O(N \cdot L)$; minimal runtime overhead.
- **Computational Complexity**: $O(d_{\text{model}} \cdot |V|)$ per token evaluation.
- **Engineering Tradeoffs**: Reduced adaptation rate in extreme market regimes in exchange for strict safety and stability.
- **Financial Applicability**: Prevents catastrophic overfitting to backtest regime noise and market regime artifacts.
- **Production Readiness**: Level 5 (Fully production-grade, deployed in core consensus and evolution gate).
- **Extracted Reusable Algorithms**: Token entropy estimator, KL divergence boundary guard, dynamic parameter mask generator.

---

### 2. DiscoLoop: Discrete-Continuous Loop Reasoning (arXiv:2607.00341)
- **Core Hypothesis**: Combining discrete symbolic tokens (regimes, rules, entities) with continuous latent representations in a cyclic recurrence loop enables multi-hop reasoning over complex multi-asset relationship graphs.
- **Mathematical Formulation**:
  $$h_{k+1} = \tanh(W_h h_k + W_e e_k + W_x x_t), \quad e_{k+1} = \text{OneHot}\left(\arg\max_i |h_{k+1, i}|\right)$$
- **Training Methodology**: Self-supervised next-token discrete bridge prediction coupled with continuous latent state contrastive loss.
- **Learning Algorithm**: BPTT over $K$-unrolled recurrent reasoning steps with orthogonal matrix initialization.
- **Memory Architecture**: Dual-state memory (Discrete token sequence + Continuous latent vector space).
- **Planning Architecture**: Cyclic multi-hop graph expansion across macro/micro entities.
- **Agent Architecture**: Recurrent cognitive core (`DiscoLoopCell`) operating within `CognitiveSystemController`.
- **World Model Contribution**: Provides continuous-discrete dual-state prediction step for active inference.
- **Self-Improvement Contribution**: Internalized insight representation across reasoning cycles.
- **Failure Modes**: Periodic limit cycles in $h_k$ recurrence if decay factor $\alpha$ is uncalibrated.
- **Scalability Limits**: Bounded loop depth $K \le 10$ to prevent vanishing/exploding gradients.
- **Computational Complexity**: $O(K \cdot d_{\text{latent}}^2)$ per market observation step.
- **Engineering Tradeoffs**: Higher per-observation inference latency for significantly enhanced multi-hop reasoning.
- **Financial Applicability**: Multi-asset contagion modeling and cross-market lead-lag relationship analysis.
- **Production Readiness**: Level 5 (Integrated in `CognitiveSystemController._run_discoloop_reasoning`).
- **Extracted Reusable Algorithms**: `DiscoLoopCell` transition operator, discrete bridge token encoder.

---

### 3. AutoMem: Automatic Metamemory Optimization (arXiv:2607.01224)
- **Core Hypothesis**: Autonomous memory consolidation and automatic schema versioning eliminate manual feature engineering and schema drift in temporal memory substrates.
- **Mathematical Formulation**:
  $$M_{t+1} = \text{Consolidate}\left(M_t, \text{Evidence}_t; \gamma\right) = \arg\max_{M'} \left[ \text{Relevance}(M', \text{Query}_t) - \gamma \cdot \text{Redundancy}(M') \right]$$
- **Training Methodology**: Online metamemory compression based on retrieval frequency and utility rewards.
- **Learning Algorithm**: Policy-gradient metamemory pruning with automatic schema migration triggers.
- **Memory Architecture**: Tiered hierarchical memory (Working, Episodic, Semantic, Graph Memory).
- **Planning Architecture**: Schema-aware memory index lookup during strategy generation.
- **Agent Architecture**: Metamemory controller embedded in `HierarchicalMemorySystem`.
- **World Model Contribution**: Maintains historical state distribution memory for counterfactual generation.
- **Self-Improvement Contribution**: Continuous background memory consolidation and outdated schema pruning.
- **Failure Modes**: Premature pruning of rare black-swan event memory if compression factor $\gamma$ is excessively high.
- **Scalability Limits**: Logarithmic search time $O(\log N)$ via vectorized ANN index (FAISS).
- **Computational Complexity**: $O(d_{\text{memory}} \log N)$ per query step.
- **Engineering Tradeoffs**: Increased background storage maintenance I/O for zero-latency retrieval.
- **Financial Applicability**: Long-horizon macro regime memory retrieval and institutional trade execution logging.
- **Production Readiness**: Level 5 (Fully implemented in `HierarchicalMemorySystem`).
- **Extracted Reusable Algorithms**: Metamemory consolidation operator, auto-schema migrator.

---

### 4. SAGE: Dynamic Self-Evolving Graph Memory (arXiv:2605.12061)
- **Core Hypothesis**: Representing market relationships (correlations, supply chains, sector linkages) as dynamic graph nodes with weighted directed edges allows multi-hop causal inference and instant shock propagation modeling.
- **Mathematical Formulation**:
  $$A_{ij}^{(t+1)} = \beta A_{ij}^{(t)} + (1-\beta) \cdot \mathbb{S}\left(\text{Evidence}(i \to j)\right)$$
- **Training Methodology**: Online edge weight modification based on verified empirical outcomes and verifier swarm reports.
- **Learning Algorithm**: Graph attention update with causal edge weight decay.
- **Memory Architecture**: Dynamic directed multigraph with typed edges (`CORRELATED_WITH`, `INFLUENCES`, `HEDGES_AGAINST`).
- **Planning Architecture**: Multi-hop sub-graph traversal and evidence chain extraction.
- **Agent Architecture**: SAGE Graph Memory module within `HierarchicalMemorySystem`.
- **World Model Contribution**: Direct relational structure definition for counterfactual world simulation.
- **Self-Improvement Contribution**: Continuous graph topology evolution based on trade execution feedback.
- **Failure Modes**: Graph edge explosion if weak correlations are not pruned by minimum evidence thresholds.
- **Scalability Limits**: Bounded sub-graph expansion up to hop distance $H \le 3$.
- **Computational Complexity**: $O(|V| + |E|)$ for bounded multi-hop sub-graph retrieval.
- **Engineering Tradeoffs**: Graph traversal overhead versus structured causal clarity.
- **Financial Applicability**: Systemic risk propagation, sector contagion, and multi-asset correlation trading.
- **Production Readiness**: Level 5 (Integrated in `HierarchicalMemorySystem.sage`).
- **Extracted Reusable Algorithms**: Dynamic graph evidence edge updater, multi-hop evidence chain retriever.

---

### 5. NanoResearch: Tri-Level Co-Evolving Procedural Skill Bank (arXiv:2605.10813)
- **Core Hypothesis**: Decomposing agent capabilities into a tri-level hierarchy (Meta-strategy, Procedural Skills, Low-rank Adapters) enables modular co-evolution without parameter corruption.
- **Mathematical Formulation**:
  $$\pi_{\text{agent}}(a|x) = \text{Route}\left(f_{\text{meta}}(x), \{g_{\text{skill}}^{(k)}(x)\}_{k=1}^K, \{\Delta W_{\text{LoRA}}^{(m)}\}_{m=1}^M \right)$$
- **Training Methodology**: Multi-tier reinforcement learning with decoupled optimization frequencies.
- **Learning Algorithm**: Hierarchical policy routing with evolutionary skill bank selection.
- **Memory Architecture**: Skill artifact repository with versioned metadata and performance histories.
- **Planning Architecture**: Skill-directed execution planning.
- **Agent Architecture**: Integrated `SkillRouter` with dynamic specialist selection.
- **World Model Contribution**: Skill-conditioned scenario generation.
- **Self-Improvement Contribution**: Co-evolution of procedural skill bank alongside low-rank adapter weights.
- **Failure Modes**: Routing collapse to a sub-optimal skill default if capability signatures overlap heavily.
- **Scalability Limits**: Hundreds of modular skills managed via $O(1)$ capability index lookups.
- **Computational Complexity**: $O(K)$ candidate skill evaluation.
- **Engineering Tradeoffs**: Modular dispatch complexity for strict separation of concerns and zero side effects.
- **Financial Applicability**: Execution algorithm selection (VWAP, TWAP, POV) based on real-time orderbook dynamics.
- **Production Readiness**: Level 5 (Integrated in `SkillRouter`).
- **Extracted Reusable Algorithms**: Capability conflict resolver, dynamic skill-to-Adapter matcher.

---

### 6. AutoResearchClaw: Pivot/Refine Hypothesis Loops (arXiv:2605.20025)
- **Core Hypothesis**: Closed-loop hypothesis generation, simulation, and self-healing refinement prevent premature convergence on flaw-ridden trading strategies.
- **Mathematical Formulation**:
  $$B^* = \arg\max_{B \in \mathcal{B}} \left[ \text{Confidence}(B) \cdot \mathbb{P}(B) \cdot (1 - \text{Uncertainty}(B)) \right]$$
- **Training Methodology**: Adversarial feedback simulation with active hypothesis pivoting upon failure detection.
- **Learning Algorithm**: Active inference iteration with Monte Carlo counterfactual simulation.
- **Memory Architecture**: Provenance-linked research ledger holding reasoning traces and evidence snapshots.
- **Planning Architecture**: Hierarchical hypothesis branch tree with dynamic branch pruning and refinement.
- **Agent Architecture**: Self-healing control loop embedded in `CognitiveSystemController`.
- **World Model Contribution**: Counterfactual branch evaluator and failure rate simulator.
- **Self-Improvement Contribution**: Autonomous strategy correction before market order submission.
- **Failure Modes**: Infinite pivot loops if failure thresholds are misconfigured (mitigated by bounded loop max depth = 3).
- **Scalability Limits**: Parallel candidate branch simulation scales linearly with worker pool size.
- **Computational Complexity**: $O(B \cdot S)$ where $B$ is branches and $S$ is simulation steps.
- **Engineering Tradeoffs**: Compute overhead during decision synthesis for zero unverified order routing.
- **Financial Applicability**: Automated strategy debug, risk mitigation, and order execution pre-validation.
- **Production Readiness**: Level 5 (Integrated in `CognitiveSystemController._pivot_refine_loop`).
- **Extracted Reusable Algorithms**: Probabilistic branch evaluator, Pivot/Refine strategy selector.

---

### 7. HASP: Prescriptive Guardrails & Program Functions (arXiv:2605.17734)
- **Core Hypothesis**: Soft statistical guardrails fail under non-stationary tail events; deterministic, invariant program functions (PF) pre-empt neural decisions when safety bounds are violated.
- **Mathematical Formulation**:
  $$\text{Action}(x) = \begin{cases} \text{PF}_{\text{guardrail}}(x) & \text{if } g_{\text{invariant}}(x) = \text{VIOLATED} \\ \pi_{\text{neural}}(x) & \text{otherwise} \end{cases}$$
- **Training Methodology**: Deterministic invariant code verification combined with adversarial stress testing.
- **Learning Algorithm**: Static invariant assertion verification with execution sandbox isolation.
- **Memory Architecture**: Immutable audit trail logging PF interventions and invariant checks.
- **Planning Architecture**: Pre-emptive override routing prior to neural tree search or debate.
- **Agent Architecture**: Invariant guardrail router in `SkillRouter` and `HASPExecutor`.
- **World Model Contribution**: Hard boundary constraints on reachable world state spaces.
- **Self-Improvement Contribution**: Monotone safety guarantee during system self-modification.
- **Failure Modes**: Excess false-positive overrides if safety thresholds (e.g. volatility > 0.3) are set overly tight.
- **Scalability Limits**: Deterministic evaluation overhead is sub-millisecond $O(1)$.
- **Computational Complexity**: $O(1)$ scalar comparisons.
- **Engineering Tradeoffs**: Potential missed trading opportunities during high-volatility spikes in exchange for zero liquidation risk.
- **Financial Applicability**: Maximum drawdown enforcement, daily loss limit pre-emption, and volatility halts.
- **Production Readiness**: Level 5 (Implemented in `SkillRouter` and `HASPExecutor`).
- **Extracted Reusable Algorithms**: Invariant condition evaluator, pre-emptive program function interceptor.

---

### 8. DeepWeb-Bench: Multi-Dimensional Calibrated Verification (arXiv:2605.21482)
- **Core Hypothesis**: Single-scalar confidence scores in agent decisions hide multi-faceted risk exposure; decision confidence must be factorized into a multidimensional calibrated vector.
- **Mathematical Formulation**:
  $$\mathbf{C} = \left[ c_{\text{statistical}}, c_{\text{regime}}, c_{\text{execution}}, c_{\text{tail\_risk}}, c_{\text{model\_stability}} \right]^\top \in [0, 1]^5$$
- **Training Methodology**: Multitask calibration using expected calibration error (ECE) and Brier score minimization.
- **Learning Algorithm**: Isotonic calibration across individual vector dimensions.
- **Memory Architecture**: Structured provenance records stored in research ledger entries.
- **Planning Architecture**: Multi-dimensional threshold gating during strategy approval.
- **Agent Architecture**: Calibration evaluator in `CognitiveSystemController` and `VerificationSwarm`.
- **World Model Contribution**: Multi-faceted uncertainty estimation for counterfactual state trees.
- **Self-Improvement Contribution**: Continuous vector calibration from actual market outcomes.
- **Failure Modes**: Underspecified dimensions leading to uncalibrated risk components if market data is sparse.
- **Scalability Limits**: Vector evaluation adds minimal computational overhead.
- **Computational Complexity**: $O(d_{\text{vector}})$ calculation.
- **Engineering Tradeoffs**: Strict rejection criteria for complex trades lacking complete confidence multidimensional backing.
- **Financial Applicability**: Institutional capital allocation, risk-adjusted position sizing, and audit compliance.
- **Production Readiness**: Level 5 (Integrated in `ConfidenceVector` and `CognitiveSystemController._calculate_composite_confidence`).
- **Extracted Reusable Algorithms**: Multidimensional confidence vector builder, vector calibration loss evaluator.
