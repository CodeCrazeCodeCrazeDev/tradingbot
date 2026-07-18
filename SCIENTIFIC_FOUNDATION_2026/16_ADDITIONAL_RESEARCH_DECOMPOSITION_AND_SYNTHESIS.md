# Additional Research Decomposition, Synthesis, and Refactoring Plan

This document details the architectural integration of eight mandatory frontier AI research papers into AlphaAlgo's Unified Cognitive Architecture (UCA V5+), forming the cornerstone of the Autonomous Quantitative Research Institution (AQRI).

---

## Part 1: Scientific Decomposition of Mandatory Research Papers

### 1. EKSFT: Entropy-KL Selective Fine-Tuning
*   **Core Hypothesis**: Standard supervised fine-tuning (SFT) over-optimizes on token sequences, leading to distribution sharpening and entropy collapse, which destroys the exploratory potential of downstream reinforcement learning. Prioritizing task-relevant capability activation via Entropy-KL selective token filtering preserves model entropy and exploration capabilities.
*   **Mathematical Formulation**:
    Tokens $t$ are masked if they are outside the selective set $\mathcal{M} = \mathcal{M}_H \cup \mathcal{M}_{KL}$.
    $$\mathcal{L}_{EKSFT}(\theta) = \mathcal{L}_{CE}^{mask}(\theta) - \lambda_H \mathcal{H}^{mask}(\theta) + \lambda_{KL} D_{KL}^{mask}(\pi_{\theta} \| \pi_{ref})$$
    where the mask selectively activates only when $\mathcal{H}(\pi_{ref}) \in [\tau_1, \tau_2]$ and $D_{KL}(\pi_{\theta} \| \pi_{ref}) \le \tau_{KL}$.
*   **Training Methodology**: Post-training cold-start alignment.
*   **Learning Algorithm**: Selective gradient masking during backpropagation. Gradients are scaled to 0 for unselected tokens.
*   **Memory Architecture**: Uses parameter-space memory (the SFT baseline model acting as a strong explorer initialization).
*   **Planning Architecture**: Non-direct; enhances planning by preserving exploration diversity in the action token distribution.
*   **Agent Architecture**: Applied to policy model initialization before RL rollout begins.
*   **World Model Contribution**: Restricts the agent's simulated futures from collapsing into a single deterministic path.
*   **Self-Improvement Contribution**: Establishes a safe domain boundary to prevent "delusional" optimization steps during model updates.
*   **Failure Modes**: Excessive masking ($\rho > 0.3$) leads to loss of task capability due to insufficient training signals.
*   **Scalability Limits**: Scalable up to arbitrary context lengths, bounded strictly by vocabulary size and tokenization speed.
*   **Computational Complexity**: $\mathcal{O}(N \cdot V)$ per step where $V$ is vocabulary size and $N$ is sequence length.
*   **Engineering Tradeoffs**: Preserves token-entropy at the cost of slight degradation in pure rule memorization.
*   **Financial Applicability**: Critical for preventing trading policies from overfitting to specific historical tick sequences (regime memorization).
*   **Production Readiness**: Production-ready. Easily implemented as custom loss mask filters in PyTorch / Hugging Face Trainer.
*   **Extracted Reusable Algorithm**:
    ```python
    def compute_eksft_mask(logits, ref_logits, lambda_h, lambda_kl):
        probs = softmax(logits)
        ref_probs = softmax(ref_logits)
        entropy = -sum(probs * log(probs))
        kl = sum(probs * log(probs / ref_probs))
        mask = (entropy > t1) & (entropy < t2) & (kl < t_kl)
        return mask
    ```

### 2. DiscoLoop: Looping Discrete Embeddings and Continuous Hidden States
*   **Core Hypothesis**: Transformers struggle with multi-hop reasoning over long intervals due to depth-local representation limitations. Looping continuous hidden states ($h_k$) coupled with discrete symbol embeddings ($e_k$) solves representational bottlenecks in multi-step reasoning.
*   **Mathematical Formulation**:
    $$S_k = [h_k; e_k]$$
    $$h_{k+1} = \tanh(W_{hh} h_k + W_{eh} e_k + b_h)$$
    $$e_{k+1} = \text{Quantize}(W_{he} h_{k+1} + b_e)$$
*   **Training Methodology**: Unsupervised sequence representation learning.
*   **Learning Algorithm**: Mixed continuous-discrete backpropagation using straight-through estimators.
*   **Memory Architecture**: Dual-path memory (continuous latent vectors stored in state variables, discrete symbolic bridges stored in context).
*   **Planning Architecture**: Multihop reasoning within a single action step via internal recurrence.
*   **Agent Architecture**: Implemented as the core reasoning engine in the Cognitive System Controller.
*   **World Model Contribution**: Empowers multi-step transition predictions by looping latent states recursively.
*   **Self-Improvement Contribution**: Supports self-correction cycles within a single inference execution.
*   **Failure Modes**: Loop instability, vanishing continuous gradients, or discrete codebook collapse.
*   **Scalability Limits**: Bounded by the recurrence depth $K$ (empirically stable for $K \le 8$).
*   **Computational Complexity**: $\mathcal{O}(K \cdot D^2)$ where $K$ is the number of loops and $D$ is the continuous state dimension.
*   **Engineering Tradeoffs**: Drastically increases internal reasoning depth but adds recurrent latency per execution.
*   **Financial Applicability**: Allows real-time correlation processing (A $\to$ B $\to$ C market reactions) in sub-millisecond execution times.
*   **Production Readiness**: High; standard implementation uses static tensor matrices.
*   **Extracted Reusable Algorithm**:
    ```python
    # See DiscoLoopCell implementation inside controller.py
    ```

### 3. AutoMem: Automated Learning of Memory as a Cognitive Skill
*   **Core Hypothesis**: Memory management is an independently learnable cognitive skill (metamemory) that can be optimized autonomously through self-evaluation loops.
*   **Mathematical Formulation**:
    $$M_{t+1} = \text{Write}(M_t, I_t, \omega_t)$$
    $$\omega^* = \arg\max_{\omega} \mathbb{E}_{\tau} [R(\tau) - \beta \cdot \text{Cost}(M_t)]$$
*   **Training Methodology**: Direct policy optimization over memory actions (Write/Prune/Optimize).
*   **Learning Algorithm**: Trajectory-based reinforcement learning using self-critique.
*   **Memory Architecture**: Self-adjusting multi-tier storage with write-through locks.
*   **Planning Architecture**: Injects contextually relevant past strategies into current subgoals.
*   **Agent Architecture**: Promotes file operations to first-class agent actions.
*   **World Model Contribution**: Prevents stale information from corrupting the transition dynamics.
*   **Self-Improvement Contribution**: Automates index schema updates and key-value clustering.
*   **Failure Modes**: Catastrophic forgetting of critical safety rules if pruning is over-optimized.
*   **Scalability Limits**: Scale is bounded only by the capacity of the backing database.
*   **Computational Complexity**: $\mathcal{O}(\log |M|)$ for hierarchical retrievals.
*   **Engineering Tradeoffs**: Reduces average context token usage but requires periodic offline schema re-indexing.
*   **Financial Applicability**: Automatically learns which market events (such as past flash crashes) are worth preserving in high-resolution episodic journals.
*   **Production Readiness**: Production-ready.
*   **Extracted Reusable Algorithm**:
    ```python
    # See AutoMem optimization inside memory.py
    ```

### 4. SAGE: Self-evolving Agentic Graph-memory Engine
*   **Core Hypothesis**: Passive RAG systems are insufficient for non-stationary environments. Graph-memory must be a self-evolving agentic substrate, updating causal relations based on execution outcomes.
*   **Mathematical Formulation**:
    $$\mathcal{G} = (V, E, W)$$
    $$W_{u,v}^{t+1} = \text{clip}(W_{u,v}^t + \alpha \cdot \text{Feedback}(u, v), 0, 1)$$
*   **Training Methodology**: Dynamic reinforcement of causal links.
*   **Learning Algorithm**: Graph node optimization and Edge Pruning via GFM feedback.
*   **Memory Architecture**: Graph-native (NetworkX / Neo4j backplanes).
*   **Planning Architecture**: Generates dynamic multi-hop evidence pathways for verification.
*   **Agent Architecture**: Decouples the memory writer (observer) from the memory reader.
*   **World Model Contribution**: Directly maps evolving correlations between financial assets as a graph topology.
*   **Self-Improvement Contribution**: Prunes invalid or outdated causal connections.
*   **Failure Modes**: Graph fragmentation or runaway consolidation (converging to a single giant component).
*   **Scalability Limits**: Highly scalable, bounded by graph traversal depths.
*   **Computational Complexity**: $\mathcal{O}(|V| \log |V|)$ for clustering and $\mathcal{O}(D)$ for retrieval traversal.
*   **Engineering Tradeoffs**: Highly accurate context but introduces overhead during multi-hop structural traversals.
*   **Financial Applicability**: Allows AlphaAlgo to maintain an active model of macro interdependencies (e.g. Yield Curve $\to$ DXY $\to$ Gold).
*   **Production Readiness**: High.
*   **Extracted Reusable Algorithm**:
    ```python
    # See SAGEGraphMemory in memory.py
    ```

### 5. NanoResearch: Tri-level Co-evolving Research Automation
*   **Core Hypothesis**: Effective automated quantitative research requires a tri-level co-evolution of (1) operational skills, (2) project-specific memory, and (3) label-free preference policy optimization.
*   **Mathematical Formulation**:
    $$\mathcal{L}_{Nano}(\theta, \mathcal{S}, \mathcal{M}) = \mathcal{L}_{policy}(\theta | \mathcal{S}, \mathcal{M}) + \gamma_1 \mathcal{L}_{skill}(\mathcal{S}) + \gamma_2 \mathcal{L}_{mem}(\mathcal{M})$$
*   **Training Methodology**: Simultaneous iterative refinement of LoRA modules, schemas, and rule cards.
*   **Learning Algorithm**: Joint coordinate descent over parameters and symbolic configurations.
*   **Memory Architecture**: Integrated episodic and semantic layers.
*   **Planning Architecture**: Iterative research-step decomposition.
*   **Agent Architecture**: Team of co-evolving agents (Director, Quant, Coder).
*   **World Model Contribution**: Aligns research hypotheses with empirically generated market simulations.
*   **Self-Improvement Contribution**: Continuous evolution of code snippets and optimization rules.
*   **Failure Modes**: Feedback loops resulting in degenerate research paths (the "echo chamber" effect).
*   **Scalability Limits**: Bounded by compute budget.
*   **Computational Complexity**: High; requires sequential generation and validation steps.
*   **Engineering Tradeoffs**: Exceptional customization to specific market tasks, with elevated training overhead.
*   **Financial Applicability**: Maximizes model-adaptation when entering entirely new trading environments.
*   **Production Readiness**: Medium (requires robust sandboxing).
*   **Extracted Reusable Algorithm**: Tri-level alignment loop.

### 6. AutoResearchClaw: Self-Reinforcing Autonomous Research
*   **Core Hypothesis**: Autonomous quantitative research is fundamentally an error-correcting process requiring a multi-agent debate and a self-healing "Pivot/Refine" executor.
*   **Mathematical Formulation**:
    $$\text{Pivot}(B) \to B' \text{ s.t. } D_{KL}(B' \| B) > \delta \land \mathcal{F}(B') < \mathcal{F}(B)$$
    where $B$ is the reasoning branch and $\mathcal{F}$ is free energy (surprise/risk).
*   **Training Methodology**: Verification-directed prompt and trajectory optimization.
*   **Learning Algorithm**: Double-loop optimization (Inner loop: Refinement, Outer loop: Pivot).
*   **Memory Architecture**: Uses verified trajectories as few-shot exemplars.
*   **Planning Architecture**: Non-linear branch-aware tree search with backtracking.
*   **Agent Architecture**: Self-correcting execution agents with structural vetoes.
*   **World Model Contribution**: Feeds back negative results to adjust the World Model's transition priors.
*   **Self-Improvement Contribution**: Continuous tuning of strategic proposals.
*   **Failure Modes**: Infinite loop during Pivot/Refine if error boundaries are too permissive.
*   **Scalability Limits**: Highly scalable.
*   **Computational Complexity**: Linear with respect to the pivot depth: $\mathcal{O}(A \cdot C)$ where $A$ is the number of attempts.
*   **Engineering Tradeoffs**: Eliminates execution-level failures at the cost of higher latency during regime shifts.
*   **Financial Applicability**: Allows trading execution models to mid-flight pivot stop-loss levels when structural anomalies are detected.
*   **Production Readiness**: High (essential for live operation safety).
*   **Extracted Reusable Algorithm**:
    ```python
    # See Pivot/Refine loop in CognitiveSystemController.process_market_observation
    ```

### 7. HASP: Harnessing LLM Agents with Skill Programs
*   **Core Hypothesis**: Textual system prompts are advisory; agents require non-bypassable, executable guardrails (Program Functions) to guarantee safe states under extreme environments.
*   **Mathematical Formulation**:
    $$\pi_{safe}(a | s) = (1 - g(s)) \cdot \pi_{llm}(a | s) + g(s) \cdot \delta_{pf}(a)$$
    where $g(s) \in \{0, 1\}$ is a deterministic program trigger and $\delta_{pf}$ is the hard-coded safety action.
*   **Training Methodology**: Direct code injection and capability routing.
*   **Learning Algorithm**: Programmatic state interception.
*   **Memory Architecture**: Executable schema files (e.g. volatility limits) mapped directly to operational checks.
*   **Planning Architecture**: Safety-first pruning of the search space.
*   **Agent Architecture**: Active routing of tasks to hard guardrails (Program Functions) instead of LLMs.
*   **World Model Contribution**: Safe model clamp preventing extreme out-of-bounds inputs.
*   **Self-Improvement Contribution**: Immutable limits on model self-rewriting capabilities.
*   **Failure Modes**: Rigid safety rules resulting in premature halting of system execution.
*   **Scalability Limits**: Unlimited scalability, zero inference overhead.
*   **Computational Complexity**: $\mathcal{O}(1)$ trigger checks.
*   **Engineering Tradeoffs**: Guarantees safety at the cost of bounding model adaptability in unmodeled black-swan events.
*   **Financial Applicability**: Absolute enforcement of position limits and stop-loss execution, even if the LLM undergoes "hallucinations."
*   **Production Readiness**: Production-ready.
*   **Extracted Reusable Algorithm**:
    ```python
    # See volatility_guardrail execution in SkillRouter
    ```

### 8. DeepWeb-Bench: Massive Cross-Source Evidence Benchmark
*   **Core Hypothesis**: The primary bottleneck of autonomous systems is not information retrieval, but derivation and calibration (confidence estimation) under conflicting evidence streams.
*   **Mathematical Formulation**:
    $$\text{CalibrationError} = \sum_{b=1}^B \frac{|I_b|}{N} |p_b - \hat{q}_b|$$
    where $p_b$ is the model's confidence and $\hat{q}_b$ is the true accuracy in bin $b$.
*   **Training Methodology**: Calibration optimization via direct preference tuning.
*   **Learning Algorithm**: Expected Calibration Error (ECE) minimization.
*   **Memory Architecture**: Deep audit trails matching conclusions to source provenance.
*   **Planning Architecture**: Verification checks evaluating evidence quality.
*   **Agent Architecture**: Evaluator-Optimizer model requiring verifiable citations.
*   **World Model Contribution**: Establishes error distributions for transition predictions.
*   **Self-Improvement Contribution**: Exposes hidden bias and overconfidence.
*   **Failure Modes**: Overly conservative actions if calibration bounds are too tight.
*   **Scalability Limits**: Bounded by verification computation.
*   **Computational Complexity**: $\mathcal{O}(N^2)$ for cross-source conflict resolution.
*   **Engineering Tradeoffs**: Drastically increases decision reliability while requiring extensive validation steps.
*   **Financial Applicability**: Enforces a "double-check" protocol before large capital commitments, matching data streams across multiple brokers.
*   **Production Readiness**: High (mandatory for risk reporting).
*   **Extracted Reusable Algorithm**: Real-time ECE tracking.

---

## Part 2: Gap Analysis Matrix

Comparing AlphaAlgo's current implementation against these extracted scientific principles.

| Principle | Mandatory Source | Implementation Status | Path to Superiority / Refactoring Step |
| :--- | :--- | :--- | :--- |
| **Selective Fine-Tuning** | EKSFT | **Partially implemented** | Integrate Entropy-KL selectivity filter during self-improvement updates. |
| **Discrete-Continuous Looping** | DiscoLoop | **Partially implemented** | Enhance the internal recurrence inside `process_market_observation` by strengthening mixed-channel transformations. |
| **Metamemory Skills** | AutoMem | **Partially implemented** | Implement dynamic schema version increments and trace optimizations in HMS. |
| **Agentic Graph-Memory** | SAGE | **Partially implemented** | Upgrade `SAGEGraphMemory` to support robust edge reinforcement and dynamic node contraction. |
| **Pivot/Refine Execution** | AutoResearchClaw | **Partially implemented** | Hard-code the dual-loop retry mechanism inside CSC for verification failures. |
| **Skill Programs (PFs)** | HASP | **Partially implemented** | Ensure volatility guardrails and program functions directly override standard model actions. |
| **Evidence Calibration** | DeepWeb-Bench | **Partially implemented** | Enforce multi-dimensional confidence vectors during trade proposals. |

---

## Part 3: Scientific Synthesis of the Unified Architecture

The final unified architecture integrates these eight papers into a **Recursive Active Inference Engine** (UCA V5+).

```
                                +-------------------+
                                | Market Observation|
                                +---------+---------+
                                          |
                                          v
+-------------------+           +---------+---------+
| SAGE Graph-Memory | <=======> |   CSC Controller  | <=======> +-------------------------+
| (Dynamic Substrate|           | (12-Step DiscoLoop|           |  HASP Program Functions |
+-------------------+           +---------+---------+           | (Hard Guardrails)       |
                                          |                     +-------------------------+
                                          v
                                +---------+---------+
                                |  Pivot/Refine Loop|
                                +---------+---------+
                                          |
                                          v
                                +---------+---------+
                                | Immutable Shield  |
                                +---------+---------+
```

### Key Integration Mechanics:
1.  **Surprise-Driven Retrieval**: Sensory surprise is calculated. If VFE exceeds a dynamic threshold, the CSC queries SAGE for an evidence chain.
2.  **Continuous-Discrete Recurrence**: The CSC executes $K$ rounds of DiscoLoop, carrying continuous hidden states and discrete semantic tokens forward to represent multi-hop connections.
3.  **Active Safety**: HASP Program Functions evaluate the state; any safety violation triggers an immediate, non-bypassable hold.
4.  **Monotone-Safe Backplane**: Code updates are strictly gated by RSEA monotone-safe validation rules, validated on out-of-sample datasets.

---

## Part 4: Refactoring Plan

### 1. Dependency Graph
```
[SAGEGraphMemory] --> [HierarchicalMemorySystem]
                             |
                             v
[SkillRouter / HASP] --> [CognitiveSystemController] <-- [InformationFolder]
                             |
                             v
                     [ImmutableShield]
```

### 2. Migration Graph
1.  Update `trading_bot/core/csc/controller.py` to refine the 12-stage active inference pipeline, including DiscoLoop states.
2.  Refine `trading_bot/core/hms/memory.py` to upgrade graph evolution (SAGE) and optimize memory schema (AutoMem).
3.  Update unit tests in `tests/uca_v5/test_csc_v5.py` to correctly verify the integrated scientific principles.

### 3. Risk Analysis and Rollback Strategy
*   *Risk*: Recurrent loops inside CSC cause performance degradation or infinite loops.
    -   *Mitigation*: Enforce a hard clamp on `_max_loops <= 5` and a strict timeout threshold of 5.0s.
    -   *Rollback*: Restore unmodified files from git immediately via `git checkout`.

### 4. Benchmark and Validation Plan
*   Run the test suite `tests/uca_v5/test_csc_v5.py` to verify that all active inference steps execute flawlessly, and check coverage.
