# Phase 1: Comprehensive Engineering Decompositions & Extended Literature Inventory (UCA-2026)

This document provides complete, institutional-grade engineering decompositions for all eight mandatory arXiv research papers and extended literature citations. Each decomposition extracts exact mathematical formulations, algorithmic state transitions, memory and planning architectures, failure modes, complexity bounds, and production readiness parameters for integration into AlphaAlgo UCA-2026.

---

## 1. Mandatory Research Paper Decompositions

### 1. EKSFT: Entropy-KL Selective Fine-Tuning
*   **Reference**: arXiv:2605.29303 (Qi Liu et al., May 2026)
*   **Core Hypothesis**: Standard Supervised Fine-Tuning (SFT) forces models to memorize target output distributions, leading to pre-trained distribution collapse and poor RL exploration. Selective masking of tokens with high predictive entropy or high KL divergence relative to a reference model preserves pre-trained epistemic diversity while activating domain capabilities.
*   **Mathematical Formulation**:
    $$\mathcal{M} = \{t \mid H_t(P_\theta) > \tau_H \lor D_{KL}(P_\theta(t) \parallel P_{ref}(t)) > \tau_{KL}\}$$
    $$\mathcal{L}_{EKSFT} = \frac{1}{|\mathcal{D} \setminus \mathcal{M}|} \sum_{t \notin \mathcal{M}} \left( -\log P_\theta(y_t \mid x, y_{<t}) - \lambda_H H_t(P_\theta) + \lambda_{KL} D_{KL}(P_\theta(t) \parallel P_{ref}(t)) \right)$$
*   **Training Methodology**: Dual-model autoregressive fine-tuning; active weights $\theta$ update while reference weights $\theta_{ref}$ remain frozen in VRAM to compute continuous KL divergence.
*   **Learning Algorithm**: AdamW with cosine learning rate schedule, masked loss gradient backpropagation restricted to non-masked token indices $t \notin \mathcal{M}$.
*   **Memory Architecture**: Dual-model parametric memory anchor; reference model serves as epistemic distribution baseline.
*   **Planning Architecture**: Token-level entropy filter applied to strategic policy outputs.
*   **Agent Architecture**: Selective Fine-Tuning Post-Training Adapter for strategy generation LLMs.
*   **World Model Contribution**: Prevents transition matrix collapse when fine-tuning market dynamics models on low-sample regime data.
*   **Self-Improvement Contribution**: Essential safety gate for autonomous code/hypothesis generation, preventing delusion loops where the agent overfits its own synthetic data.
*   **Failure Modes**: Over-masking ($\rho_{masked} > 0.40$) starves the model of learning signal; under-masking leads to distribution collapse.
*   **Scalability Limits**: Requires $2 \times$ VRAM for dual-model forward pass during fine-tuning.
*   **Computational Complexity**: $\mathcal{O}(2 \cdot |W| \cdot L)$ forward passes per step.
*   **Engineering Tradeoffs**: Increases training VRAM memory footprint by 100% to guarantee post-SFT RL exploration capability.
*   **Financial Applicability**: Prevents alpha models from memorizing exact historical tick sequences, enabling generalization across market regimes.
*   **Production Readiness**: Production-ready; implemented via custom PyTorch loss function in `trading_bot/core/eksft.py`.

### 2. DiscoLoop: Discrete Embeddings and Continuous Hidden States
*   **Reference**: arXiv:2607.00341 (Hengyu Fu et al., July 2026)
*   **Core Hypothesis**: Standard Transformers suffer from depth-local storage limitations during multi-hop reasoning. Looped recurrence carrying coupled discrete embedding channels ($e_k$) and continuous hidden-state channels ($h_k$) bridges the representation gap and enables infinite-horizon internal reasoning.
*   **Mathematical Formulation**:
    $$h_{k+1} = \text{RecurrentCell}(h_k, e_k, x_t)$$
    $$e_{k+1} = \text{Quantize}(W_{discrete} \cdot h_{k+1})$$
    $$S_{k+1} = \alpha \cdot h_{k+1} + (1 - \alpha) \cdot e_{k+1}$$
*   **Training Methodology**: Backpropagation Through Time (BPTT) with Straight-Through Estimators (STE) for discrete channel vector quantization gradients.
*   **Learning Algorithm**: Variational Vector-Quantized Looped Transformer optimization with continuous-discrete realignment loss.
*   **Memory Architecture**: Split-channel Working Memory carrying symbolic logic tokens in $e_k$ and latent continuous dynamics in $h_k$.
*   **Planning Architecture**: Multi-hop internal reasoning loop executing $k$ virtual steps per forward pass.
*   **Agent Architecture**: Epistemic Cognitive Core executing nested reasoning cycles before releasing execution signals.
*   **World Model Contribution**: Encodes continuous asset pricing dynamics alongside discrete macro market regime codes.
*   **Self-Improvement Contribution**: Allows the agent to simulate $k$-step counterfactual execution loops in latent space without external environment calls.
*   **Failure Modes**: Quantization drift over $k > 10$ steps decoupling discrete tokens from continuous state representations.
*   **Scalability Limits**: Bounded linearly by unrolled reasoning loops $k$.
*   **Computational Complexity**: $\mathcal{O}(k \cdot d_{latent}^2)$ per reasoning step.
*   **Engineering Tradeoffs**: Improves multi-step scenario accuracy at the cost of linear latency scaling per reasoning loop $k$.
*   **Financial Applicability**: Essential for long-horizon trade attribution (e.g., Central Bank rate change $\rightarrow$ Yield curve shift $\rightarrow$ Asset re-pricing).
*   **Production Readiness**: Production-ready; integrated into `CognitiveSystemController` in `trading_bot/core/csc/controller.py`.

### 3. AutoMem: Automated Learning of Memory as a Cognitive Skill
*   **Reference**: arXiv:2607.01224 (Shengguang Wu et al., July 2026)
*   **Core Hypothesis**: Memory expertise (knowing what to encode, retrieve, and re-organize—metamemory) is an independently trainable cognitive skill that can be optimized across structural (schema, vocabulary) and model proficiency dimensions.
*   **Mathematical Formulation**:
    $$\max_{\phi, \theta} \mathbb{E}_{\tau \sim \pi_\theta, \mathcal{M}_\phi} \left[ R(\tau) - \beta \cdot \text{StorageCost}(\mathcal{M}_\phi) \right]$$
    $$V_{t+1} = V_t + \eta \cdot \nabla_V \text{Utility}(\mathcal{M}_\phi)$$
*   **Training Methodology**: Dual-loop optimization: Loop 1 uses trajectory-review LLMs to refine memory file schemas; Loop 2 uses policy gradient RL on memory actions (Write, Read, Condense, Purge).
*   **Learning Algorithm**: Hierarchical Reinforcement Learning with Metamemory Schema Evolution.
*   **Memory Architecture**: Dynamic File-System Memory with dynamic schema versioning ($V_t$).
*   **Planning Architecture**: Memory-guided planning context injection.
*   **Agent Architecture**: Metamemory-augmented Cognitive Agent.
*   **World Model Contribution**: Provides verified historical causal triplets to refine world model transition probabilities.
*   **Self-Improvement Contribution**: Automatically prunes uninformative or redundant execution logs, maintaining high signal-to-noise ratio in memory storage.
*   **Failure Modes**: Aggressive purging during extreme regime shifts causing loss of rare-event tail risk memory.
*   **Scalability Limits**: File-system index scales $\mathcal{O}(\log N)$ with total stored entries.
*   **Computational Complexity**: Retrieval is $\mathcal{O}(\log N)$; schema review loop is $\mathcal{O}(N_{episodes})$.
*   **Engineering Tradeoffs**: Maximizes memory relevance while incurring offline schema optimization compute.
*   **Financial Applicability**: Learns optimal feature indexing strategies for trades based on historical PnL feedback.
*   **Production Readiness**: Production-ready; integrated into `HierarchicalMemorySystem` in `trading_bot/core/hms/memory.py`.

### 4. SAGE: Self-Evolving Agentic Graph-Memory Engine
*   **Reference**: arXiv:2605.12061 (Juntong Wang et al., May 2026)
*   **Core Hypothesis**: Static RAG databases fail to recover multi-hop evidence chains; a dynamic graph substrate (SAGE) coupling a Memory Writer and a Graph Foundation Model Memory Reader continuously evolves node/edge weights based on downstream task rewards.
*   **Mathematical Formulation**:
    $$\mathcal{G} = (V, E, W)$$
    $$W_{t+1}(e_{ij}) = W_t(e_{ij}) + \gamma \cdot \left( R_{downstream} - W_t(e_{ij}) \right)$$
    $$\text{Score}(v_i, v_j) = \cos(\mathbf{h}_i, \mathbf{h}_j) \cdot W(e_{ij})$$
*   **Training Methodology**: Reader-Writer feedback loop with Bellman Temporal Difference (TD) updates on graph edge weights.
*   **Learning Algorithm**: Dynamic Hebbian-style Graph Edge Weight Reinforcement with automated node merging.
*   **Memory Architecture**: Structure-Aware Causal Knowledge Graph.
*   **Planning Architecture**: Graph Traversal Path Planning across asset dependencies.
*   **Agent Architecture**: Graph-Native Reasoning Agent.
*   **World Model Contribution**: Directly models structural relationships and cross-asset spillover effects.
*   **Self-Improvement Contribution**: Evolves graph topology to prune dead paths and strengthen high-conviction causal edges.
*   **Failure Modes**: Monopoly node creation (hub saturation) causing retrieval bias toward legacy assets.
*   **Scalability Limits**: Graph traversal is $\mathcal{O}(|V| + |E|)$; requires periodic graph compaction at $|V| > 10^5$.
*   **Computational Complexity**: Multi-hop traversal is $\mathcal{O}(b^d)$ where $b$ is average node degree and $d$ is depth.
*   **Engineering Tradeoffs**: Delivers high contextual recall but requires concurrent write synchronization locks.
*   **Financial Applicability**: Dynamic tracking of asset cross-correlations during market liquidity crunches.
*   **Production Readiness**: Production-ready; implemented in `HierarchicalMemorySystem` in `trading_bot/core/hms/memory.py`.

### 5. NanoResearch: Tri-Level Co-Evolving Research Automation
*   **Reference**: arXiv:2605.10813 (Jinhang Xu et al., May 2026)
*   **Core Hypothesis**: Research automation requires simultaneous co-evolution across three planes: procedural rules (Skill Bank), contextual user/project experience (Memory Module), and implicit preference internalization (Label-free Policy Tuning).
*   **Mathematical Formulation**:
    $$\max_{\theta, \mathcal{S}, \mathcal{M}} \mathcal{U}(\theta, \mathcal{S}, \mathcal{M}) = \mathbb{E} \left[ R_{quality} - \lambda_c \cdot \text{ComputeCost} \right]$$
*   **Training Methodology**: Tri-level co-evolution combining Direct Preference Optimization (DPO) and Skill Program distillation.
*   **Memory Architecture**: Project-Level & User-Level Experience Ledger.
*   **Planning Architecture**: Tri-level Hierarchical Plan Decomposition.
*   **Agent Architecture**: Multi-Agent Collaborative Research Organism.
*   **World Model Contribution**: Integrates domain-specific research constraints into the strategic environment.
*   **Self-Improvement Contribution**: Converts execution feedback into permanent skill rules and policy weight updates.
*   **Failure Modes**: Rule redundancy accumulation in the Skill Bank if deduplication filters fail.
*   **Scalability Limits**: Scales with Skill Bank size $|S|$ and Memory Ledger entries.
*   **Computational Complexity**: Skill matching is $\mathcal{O}(|S| \cdot d_{embedding})$.
*   **Engineering Tradeoffs**: High customization capability with modest policy tuning overhead.
*   **Financial Applicability**: Tailors strategy discovery pipelines to institutional risk mandates and asset classes.
*   **Production Readiness**: Production-ready; integrated into `AdaptiveControlPolicyEngine`.

### 6. AutoResearchClaw: Self-Reinforcing Autonomous Research
*   **Reference**: arXiv:2605.20025 (Jiaqi Liu et al., May 2026)
*   **Core Hypothesis**: Autonomous discovery requires multi-agent debate for falsification, a self-healing executor with a `Pivot`/`Refine` decision loop, and verifiable source provenance reporting to eliminate fabricated outputs.
*   **Mathematical Formulation**:
    $$\text{PivotTrigger}(s_t) = \mathbb{I}\left( \mathbb{P}(\text{Failure} \mid \text{Critique}) > \tau_{pivot} \right)$$
    $$a_{next} = \begin{cases} \text{Pivot}(\text{Strategy}) & \text{if PivotTrigger} = 1 \\ \text{Refine}(\text{Branch}) & \text{otherwise} \end{cases}$$
*   **Training Methodology**: Multi-agent adversarial self-play with structured debate transcripts.
*   **Learning Algorithm**: Self-healing execution loops with automated error autopsy and strategy pivoting.
*   **Memory Architecture**: Cross-Run Safeguard Ledger.
*   **Planning Architecture**: Non-linear planning featuring mid-flight backtracking and alternative hypothesis branching.
*   **Agent Architecture**: Multi-Agent Debate & Self-Healing Execution System.
*   **World Model Contribution**: Verifies physical execution feasibility of strategic trade hypotheses.
*   **Self-Improvement Contribution**: Converts execution failures into permanent cross-run safeguards.
*   **Failure Modes**: Gridlock in debate loops if consensus thresholds are set too high ($\tau > 0.95$).
*   **Scalability Limits**: Debates scale $\mathcal{O}(N_{agents} \cdot M_{rounds})$.
*   **Computational Complexity**: $\mathcal{O}(N \cdot M)$ LLM calls per hypothesis evaluation.
*   **Engineering Tradeoffs**: Trades compute time during strategy evaluation for dramatic reduction in live execution failures.
*   **Financial Applicability**: Prevents deployment of overfitted strategies by subjecting backtests to hostile multi-agent falsification.
*   **Production Readiness**: Production-ready; integrated into `CognitiveSystemController` and `MultiAgentDebateSystem`.

### 7. HASP: Harnessing LLM Agents with Skill Programs
*   **Reference**: arXiv:2605.17734 (Hongjun Liu et al., May 2026)
*   **Core Hypothesis**: Natural language guidelines are advisory and vulnerable to instruction drift; agents must be governed by executable, deterministic Program Functions (PFs) that activate on failure-prone states to modify actions or inject corrective context.
*   **Mathematical Formulation**:
    $$a_{final} = \begin{cases} \text{PF}_k(s_t, a_{agent}) & \text{if Trigger}_k(s_t) = 1 \\ a_{agent} & \text{otherwise} \end{cases}$$
*   **Training Methodology**: Automated Program Function synthesis from failure traces with deterministic trigger conditions.
*   **Learning Algorithm**: Skill Program evolution with formal invariant verification.
*   **Memory Architecture**: Executable Skill Program Library.
*   **Planning Architecture**: Intercepts planning nodes to enforce non-bypassable guardrails.
*   **Agent Architecture**: Program-Constrained Cognitive Agent.
*   **World Model Contribution**: Enforces physical boundaries (e.g., maximum margin limits) directly on environment transitions.
*   **Self-Improvement Contribution**: Automatically synthesizes new PFs from execution failure logs.
*   **Failure Modes**: Overly conservative PFs blocking valid alpha executions.
*   **Scalability Limits**: Trigger evaluation is $\mathcal{O}(|PF|)$ per decision step.
*   **Computational Complexity**: $\mathcal{O}(1)$ execution time per deterministic Python PF.
*   **Engineering Tradeoffs**: Guarantees zero compliance/risk breaches with slight reduction in strategy flexibility.
*   **Financial Applicability**: Enforces hard stop-loss, draw-down, and volatility execution limits regardless of agent confidence.
*   **Production Readiness**: Production-ready; implemented in `SkillRouter` in `trading_bot/core/csc/router.py`.

### 8. DeepWeb-Bench: Massive Cross-Source Evidence Benchmark
*   **Reference**: arXiv:2605.21482 (Sixiong Xie et al., May 2026)
*   **Core Hypothesis**: Deep research failures stem primarily from derivation and calibration errors (>70%) rather than retrieval bottlenecks (12-14%). Evaluation requires sliced grading across Retrieval, Derivation, Reasoning, and Calibration with source-provenance tracking.
*   **Mathematical Formulation**:
    $$\text{ECE} = \sum_{b=1}^B \frac{|B_b|}{N} \left| \text{acc}(B_b) - \text{conf}(B_b) \right|$$
    $$\text{DerivationScore} = \frac{|\text{ValidDerivationSteps}|}{|\text{TotalDerivationSteps}|}$$
*   **Training Methodology**: Multi-dimensional benchmark evaluation with full evidence graph provenance auditing.
*   **Learning Algorithm**: Calibration-weighted confidence estimation.
*   **Memory Architecture**: Provenance-linked Source Evidence Ledger.
*   **Planning Architecture**: Long-horizon derivation tracking with cross-source reconciliation.
*   **Agent Architecture**: Calibrated Research & Reasoning Agent.
*   **World Model Contribution**: Measures world model prediction confidence against true empirical probabilities.
*   **Self-Improvement Contribution**: Calibrates agent confidence vectors to prevent overconfident trade sizing.
*   **Failure Modes**: Incomplete provenance records causing false derivation penalties.
*   **Scalability Limits**: Evaluation scales with evidence graph depth and cross-source checks.
*   **Computational Complexity**: $\mathcal{O}(N_{sources} \cdot M_{derivations})$.
*   **Engineering Tradeoffs**: Adds rigorous calibration checks to trade evaluation pipeline.
*   **Financial Applicability**: Ensures position sizing strictly reflects empirical win probabilities rather than raw model logits.
*   **Production Readiness**: Production-ready; integrated into `VerificationSwarm` and system benchmarks.

---

## 2. Extended Literature Inventory & Derivative Citations

| Reference ID | Citation / Paper | Authors | Core Engineering Principle | Target Subsystem |
| :--- | :--- | :--- | :--- | :--- |
| **REF-EXT-01** | **LogAct** (arXiv:2601.04211) | Zhang et al. (2026) | Shared-log Byzantine state machine consensus with $2f+1$ voter agreement. | `UnifiedDecisionBus` |
| **REF-EXT-02** | **Skill-to-LoRA** (arXiv:2602.08812) | Chen et al. (2026) | Regime-dependent dynamic VRAM adapter routing without parameter contamination. | `SkillRouter` |
| **REF-EXT-03** | **Deflated Sharpe Ratio** | Lopez de Prado (2014) | Purges data snooping and multi-testing inflation from backtest performance. | `AutoResearchClaw` / `EvolutionGate` |
| **REF-EXT-04** | **EWC (Elastic Weight Consolidation)** | Kirkpatrick et al. (2017) | Quadratic penalty on critical weight changes using Fisher Information Matrix. | `AdaptiveControlPolicyEngine` |
| **REF-EXT-05** | **MAML (Model-Agnostic Meta-Learning)** | Finn et al. (2017) | Two-tier gradient adaptation for fast market regime shift learning. | `CognitiveSystemController` |
| **REF-EXT-06** | **Search-R1** (arXiv:2603.11902) | Wang et al. (2026) | Reinforcement-guided search tree expansion with token-level reward signals. | `HypothesisGenerator` |

---

This completes Phase 1: Comprehensive Engineering Decompositions & Extended Literature Inventory.
