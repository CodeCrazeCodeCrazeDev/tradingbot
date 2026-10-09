# Phase 1: Mandatory Research Papers Engineering Decomposition (2026)

This document provides a formal, production-grade engineering decomposition for all eight mandatory post-2025 arXiv references in AlphaAlgo's Unified Scientific Architecture (UCA-2026).

---

## 1. Paper 1: EKSFT — Entropy-KL Selective Fine-Tuning
* **arXiv Reference:** arXiv:2605.29303
* **Core Hypothesis:** Selectively masking tokens based on entropy and KL-divergence bounds during fine-tuning prevents catastrophic forgetting and preserves calibrated uncertainty estimates.
* **Mathematical Formulation:**
  $$\mathcal{L}_{\text{EKSFT}} = \sum_{t} \mathbb{I}(H(p_t) \le \tau_H \land D_{\text{KL}}(p_t \parallel q_t) \le \tau_{\text{KL}}) \cdot \mathcal{L}_{\text{CE}}(y_t, p_t)$$
* **Training Methodology:** Adaptive token masking with entropy thresholding ($\tau_H$) and KL drift bounds ($\tau_{\text{KL}}$).
* **Learning Algorithm:** Token-level masked policy gradient / cross-entropy alignment.
* **Memory Architecture:** Preserves historical reference policy logits in compact memory buffers.
* **Planning Architecture:** Informs uncertainty bounds during branch generation in hierarchical planning.
* **Agent Architecture:** Multi-agent debate confidence weighting based on epistemic entropy.
* **World Model Contribution:** Calibrates state transition predictive distributions.
* **Self-Improvement Contribution:** Prevents policy degeneration during recursive self-fine-tuning.
* **Failure Modes:** Overly conservative thresholds ($\tau_H \to 0$) halt learning; loose bounds allow catastrophic forgetting.
* **Scalability Limits:** $\mathcal{O}(T)$ linear in sequence length $T$.
* **Computational Complexity:** $\mathcal{O}(V)$ per token where $V$ is vocabulary size.
* **Engineering Tradeoffs:** Memory overhead for reference policy logits vs. policy stability.
* **Financial Applicability:** Prevents overfitting to short-term market regime anomalies.
* **Production Readiness:** High. Integrated into `trading_bot/core/csc/acpe.py` and `trading_bot/systems_ai/self_improvement.py`.

---

## 2. Paper 2: DiscoLoop — Discrete-Continuous Recurrent Reasoning
* **arXiv Reference:** arXiv:2607.00341
* **Core Hypothesis:** Alternating discrete symbolic entity tokens and continuous latent state transitions in recurrent reasoning loops eliminates context drift and enables multi-hop causal inference.
* **Mathematical Formulation:**
  $$h_{k+1} = \tanh(W_h h_k + W_e e_k + W_x x_{\text{obs}})$$
  $$e_{k+1} = \text{one\_hot}(\arg\max |h_{k+1}|)$$
* **Training Methodology:** End-to-end discrete-continuous state machine optimization.
* **Learning Algorithm:** Dynamic state recurrence with discrete entity token projection.
* **Memory Architecture:** Dual continuous-discrete working memory channel.
* **Planning Architecture:** Multi-hop reasoning loop cell (`DiscoLoopCell`) inside Cognitive System Controller.
* **Agent Architecture:** Enforces state machine consensus across multi-agent debate sessions.
* **World Model Contribution:** Models hybrid discrete market regime transitions and continuous price dynamics.
* **Self-Improvement Contribution:** Stabilizes long-horizon plan execution tracking.
* **Failure Modes:** Vanishing gradients in long recurrence loops ($k > 10$); discrete entity saturation.
* **Scalability Limits:** Bounded loop iterations ($k \le 5$).
* **Computational Complexity:** $\mathcal{O}(k \cdot d^2)$ where $d$ is latent dimension size.
* **Engineering Tradeoffs:** Recurrence latency vs. reasoning depth.
* **Financial Applicability:** Multi-step causal reasoning over microstructural order flow and macroeconomic events.
* **Production Readiness:** Production-ready. Core component in `trading_bot/core/csc/controller.py`.

---

## 3. Paper 3: AutoMem — Dynamic Metamemory Schema Migration
* **arXiv Reference:** arXiv:2607.01224
* **Core Hypothesis:** Autonomous dual-loop metamemory optimization dynamically restructures database schemas and index weights based on access frequency and retrieval failure rates.
* **Mathematical Formulation:**
  $$S^* = \arg\max_S \sum_{i} \left( \text{Utility}(q_i, S) - \lambda \cdot \text{Latency}(q_i, S) \right)$$
* **Training Methodology:** Continuous offline index optimization and online schema version migration.
* **Learning Algorithm:** Reinforcement learning over database schema search spaces.
* **Memory Architecture:** Self-evolving relational and vector graph store with versioned schemas.
* **Planning Architecture:** Accelerates context retrieval for active inference planning.
* **Agent Architecture:** Provides agent-specific indexed memory partitions with zero cross-talk.
* **World Model Contribution:** Fast indexing of historical world model simulation outcomes.
* **Self-Improvement Contribution:** Automated database schema migration without downtime.
* **Failure Modes:** Premature schema migration under non-stationary query distributions.
* **Scalability Limits:** Sub-linear retrieval time $\mathcal{O}(\log N)$.
* **Computational Complexity:** $\mathcal{O}(N \cdot d)$ for graph index updates.
* **Engineering Tradeoffs:** Migration I/O spikes vs. long-term query throughput.
* **Financial Applicability:** Fast retrieval of relevant historical market regimes and trading executions.
* **Production Readiness:** High. Integrated into `trading_bot/core/hms/memory.py`.

---

## 4. Paper 4: SAGE — Dynamic Self-Evolving Graph Memory
* **arXiv Reference:** arXiv:2605.12061
* **Core Hypothesis:** Representing knowledge as a dynamically evolving triplet evidence graph ($G = (V, E)$) enables multi-hop causal reasoning and continuous pruning of invalid hypotheses.
* **Mathematical Formulation:**
  $$w_{ij}^{(t+1)} = \sigma\left(\gamma \cdot w_{ij}^{(t)} + \eta \cdot \text{CoOccurrence}(v_i, v_j) - \delta \cdot \text{Falsification}(v_i, v_j)\right)$$
* **Training Methodology:** Online edge weight propagation and triplet validity verification.
* **Learning Algorithm:** Graph neural network edge propagation with falsification decay.
* **Memory Architecture:** Triplet graph memory storing evidence nodes and causal edges.
* **Planning Architecture:** Causal graph search over competing hypothesis branches.
* **Agent Architecture:** Multi-agent debate evidence graph sharing and verification.
* **World Model Contribution:** Structural causal model representation of financial instruments.
* **Self-Improvement Contribution:** Prunes invalid or refuted causal paths automatically.
* **Failure Modes:** Graph densification under noise without aggressive pruning ($\delta$).
* **Scalability Limits:** $\mathcal{O}(|V| + |E|)$ graph traversal complexity.
* **Computational Complexity:** $\mathcal{O}(|E|)$ per graph update pass.
* **Engineering Tradeoffs:** Graph storage footprint vs. causal reasoning depth.
* **Financial Applicability:** Uncovers complex inter-market supply chain and credit relationships.
* **Production Readiness:** High. Core substrate in `trading_bot/core/hms/memory.py`.

---

## 5. Paper 5: NanoResearch — Dynamic Tri-Level Skill Scorecards
* **arXiv Reference:** arXiv:2605.10813
* **Core Hypothesis:** Maintaining co-evolving agent scorecards across micro, meso, and macro reasoning levels allows adaptive skill selection and optimal task routing.
* **Mathematical Formulation:**
  $$\text{Score}_a = \alpha \cdot \text{Accuracy}_a + \beta \cdot \text{Calibration}_a - \gamma \cdot \text{Latency}_a$$
* **Training Methodology:** Online Bayesian scorecard updates following task execution.
* **Learning Algorithm:** Multi-armed bandit with Upper Confidence Bound (UCB) scorecard selection.
* **Memory Architecture:** Scorecard registry storing agent historical performance across tasks.
* **Planning Architecture:** Routes execution subtasks to top-performing specialized agents.
* **Agent Architecture:** Dynamic agent scorecard and specialization assignment.
* **World Model Contribution:** Selects domain-specific world model sub-simulators.
* **Self-Improvement Contribution:** Demotes degraded agents and promotes high-performing strategies.
* **Failure Modes:** Scorecard cold-start variance; exploration stagnation.
* **Scalability Limits:** $\mathcal{O}(K)$ where $K$ is the number of active skills/agents.
* **Computational Complexity:** $\mathcal{O}(1)$ lookup and score update.
* **Engineering Tradeoffs:** Exploration rate ($\epsilon$) vs. exploit efficiency.
* **Financial Applicability:** Selects specialized trading bots for trending vs. sideways regimes.
* **Production Readiness:** High. Integrated into `trading_bot/core/csc/router.py`.

---

## 6. Paper 6: AutoResearchClaw — Autonomous Pivot/Refine Control
* **arXiv Reference:** arXiv:2605.20025
* **Core Hypothesis:** Self-healing hypothesis control loops with automated red-teaming falsification iteratively pivot and refine strategy branches prior to execution.
* **Mathematical Formulation:**
  $$\text{Branch}^* = \arg\max_{B \in \mathcal{B}} P(B) \cdot (1 - U(B)) \cdot \text{Confidence}(B)$$
* **Training Methodology:** Continuous red-teaming scenario synthesis and falsification testing.
* **Learning Algorithm:** Iterative hypothesis search with adversarial pivot loops.
* **Memory Architecture:** Research ledger logging all attempted hypotheses, pivots, and refinements.
* **Planning Architecture:** Active inference hypothesis generation and simulation pipeline.
* **Agent Architecture:** Red-team blue-team adversarial agent debate loops.
* **World Model Contribution:** Counterfactual stress-testing under synthesized extreme market conditions.
* **Self-Improvement Contribution:** Continuous self-correction of flawed strategy logic.
* **Failure Modes:** Infinte pivot loops under contradictory simulation feedback (mitigated by max iteration depth $k \le 3$).
* **Scalability Limits:** Bounded by simulation budget.
* **Computational Complexity:** $\mathcal{O}(B \cdot S)$ where $B$ is branches and $S$ is simulation steps.
* **Engineering Tradeoffs:** Simulation compute overhead vs. decision execution safety.
* **Financial Applicability:** Prevents strategy deployment in hidden tail-risk environments.
* **Production Readiness:** High. Core logic in `trading_bot/core/csc/controller.py` and `trading_bot/governance/evolution_gate.py`.

---

## 7. Paper 7: HASP — Prescriptive Guardrail Skill Verification
* **arXiv Reference:** arXiv:2605.17734
* **Core Hypothesis:** Programmatic invariant checks and prescriptive guardrails executed in isolated sandboxes enforce strict, non-negotiable safety vetoes.
* **Mathematical Formulation:**
  $$\text{Exec}(A) = \begin{cases} A, & \text{if } \bigwedge_{g \in G} g(A) = \text{PASS} \\ \text{VETO}, & \text{otherwise} \end{cases}$$
* **Training Methodology:** Pre-execution programmatic invariant analysis and static AST checking.
* **Learning Algorithm:** Deterministic rule evaluation over AST and execution parameters.
* **Memory Architecture:** Programmatic invariant store and audit log.
* **Planning Architecture:** Hard pre-emption of plans violating safety parameters.
* **Agent Architecture:** Non-negotiable safety sentinel with absolute veto power.
* **World Model Contribution:** Asserts physical and market boundaries on predicted states.
* **Self-Improvement Contribution:** Prevents self-modification from weakening safety constraints.
* **Failure Modes:** Overly restrictive invariants causing system paralysis (mitigated by explicit override protocols).
* **Scalability Limits:** $\mathcal{O}(|G|)$ linear in the number of guardrail predicates.
* **Computational Complexity:** $\mathcal{O}(1)$ runtime predicate checks.
* **Engineering Tradeoffs:** False positive trade rejections vs. zero capital blowups.
* **Financial Applicability:** Enforces hard portfolio drawdown, concentration, and leverage limits.
* **Production Readiness:** High. Implemented in `trading_bot/core/csc/router.py` and `trading_bot/core/immutable_shield.py`.

---

## 8. Paper 8: DeepWeb-Bench — Calibration Error (ECE) Evaluation Bounds
* **arXiv Reference:** arXiv:2605.21482
* **Core Hypothesis:** Quantifying Expected Calibration Error (ECE) and Brier scores ensures that agent decision confidence accurately reflects true empirical success probabilities.
* **Mathematical Formulation:**
  $$\text{ECE} = \sum_{m=1}^M \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$
  $$\text{Brier} = \frac{1}{N} \sum_{i=1}^N (f_i - o_i)^2$$
* **Training Methodology:** Post-hoc probability calibration (Platt scaling / isotonic regression).
* **Learning Algorithm:** Empirical binning calibration optimization.
* **Memory Architecture:** Calibration tracking history across execution decision outcomes.
* **Planning Architecture:** Rejects planning branches with high calibration uncertainty.
* **Agent Architecture:** Calibrates multi-agent debate voting weights according to historical ECE.
* **World Model Contribution:** Evaluates prediction calibration across volatile market regimes.
* **Self-Improvement Contribution:** Evolution gate metric threshold for strategy promotion ($\text{ECE} \le 0.05$).
* **Failure Modes:** Insufficient outcome sample size ($N < 100$) leading to inaccurate ECE estimation.
* **Scalability Limits:** $\mathcal{O}(N)$ over evaluation dataset size.
* **Computational Complexity:** $\mathcal{O}(N \log N)$ sorting for quantile binning.
* **Engineering Tradeoffs:** Calibration sample window length vs. responsiveness.
* **Financial Applicability:** Ensures position sizing scales reliably with model confidence.
* **Production Readiness:** High. Integrated into `trading_bot/governance/evolution_gate.py`.
