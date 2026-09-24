# Phase 1: Research Selection, Decomposition & Quality Methodology (2026)

This document details the selection process, quality filtering, engineering decompositions, and multi-attribute research inventory for the SOTA research papers underpinning the AlphaAlgo Unified Scientific Architecture (UCA-2026).

---

## 1. Selection Criteria & Methodology

We filtered paper candidates using a formal multi-attribute evaluation process across:
*   **Scientific Merit**: Status of venue/peer-review, or status of leading research labs (DeepMind, OpenAI, Anthropic, Shanghai AI Lab).
*   **Mathematical Rigor**: Formal definition of state transitions, losses, metrics, or bounds.
*   **Engineering Maturity**: Practicality of implementation, presence of verifiable open-source baselines, and production applicability.
*   **Financial Transferability**: Robustness to non-stationary distributions, temporal leakage, look-ahead bias, and high-noise regimes.

---

## 2. Comprehensive Mandatory Research Inventory

| Research ID | Paper / Title | Authors / Source | Year | Primary Focus | Math Rigor | Engineering Maturity | Production Relevance | Financial Transferability | Selection Decision |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **arXiv:2605.29303** | EKSFT: Entropy-KL Selective Fine-Tuning | DeepMind / arXiv | 2026 | Selective Token Masking | Very High | High | High | High | **MANDATORY CORE** |
| **arXiv:2607.00341** | DiscoLoop: Discrete & Continuous Reasoning | Shanghai AI Lab / arXiv | 2026 | Recurrent Dual-Channel Reasoning | High | High | High | Very High | **MANDATORY CORE** |
| **arXiv:2607.01224** | AutoMem: Automated Meta-Memory Optimization | Tsinghua / arXiv | 2026 | Metamemory Schema Migration | High | High | High | High | **MANDATORY CORE** |
| **arXiv:2605.12061** | SAGE: Self-Evolving Agentic Graph-Memory Engine | Wang et al. / arXiv | 2026 | Causal Knowledge Graph | Very High | High | Very High | Very High | **MANDATORY CORE** |
| **arXiv:2605.10813** | NanoResearch: Tri-Level Co-evolving Research | Research Team / arXiv | 2026 | Tri-Level Research Automation | High | Medium | Medium | High | **MANDATORY CORE** |
| **arXiv:2605.20025** | AutoResearchClaw: Debating & Refining Alphas | Kim et al. / arXiv | 2026 | Adversarial Alpha Falsification | Very High | High | High | Very High | **MANDATORY CORE** |
| **arXiv:2605.17734** | HASP: Hierarchical Agentic Skill Programs | Patel et al. / arXiv | 2026 | Program Function Guardrails | Very High | Very High | Very High | High | **MANDATORY CORE** |
| **arXiv:2605.21482** | DeepWeb-Bench: Multi-Dimensional Evaluation | Benchmark Team / arXiv | 2026 | Calibration & ECE Auditing | High | High | High | High | **MANDATORY CORE** |

---

## 3. Full Engineering Decompositions (8 Mandatory Papers)

### 1. EKSFT: Entropy-KL Selective Fine-Tuning (arXiv:2605.29303)
*   **Core Hypothesis**: Standard Supervised Fine-Tuning (SFT) causes mode collapse by forcing memorization of specific target distributions. Selective fine-tuning masking high-entropy or high-KL tokens relative to a reference model preserves RL exploration capacity.
*   **Mathematical Formulation**: Masking set $\mathcal{M} = \{t \mid H(t) > \tau_H \lor D_{KL}(P_{\theta}(t) \parallel P_{ref}(t)) > \tau_{KL}\}$. Loss: $\mathcal{L}_{EKSFT} = \frac{1}{|\mathcal{D} \setminus \mathcal{M}|} \sum_{t \notin \mathcal{M}} \mathcal{L}_{CE}(t) - \lambda_H H(t) + \lambda_{KL} D_{KL}(P_{\theta}(t) \parallel P_{ref}(t))$.
*   **Training & Learning**: Dual-model (active + reference) autoregressive training using AdamW with cosine decay.
*   **Memory & Planning**: Uses parametric memory anchored by static reference model weights.
*   **Agent & World Model**: Protects transition distributions against noisy market ticks.
*   **Self-Improvement**: Gatekeeper for policy evolution, preventing overfitted hallucination loops.
*   **Failure Modes & Limits**: Excessive masking ($\rho > 0.35$) causes learning stagnation; insufficient masking allows distribution collapse.
*   **Complexity & Tradeoffs**: $\mathcal{O}(2 \cdot N_{params})$ forward passes. Increases memory overhead during tuning phase by 100%.
*   **Financial & Production**: Prevents overfitting to historical price paths while preserving regime inference. Implemented as a post-training compliance gate in `EvolutionGate`.

### 2. DiscoLoop: Discrete Embeddings and Continuous Hidden States (arXiv:2607.00341)
*   **Core Hypothesis**: Dual continuous-discrete hidden channels bypass depth limitations in standard Transformers for infinite-horizon reasoning.
*   **Mathematical Formulation**: Recurrence $h_{t+1} = \text{RNN}(h_t, e_t, x_t)$; Discrete token $e_t = \text{Quantize}(W_{discrete} h_t)$; Coupled state $S_t = [h_t ; e_t]$.
*   **Training & Learning**: BPTT with Straight-Through Estimators (STE) for quantized gradients.
*   **Memory & Planning**: Working memory featuring discrete (subgoal logic) and continuous (latent dynamics) channels.
*   **Agent & World Model**: Epistemic core executing internal reflection before acting.
*   **Failure Modes & Limits**: Quantization drift decoupling discrete subgoals from latent market state.
*   **Complexity & Tradeoffs**: $\mathcal{O}(L \cdot D^2)$ for $L$ internal loops. Increases inference latency linearly with loop depth.
*   **Financial & Production**: Critical for multi-step trade attribution across macro shocks, liquidity changes, and order flow execution.

### 3. AutoMem: Automated Learning of Memory as a Cognitive Skill (arXiv:2607.01224)
*   **Core Hypothesis**: Database schemas and consolidation routines can be optimized via success-oriented reinforcement loops.
*   **Mathematical Formulation**: Schema utility $\max_{\phi} \mathbb{E}_{\tau} [R(\tau) - \beta \cdot \text{Cost}(\mathcal{M}_{\phi})]$. Schema update: $V_{t+1} = V_t + \alpha \nabla_V \text{Utility}(\mathcal{M})$.
*   **Training & Learning**: Policy iteration on memory actions (Read, Write, Condense, Purge).
*   **Memory & Planning**: Dynamic 8-tier hierarchy (Working -> Episodic -> Semantic -> Institutional).
*   **Failure Modes & Limits**: Memory "forgetting" rare-event patterns during market regime shifts.
*   **Complexity & Tradeoffs**: $\mathcal{O}(\log N)$ retrieval via vector indexing; schema refinement is $\mathcal{O}(N_{trajectories})$.
*   **Financial & Production**: Learns optimal storage structures for trade logs and market features without manual DBA redesign.

### 4. SAGE: Self-Evolving Agentic Graph-Memory Engine (arXiv:2605.12061)
*   **Core Hypothesis**: Autonomous dynamic graph substrate with TD edge updates eliminates semantic drift found in vector databases.
*   **Mathematical Formulation**: Graph $\mathcal{G} = (V, E)$; Edge update $W_{t+1}(e) = W_t(e) + \eta (\text{Reward}_{feedback} - W_t(e))$.
*   **Training & Learning**: Online Hebbian-style weight updates + offline graph compaction.
*   **Memory & Planning**: Causal Knowledge Graph substrate for multi-hop graph traversal path planning.
*   **Failure Modes & Limits**: Monopoly hub node formation causing retrieval bias.
*   **Complexity & Tradeoffs**: Graph traversal is $\mathcal{O}(V + E)$.
*   **Financial & Production**: Dynamically models non-stationary inter-asset correlations (e.g. Gold vs Yields vs Oil).

### 5. NanoResearch: Tri-Level Co-Evolving Research Automation (arXiv:2605.10813)
*   **Core Hypothesis**: Research automation requires co-evolution of procedural rules (Skill Bank), experience (Memory), and preference alignment (Policy).
*   **Mathematical Formulation**: Co-evolution optimization $\max_{\theta, \mathcal{S}, \mathcal{M}} \mathcal{U}(\theta, \mathcal{S}, \mathcal{M})$.
*   **Training & Learning**: DPO combined with evolutionary search over candidate rule sets.
*   **Financial & Production**: Custom institutional strategy specialization under safety constraints.

### 6. AutoResearchClaw: Debating & Refining Alphas (arXiv:2605.20025)
*   **Core Hypothesis**: Autonomous discovery requires iterative self-healing loops (Pivot/Refine) and structured multi-agent debate to falsify hypotheses.
*   **Mathematical Formulation**: Pivot trigger $\mathbb{P}(\text{Fail} \mid \text{Critique}) > \tau_{pivot} \implies \text{Pivot}(\text{Strategy})$.
*   **Planning & Agent**: Non-linear planning featuring mid-flight recovery and Lopez de Prado Deflated Sharpe Ratio (DSR) verification.
*   **Financial & Production**: Prevents overfitting and data snooping by falsifying strategies prior to deployment.

### 7. HASP: Hierarchical Agentic Skill Programs (arXiv:2605.17734)
*   **Core Hypothesis**: LLM agents must be bounded by executable Program Functions (PFs) that intercept unsafe states.
*   **Mathematical Formulation**: Guardrail mapping $a_{final} = \text{PF}(a_{agent}, s_t)$ if $\text{Trigger}(s_t) = 1$ else $a_{agent}$.
*   **Financial & Production**: Hard-coded risk thresholds that force execution limits or hold orders regardless of LLM overconfidence.

### 8. DeepWeb-Bench: Multi-Dimensional Evaluation (arXiv:2605.21482)
*   **Core Hypothesis**: Agent evaluation requires grading Retrieval, Derivation, Reasoning, and Calibration (ECE).
*   **Mathematical Formulation**: Expected Calibration Error $\text{ECE} = \sum_b \frac{|B_b|}{N} | \text{acc}(B_b) - \text{conf}(B_b) |$.
*   **Financial & Production**: Measures strategic prediction accuracy and ensures confidence levels are calibrated to true market probabilities.
