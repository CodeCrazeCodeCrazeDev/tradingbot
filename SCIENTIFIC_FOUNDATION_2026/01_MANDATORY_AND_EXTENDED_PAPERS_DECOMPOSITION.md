# Scientific Architecture Decomposition: Mandatory & Extended Literature (2026)

This document provides rigorous engineering decompositions for all 8 mandatory arXiv research papers, alongside extended cited/citing literature, serving as concrete engineering specifications for AlphaAlgo's cognitive architecture.

---

## 1. EKSFT: Entropy-KL Selective Fine-Tuning
**Reference:** arXiv:2605.29303

### Engineering Decomposition
- **Core Hypothesis:** Fine-tuning post-RL or supervised fine-tuning (SFT) leads to distribution sharpening and entropy collapse if applied uniformly across all tokens or market observations. Masking high-entropy and high-KL divergence tokens/states during online updating preserves exploratory capacity and prevents catastrophic policy collapse.
- **Mathematical Formulation:**
  $$\mathcal{L}_{\text{EKSFT}}(\theta) = -\sum_{t} M(s_t, a_t) \log \pi_\theta(a_t | s_t)$$
  where the binary mask $M(s_t, a_t)$ is defined as:
  $$M(s_t, a_t) = \mathbb{I}\left( H(\pi_\theta(\cdot | s_t)) \le \tau_H \right) \cdot \mathbb{I}\left( D_{\text{KL}}(\pi_\theta(\cdot | s_t) \parallel \pi_{\text{ref}}(\cdot | s_t)) \le \tau_{\text{KL}} \right)$$
- **Training Methodology:** Dual-threshold dynamic masking during parameter updating and online policy adaptation.
- **Learning Algorithm:** Dynamic token-level and state-level policy gradient filtering.
- **Memory Architecture:** Integrates entropy and KL statistics into the episodic and research memory traces.
- **Planning Architecture:** Non-lossy policy shift boundaries during Monte Carlo search and tree-based plan exploration.
- **Agent Architecture:** Applied in `EvolutionGate` and `AdaptiveControlPolicyEngine` (ACPE) to audit model weight updates.
- **World Model Contribution:** Guarantees world model transitions do not drift into out-of-distribution uncalibrated regimes.
- **Self-Improvement Contribution:** Prevents policy degradation during self-play and online learning.
- **Failure Modes:** Overly restrictive thresholds ($\tau_H, \tau_{\text{KL}}$) block necessary learning under severe regime shifts.
- **Scalability Limits:** $\mathcal{O}(N)$ per update step where $N$ is sequence length or batch size.
- **Financial Applicability:** Prevents overfitting to brief market noise anomalies (e.g. flash crash tail events).
- **Production Readiness:** **High** — Native Python/PyTorch gate check in `EvolutionGate._check_eksft_compliance`.

---

## 2. DiscoLoop: Discrete & Continuous Recurrent Internalization
**Reference:** arXiv:2607.00341

### Engineering Decomposition
- **Core Hypothesis:** Coupling discrete symbolic abstractions (rules, signals, market regimes) with continuous latent representations (embeddings, continuous belief states) in a recurrent loop enables deep multi-hop causal reasoning superior to pure LLM prompt chains or pure vector neural networks.
- **Mathematical Formulation:**
  $$z_t = f_{\text{cont}}(z_{t-1}, d_{t-1}, x_t)$$
  $$d_t = g_{\text{disc}}(z_t, \text{KnowledgeGraph})$$
  $$\mathcal{F}_{\text{VFE}}(z_t, d_t) = \mathbb{E}_{q(z|x)}[\log q(z|x) - \log p(x, z | d)]$$
- **Training Methodology:** Variational Free Energy (VFE) minimization over coupled state trajectories.
- **Learning Algorithm:** Recurrent Variational Inference with discrete state quantization.
- **Memory Architecture:** Dual-channel workspace memory holding discrete symbol sequences and $d$-dimensional continuous hidden vectors.
- **Planning Architecture:** Tree search over discrete symbols conditioned on continuous latent value estimations.
- **Agent Architecture:** Implemented in `CognitiveSystemController` (CSC) `_run_discoloop_internalization`.
- **World Model Contribution:** Predicts dual discrete regime transitions and continuous price distributions.
- **Self-Improvement Contribution:** Refines latent state transitions via active inference updates.
- **Failure Modes:** Mode collapse in discrete quantization or variance explosion in continuous sampling.
- **Scalability Limits:** $\mathcal{O}(K \cdot H)$ where $K$ is discrete vocabulary size and $H$ is hidden dimension size.
- **Financial Applicability:** Models abrupt market regime flips while maintaining smooth volatility estimates.
- **Production Readiness:** **High** — Fully integrated into CSC processing pipeline.

---

## 3. AutoMem: Automated Memory as a Cognitive Skill
**Reference:** arXiv:2607.01224

### Engineering Decomposition
- **Core Hypothesis:** Memory management (read, write, compress, prune, update schema) should not be hardcoded heuristic rules, but treated as first-class, learnable cognitive skill actions optimized via downstream task rewards.
- **Mathematical Formulation:**
  $$\alpha_t \sim \pi_{\text{mem}}(a_{\text{mem}} | s_t)$$
  $$\Delta \mathbf{W}_{\text{schema}} = \eta \cdot R_{\text{downstream}} \nabla_\theta \log \pi_{\text{mem}}(a_{\text{mem}} | s_t)$$
- **Training Methodology:** Policy gradient reinforcement learning on meta-memory schema modifications and edge pruning.
- **Learning Algorithm:** AutoMem Dual-Loop Schema and Weight Optimization.
- **Memory Architecture:** Tier-8 Meta-Memory in `HierarchicalMemorySystem` (HMS).
- **Planning Architecture:** Memory schema updates automatically expose higher-order concepts for planning.
- **Agent Architecture:** `HierarchicalMemorySystem.optimize_metamemory` and schema versioning.
- **World Model Contribution:** Adapts graph schemas dynamically as market structure evolves.
- **Self-Improvement Contribution:** Autonomous memory consolidation without human engineering intervention.
- **Failure Modes:** Unstable schema drift if reward signal is noisy.
- **Scalability Limits:** $\mathcal{O}(M)$ where $M$ is total number of memory schema entities and edges.
- **Financial Applicability:** Dynamically learns to prune stale market regimes and retain long-term macro correlations.
- **Production Readiness:** **High** — Implemented in `HierarchicalMemorySystem`.

---

## 4. SAGE: Self-evolving Agentic Graph-Memory Engine
**Reference:** arXiv:2605.12061

### Engineering Decomposition
- **Core Hypothesis:** Graph memory with static edge weights fails in dynamic environments. Representing memory as a self-evolving graph where edge weights dynamically evolve based on context-sensitive triplet validity and reader-writer feedback loops enables accurate multi-hop retrieval over extended horizons.
- **Mathematical Formulation:**
  $$w_{ij}^{(t+1)} = \text{clip}\left( w_{ij}^{(t)} + \eta \cdot \Delta_{\text{feedback}}, 0.0, 1.0 \right)$$
  $$\text{Score}(u, v) = w_{uv} \cdot \cos(\mathbf{e}_u, \mathbf{e}_v) \cdot \mathbb{I}(\text{Context Match})$$
- **Training Methodology:** Hebbian-inspired online edge weight refinement and low-confidence edge pruning.
- **Learning Algorithm:** Multi-hop BFS retrieval with automated edge compaction.
- **Memory Architecture:** `SAGEGraphMemory` in `trading_bot/core/hms/memory.py`.
- **Planning Architecture:** Provides structured subgraphs as context for counterfactual planning and hypothesis testing.
- **Agent Architecture:** Graph memory substrate utilized by `HierarchicalMemorySystem` and `MultiAgentDebateSystem`.
- **World Model Contribution:** Maps causal dependencies between macro indicators, orderbook signals, and price action.
- **Self-Improvement Contribution:** Automatically prunes edges with weight $w < 0.1$ and strengthens high-utility causal links.
- **Failure Modes:** Disconnection of relevant nodes if pruning threshold is overly aggressive.
- **Scalability Limits:** $\mathcal{O}(V + E)$ graph traversal complexity; mitigated by BFS depth limiting ($h \le 2$).
- **Financial Applicability:** Maps interconnected risk drivers across asset classes and sector correlations.
- **Production Readiness:** **High** — Implemented as NetworkX MultiDiGraph substrate in HMS.

---

## 5. NanoResearch: Tri-level Co-evolving Research Automation
**Reference:** arXiv:2605.10813

### Engineering Decomposition
- **Core Hypothesis:** Autonomous research systems require tri-level co-evolution across three independent planes: Parameter Policies (Level 1), Memory Substrates (Level 2), and Skill Banks (Level 3), preventing catastrophic interference between execution and learning.
- **Mathematical Formulation:**
  $$\theta^{(t+1)} = \text{EKSFT}(\theta^{(t)}, \mathcal{D}_{\text{research}})$$
  $$\mathcal{M}^{(t+1)} = \text{SAGE\_Evolve}(\mathcal{M}^{(t)}, \mathcal{F})$$
  $$\mathcal{S}^{(t+1)} = \mathcal{S}^{(t)} \cup \{ \text{PF}_{\text{validated}} \}$$
- **Training Methodology:** Asynchronous tri-plane updates isolated by governance gates (`EvolutionGate`).
- **Learning Algorithm:** Continuous tri-level co-evolution protocol.
- **Memory Architecture:** Integrates Level 2 graph updates directly into HMS.
- **Planning Architecture:** Level 3 skill program expansion enhances long-horizon execution plans.
- **Agent Architecture:** Coordinated by `CognitiveSystemController` and `EvolutionGate`.
- **World Model Contribution:** Continually upgrades world model transition parameters without stopping execution loops.
- **Self-Improvement Contribution:** Prevents multi-plane corruption via strict isolation gates.
- **Failure Modes:** Synchronization deadlocks across planes if asynchronous locks fail.
- **Scalability Limits:** $\mathcal{O}(P_1 + P_2 + P_3)$ independent scaling per plane.
- **Financial Applicability:** Multi-horizon trading strategy research and automated quantitative signal creation.
- **Production Readiness:** **High** — Enforced by `EvolutionGate` and CSC.

---

## 6. AutoResearchClaw: Self-Reinforcing Autonomous Research
**Reference:** arXiv:2605.20025

### Engineering Decomposition
- **Core Hypothesis:** Single-pass reasoning or execution in complex domains leads to undetected errors. A self-reinforcing pivot-and-refine execution loop with dual adversarial verifiers detects failures, generates hypotheses, and iteratively fixes code or plans.
- **Mathematical Formulation:**
  $$P(\text{Success} | x) = \prod_{k=1}^K \mathbb{I}(\text{Verifier}_k(x) = 1)$$
  $$\text{Pivot}(x) = x + \nabla_x \mathcal{L}_{\text{adversarial}}(x)$$
- **Training Methodology:** Iterative falsification and counterfactual refinement loops.
- **Learning Algorithm:** Double-verifier pivot-and-refine execution loop.
- **Memory Architecture:** Saves falsified plans and failure traces in research ledger.
- **Planning Architecture:** Automatically triggers re-planning and strategy pivoting upon verifier rejection.
- **Agent Architecture:** Step-10 pivot-refine loop in `CognitiveSystemController`.
- **World Model Contribution:** Validates strategy scenarios against hostile synthetic market environments.
- **Self-Improvement Contribution:** Converts execution failures into structured negative lessons.
- **Failure Modes:** Infinite pivot loops if step limit $K_{\text{max}}$ is not enforced.
- **Scalability Limits:** $\mathcal{O}(K_{\text{refine}} \cdot C_{\text{verifier}})$ computation multiplier.
- **Financial Applicability:** Rejects overfitted trading strategies prior to live deployment.
- **Production Readiness:** **High** — Integrated into CSC and `MultiAgentDebateSystem`.

---

## 7. HASP: Harnessing LLM Agents with Skill Programs
**Reference:** arXiv:2605.17734

### Engineering Decomposition
- **Core Hypothesis:** Open-ended LLM generations must be constrained by non-bypassable, deterministic Program Functions (PFs) that intercept agent calls, verify strict numerical and safety invariants, and fall back to safe actions upon violation.
- **Mathematical Formulation:**
  $$a_{\text{final}} = \begin{cases} a_{\text{agent}}, & \text{if } \mathbf{C}_{\text{safety}}(a_{\text{agent}}, s) = \text{TRUE} \\ \text{PF}_{\text{fallback}}(s), & \text{otherwise} \end{cases}$$
- **Training Methodology:** Static and runtime formal invariant verification.
- **Learning Algorithm:** Executable guardrail interception and Program Function routing.
- **Memory Architecture:** Stores registered safety PFs in Procedural Memory.
- **Planning Architecture:** Constrains search space to valid, safe invariant regions.
- **Agent Architecture:** Implemented in `SkillRouter` and `EvolutionGate`.
- **World Model Contribution:** Enforces physical/financial realism on model predictions (e.g. leverage limits, liquidity constraints).
- **Self-Improvement Contribution:** Prevents self-modifying code from removing security/risk constraints.
- **Failure Modes:** Fallback action triggering under non-critical edge cases if guardrails are overly conservative.
- **Scalability Limits:** $\mathcal{O}(1)$ deterministic code execution overhead.
- **Financial Applicability:** Prevents unauthorized position size expansion, extreme leverage, or risk limit bypasses.
- **Production Readiness:** **High** — Hardened inside `SkillRouter`.

---

## 8. DeepWeb-Bench: Multi-Dimensional Evidence Calibration
**Reference:** arXiv:2605.21482

### Engineering Decomposition
- **Core Hypothesis:** Evaluates systems across multi-dimensional evidence sources (news, sentiment, orderbook, price) and demands precise calibration (minimizing Expected Calibration Error, ECE) rather than raw overconfident accuracy.
- **Mathematical Formulation:**
  $$\text{ECE} = \sum_{m=1}^M \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$
  $$\text{Loss}_{\text{calibrated}} = \mathcal{L}_{\text{task}} + \lambda \cdot \text{ECE}$$
- **Training Methodology:** Out-of-sample probability binning and Platt scaling / isotonic regression.
- **Learning Algorithm:** Multi-source confidence calibration and Brier score optimization.
- **Memory Architecture:** Records historical forecast confidence and actual outcomes in research ledger.
- **Planning Architecture:** Weighs decision paths by calibrated probabilities rather than raw agent scores.
- **Agent Architecture:** Embedded in `MultiAgentDebateSystem` (`BayesianDecisionEngine`) and `EvolutionGate`.
- **World Model Contribution:** Calibrates state transition probability distributions against real market outcomes.
- **Self-Improvement Contribution:** Rejects self-modifications that increase confidence without increasing accuracy.
- **Failure Modes:** Underconfident agent outputs if calibration penalty $\lambda$ is set too high.
- **Scalability Limits:** $\mathcal{O}(B)$ bin computation cost.
- **Financial Applicability:** Ensures position sizing strictly reflects actual statistical probability of trade success.
- **Production Readiness:** **High** — Integrated into validation benchmarks and debate calibration.

---

## 9. Extended Literature Expansions

### A. RSEA: Recursive Self-Evolving Agents (arXiv:2606.28374)
- **Contribution:** Monotone-safe update protocol ensuring every self-modification strictly increases system performance $G \ge \tau$ without causing safety or latency regressions.
- **Integration Point:** `EvolutionGate.validate_evolution`.

### B. LogAct: Shared-Log Agent Backbone (arXiv:2605.11200)
- **Contribution:** Append-only, thread-safe decision event log providing full auditability and temporal reproducibility.
- **Integration Point:** `trading_bot.core.unified_event_bus.UnifiedDecisionBus`.

### C. S2L: System-1 / System-2 Hybrid Routing (arXiv:2604.09912)
- **Contribution:** Dynamic switching between ultra-fast System-1 reactive execution ($< 5\text{ms}$) and deep System-2 deliberative debate depending on market volatility and uncertainty.
- **Integration Point:** `SkillRouter.route_task`.

### D. CL-Bench: Continuous Learning Benchmark (arXiv:2603.14800)
- **Contribution:** Standardized gain metric $G = \text{Performance}_{\text{new}} - \text{Performance}_{\text{old}}$ for evaluating continuous learning without catastrophic forgetting.
- **Integration Point:** `tests/validation/test_uca_v5_scientific_benchmarks.py`.

---

## 10. Summary Matrix of Reusable Scientific Algorithms

| Algorithm / Principle | Source Paper | Core Module | Primary Function |
| :--- | :--- | :--- | :--- |
| Dynamic Entropy-KL Token Masking | EKSFT (arXiv:2605.29303) | `EvolutionGate` / ACPE | Prevents entropy collapse during online updating |
| Coupled Discrete-Continuous Latent Loop | DiscoLoop (arXiv:2607.00341) | `CognitiveSystemController` | Two-hop causal reasoning & active inference |
| Skill-Based Metamemory Schema Optimization | AutoMem (arXiv:2607.01224) | `HierarchicalMemorySystem` | Learnable memory retention & schema evolution |
| Dynamic Graph Memory & Hebbian Edge Evolution | SAGE (arXiv:2605.12061) | `SAGEGraphMemory` | Self-evolving multi-hop causal graph |
| Tri-plane Co-evolution Isolation | NanoResearch (arXiv:2605.10813) | `EvolutionGate` / CSC | Multi-plane safe self-improvement |
| Double-Verifier Pivot-and-Refine Loop | AutoResearchClaw (arXiv:2605.20025)| `MultiAgentDebateSystem` | Self-reinforcing hypothesis generation & verification |
| Non-Bypassable Program Function Guardrails | HASP (arXiv:2605.17734) | `SkillRouter` | Invariant enforcement & safety fallback |
| Expected Calibration Error (ECE) Minimization | DeepWeb-Bench (arXiv:2605.21482)| `BayesianDecisionEngine` | Multi-source probability confidence calibration |
