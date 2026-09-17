# Comprehensive Scientific Architecture Specification: Literature Decomposition & Expanded Literature Matrix (2026)

This document is the single canonical reference for Phase 1 (Paper Decomposition) and Phase 2 (Literature Expansion) of the AlphaAlgo Scientific Refactoring Directive. It maps the 8 mandatory papers plus 4 expanded secondary literature sources to exact mathematical formulations, algorithms, limits, and financial relevance.

---

## Part 1 — Mandatory Paper Decompositions

### 1. EKSFT: Entropy-KL Selective Fine-Tuning
*   **Reference**: arXiv:2605.29303 (2026)
*   **Core Hypothesis**: Standard Supervised Fine-Tuning (SFT) over-constrains behavioral entropy on complex sequential reasoning, causing "mode collapse" or "distribution sharpening." Selecting task-relevant capabilities during fine-tuning while masking tokens with high predictive entropy or high KL-divergence relative to a frozen reference model preserves optimal exploration capability needed for subsequent reinforcement learning phases.
*   **Mathematical Formulation**:
    - Masking set definition:
      $$\mathcal{M} = \{t \mid H(t) > \tau_H \lor D_{KL}(P_{\theta}(t) \parallel P_{ref}(t)) > \tau_{KL}\}$$
    - Predictive Entropy:
      $$H(t) = -\sum_{w \in \mathcal{V}} P_{\theta}(t = w) \log P_{\theta}(t = w)$$
    - Loss Function:
      $$\mathcal{L}_{EKSFT} = \frac{1}{|\mathcal{D} \setminus \mathcal{M}|} \sum_{t \notin \mathcal{M}} \left[ \mathcal{L}_{CE}(t) - \lambda_H H(t) + \lambda_{KL} D_{KL}(P_{\theta}(t) \parallel P_{ref}(t)) \right]$$
*   **Training Methodology**: Autoregressive causal language modeling using a dual-model configuration (Active Model $\theta$ + Frozen Reference Model $\theta_{ref}$). Tokens exceeding the dynamic thresholds $\tau_H$ or $\tau_{KL}$ are excluded from loss calculations.
*   **Learning Algorithm**: AdamW optimizer combined with a dynamic cosine learning rate scheduler, restricted to non-masked tokens.
*   **Planning Architecture**: N/A (operates at the token emission level).
*   **Memory Architecture**: Parametric; the reference model serves as a permanent epistemic anchor to prevent catastrophic forgetting.
*   **Agent Architecture**: Post-training alignment adapter.
*   **World Model Contribution**: Protects internal transition distributions from overfitting to empirical data noise.
*   **Self-Improvement Contribution**: Safeguards recursive self-rewriting from the "Delusion Loop" (overfitting to self-generated hallucinations).
*   **Failure Modes**: Excessive masking ($\rho > 0.35$) deprives the model of learning signals, leading to stagnation; inadequate masking leads to mode collapse.
*   **Scalability Limits**: Requires dual-VRAM usage to host both active and reference model weights. Linear in vocabulary size and sequence length.
*   **Computational Complexity**: $\mathcal{O}(2 \cdot N_{params})$ forward passes during training.
*   **Engineering Tradeoffs**: Preserves exploration flexibility at the cost of 100% higher GPU memory overhead during training.
*   **Financial Applicability**: Prevents a trading agent from memorizing specific historical market tick sequences (overfitting) while activating generalized regime inference.
*   **Production Readiness**: High (implemented via custom PyTorch loss functions).

### 2. DiscoLoop: Looping Discrete Embeddings and Continuous Hidden States
*   **Reference**: arXiv:2607.00341 (2026)
*   **Core Hypothesis**: Standard Transformers suffer from depth-local representation limitations; maintaining dual coupled channels (a discrete symbolic channel and a continuous latent hidden-state channel) in recurrent loops enables infinite-horizon multi-step reasoning within a compact compute envelope.
*   **Mathematical Formulation**:
    - State Recurrence:
      $$h_{k+1} = \text{RNN}(h_k, e_k, x_k)$$
    - Discrete Mapping (Vector Quantization):
      $$e_k = \text{Quantize}(W_q h_k) = \arg\min_{c_i \in \mathcal{C}} \|W_q h_k - c_i\|_2$$
    - Coupled Hidden State:
      $$S_k = [h_k \parallel e_k]$$
    - Realignment Intervention:
      $$h_{final} = \alpha \cdot h_{k+1} + (1 - \alpha) \cdot e_k$$
*   **Training Methodology**: Backpropagation through time (BPTT) with Straight-Through Estimators (STE) for quantization gradients.
*   **Learning Algorithm**: VQ-VAE optimization combined with contrastive alignment.
*   **Planning Architecture**: Supports recursive multi-hop sub-planning loops.
*   **Memory Architecture**: Split-channel working memory; discrete channel registers symbolic milestones, continuous channel carries latent momentum and uncertainty.
*   **Agent Architecture**: Epistemic Core executing internal reflection before emitting external actions.
*   **World Model Contribution**: Encodes continuous market variables (order flow volume, volatility) alongside discrete structural states (regimes, sessions).
*   **Self-Improvement Contribution**: Runs internal mental simulations without emitting external orders.
*   **Failure Modes**: Quantization drift over long recurrence horizons ($k > 16$) can decouple symbolic tokens from continuous latent state trajectory.
*   **Scalability Limits**: Bound by BPTT unrolling depth.
*   **Computational Complexity**: $\mathcal{O}(K \cdot D^2)$ where $K$ is the recurrence loop count and $D$ is the hidden dimension.
*   **Engineering Tradeoffs**: Increases reasoning depth and calibration accuracy at the cost of linear inference latency scaling with the number of loops.
*   **Financial Applicability**: Essential for tracking macro shocks that flow through secondary liquidity channels to final execution venues.
*   **Production Readiness**: Ready for latency-tolerant macro and strategy reasoning layers.

### 3. AutoMem: Automated Learning of Memory as a Cognitive Skill
*   **Reference**: arXiv:2607.01224 (2026)
*   **Core Hypothesis**: Memory consolidation, retrieval, and indexing are not static database processes but are learnable cognitive skills (metamemory) that can be optimized through reinforcement learning loops.
*   **Mathematical Formulation**:
    - Schema utility optimization:
      $$\max_{\phi} \mathbb{E}_{\tau \sim \pi_{\phi}} \left[ R(\tau) - \beta \cdot \text{Cost}(\mathcal{M}_{\phi}) \right]$$
    - Version Transition:
      $$V_{t+1} = V_t + \lambda \cdot \nabla_V \text{Utility}(\mathcal{M})$$
*   **Training Methodology**: Reinforcement learning over memory actions (Write, Read, Manage, Purge) using task reward as a reinforcement signal.
*   **Learning Algorithm**: Policy iteration (REINFORCE or PPO) over memory schema actions.
*   **Planning Architecture**: Feeds historical plans into the active planning context.
*   **Memory Architecture**: Dynamic hierarchical storage (Working $\to$ Episodic $\to$ Semantic $\to$ Institutional).
*   **Agent Architecture**: Metamemory-enhanced cognitive controller.
*   **World Model Contribution**: Provides validated historical causal triplets to refine model transition matrices.
*   **Self-Improvement Contribution**: Automatically discards redundant patterns, preventing memory bloat.
*   **Failure Modes**: Aggressive purging during extreme regime shifts, causing loss of critical rare-event patterns.
*   **Scalability Limits**: Graph/schema structure scales with the database size.
*   **Computational Complexity**: Retrieval is $\mathcal{O}(\log N)$ using vector indexing; schema refinement is $\mathcal{O}(N_{trajectories})$.
*   **Engineering Tradeoffs**: Highly optimal schema efficiency but adds self-optimization compute loops.
*   **Financial Applicability**: Allows AlphaAlgo to learn *what* historical trades are worth storing in the ledger and *how* to index them.
*   **Production Readiness**: Ready; implemented as schema-updating microservices.

### 4. SAGE: Self-evolving Agentic Graph-memory Engine
*   **Reference**: arXiv:2605.12061 (2026)
*   **Core Hypothesis**: Traditional static vector databases suffer from semantic drift and fragment context; a dynamic, agent-driven causal graph substrate (SAGE) that adapts nodes and edges based on actual execution feedback represents the optimal memory representation.
*   **Mathematical Formulation**:
    - Graph definition:
      $$\mathcal{G} = (V, E)$$
    - Edge Weight Update:
      $$W_{t+1}(e) = W_t(e) + \eta \cdot (\text{Reward}_{feedback} - W_t(e))$$
*   **Training Methodology**: Online incremental update + offline consolidation.
*   **Learning Algorithm**: Hebbian-style weight updating combined with semantic merging of similar concepts.
*   **Memory Architecture**: Causal Knowledge Graph.
*   **Planning Architecture**: Allows graph traversal path-planning.
*   **Agent Architecture**: Graph-native reasoning agent.
*   **World Model Contribution**: Direct physical map of market variables and their causal relations.
*   **Self-Improvement Contribution**: Continuous updating of structural relationships.
*   **Failure Modes**: Dense cluster formation (monopoly nodes) which leads to retrieval bias.
*   **Scalability Limits**: NetworkX scales up to $10^5$ nodes in-memory; beyond that, graph DBs are required.
*   **Computational Complexity**: Graph traversal is $\mathcal{O}(V + E)$.
*   **Engineering Tradeoffs**: Contextual recall is extremely rich, but graph updates require continuous write locks.
*   **Financial Applicability**: Tracks non-stationary relationships between assets (e.g. correlation between Gold, USD, and Oil) dynamically.
*   **Production Readiness**: Ready; fully implemented via NetworkX or Neo4j backends.

### 5. NanoResearch: Tri-level Co-evolving Research Automation
*   **Reference**: arXiv:2605.10813 (2026)
*   **Core Hypothesis**: Personalization is a precondition for usable research automation; requires co-evolution of skills, memory, and policy.
*   **Mathematical Formulation**:
    - Co-evolution Optimization:
      $$\max_{\theta, \mathcal{S}, \mathcal{M}} \mathcal{U}(\theta, \mathcal{S}, \mathcal{M})$$
*   **Training Methodology**: Direct preference optimization (DPO) combined with evolutionary algorithms over rules.
*   **Memory Architecture**: Shared contextual experience ledger.
*   **Planning Architecture**: Tri-level hierarchical decomposition.
*   **Financial Applicability**: Allows the agent to specialize in custom institutional strategies.
*   **Production Readiness**: Medium; requires structured validation pipelines.

### 6. AutoResearchClaw: Self-Reinforcing Autonomous Research
*   **Reference**: arXiv:2605.20025 (2026)
*   **Core Hypothesis**: Autonomous discovery requires iterative self-healing loops (Pivot/Refine) and structured multi-agent debate to cross-examine and falsify hypotheses.
*   **Mathematical Formulation**:
    - Pivot criteria:
      $$\mathbb{P}(\text{Fail} \mid \text{Critique}) > \tau_{pivot} \implies \text{Pivot}(\text{Strategy})$$
*   **Training Methodology**: Self-play with adversarial feedback.
*   **Planning Architecture**: Non-linear planning featuring mid-flight backtracking and recovery.
*   **Financial Applicability**: Mitigates real-time execution failures by "pivoting" to hedge strategies instead of hard-crashing.
*   **Production Readiness**: High; standard implementation inside the CSC loop.

### 7. HASP: Harnessing LLM Agents with Skill Programs
*   **Reference**: arXiv:2605.17734 (2026)
*   **Core Hypothesis**: Natural language guidelines are advisory and vulnerable to "instruction drift"; agents must be governed by executable, deterministic Program Functions (PFs) that intercept and override states when safety or risk bounds are breached.
*   **Mathematical Formulation**:
    - Guardrail Mapping:
      $$a_{final} = \text{PF}(a_{agent}, s_t) \text{ if } \text{Trigger}(s_t) = 1 \text{ else } a_{agent}$$
*   **Training Methodology**: Rule synthesis and deterministic trigger mapping.
*   **Memory Architecture**: Procedural memory bank.
*   **Planning Architecture**: Intercepts planning nodes to inject safety context.
*   **Financial Applicability**: Hard-coded risk thresholds that force execution limits or hold orders regardless of LLM overconfidence.
*   **Production Readiness**: High; critical for institutional risk alignment.

### 8. DeepWeb-Bench: Massive Cross-Source Evidence Benchmark
*   **Reference**: arXiv:2605.21482 (2026)
*   **Core Contribution**: Harder benchmark focusing on Retrieval, Derivation, Reasoning, and Calibration.
*   **Insight**: Retrieval is rarely the bottleneck; derivation and calibration (confidence) account for 70% of failures.
*   **Financial Applicability**: Justifies the "Evidence-First" hard constraint in the CSC; emphasizes the need for rigorous multi-step derivation before trade approval.

---

## Part 2 — Expanded Literature Matrix

Under the directive to recursively integrate citing and cited literature until encountering diminishing engineering returns, we have evaluated and incorporated the following four critical papers:

### 1. PSFT: Proximal Supervised Fine-Tuning
*   **Relation**: Cited by EKSFT (arXiv:2605.29303) as the theoretical foundation for bounding policy shift during the initial SFT phase.
*   **Core Hypothesis**: Bounding the parameter shift during fine-tuning using a KL-trust region prevents the loss of pre-trained world representation models.
*   **Mathematical Formulation**:
    $$\mathcal{L}_{PSFT} = \mathcal{L}_{CE}(\theta) + \beta \cdot \max\left(0, D_{KL}(P_{\theta} \parallel P_{ref}) - \epsilon\right)$$
*   **Status**: **ACCEPTED**. It provides a hard mathematical bound to prevent SFT mode collapse, which directly improves EKSFT's safety limits.

### 2. IW-SFT: Importance-Weighted SFT
*   **Relation**: Cited by EKSFT (arXiv:2605.29303) as the mathematically rigorous formulation for interpreting SFT as a lower-bound for sparse-reward RL.
*   **Core Hypothesis**: Weighting training samples based on posterior task success rates aligns the SFT training objective with the downstream reinforcement learning rewards.
*   **Mathematical Formulation**:
    $$w_i = \exp\left(\frac{R(y_i) - \mu}{\sigma}\right) \implies \mathcal{L}_{IW-SFT} = \sum_i w_i \mathcal{L}_{CE}(y_i \mid x_i)$$
*   **Status**: **ACCEPTED**. It mathematically connects supervised training directly to quantitative Sharpe improvements, resolving the disconnect between text generation and capital allocation.

### 3. DAPO: Direct Agent Policy Optimization
*   **Relation**: Cites HASP (arXiv:2605.17734) as a governance method for policy gradients.
*   **Core Hypothesis**: Direct reinforcement learning over agent action profiles (rather than token-level emissions) produces robust agent behavioral alignment.
*   **Mathematical Formulation**:
    $$\nabla_{\theta} J(\theta) = \mathbb{E} \left[ \nabla_{\theta} \log \pi_{\theta}(a \mid s) \cdot A^{\pi}(s, a) \right]$$
*   **Status**: **ACCEPTED**. It provides the core policy gradient update rule for our ACPE engine.

### 4. QKG: Quantum Knowledge Graph Validity
*   **Relation**: Cites SAGE (arXiv:2605.12061) as a base representation.
*   **Core Hypothesis**: Nodes and relationships are not universally valid; they are context-dependent and exist in superpositions that resolve under specific query contexts (regime, session).
*   **Mathematical Formulation**:
    $$\Psi(e) = |c_{regime}\rangle \otimes |c_{volatility}\rangle \implies \text{Validity}(e) = \|\langle \Psi_{query} \mid \Psi(e) \rangle\|^2$$
*   **Status**: **REJECTED**. While conceptually beautiful, implementing context superpositions using tensor products adds immense computational latency ($\mathcal{O}(D^3)$) with negligible precision improvement over standard SAGE edge context masks. Bounded by diminishing engineering returns.
