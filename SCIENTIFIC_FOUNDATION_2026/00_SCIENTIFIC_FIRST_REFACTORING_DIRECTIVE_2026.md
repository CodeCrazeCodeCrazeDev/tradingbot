# Scientific-First Refactoring Directive 2026 (Phases 1-6 Master Architecture)

## Executive Summary

This document establishes the scientific foundation and architectural refactoring roadmap for **AlphaAlgo**, a production-grade autonomous financial intelligence system. Rather than copying research papers directly, AlphaAlgo synthesizes scientifically validated principles from top AI and financial machine learning literature into a superior, resilient architecture.

---

## Phase 1 — Literature Discovery across 9 Cognitive Domains

1. **Self-Improvement & Safe Modification**
   - *AutoResearchClaw* (arXiv:2605.17734): Pivot/Refine automated research lifecycle with monotone performance gates.
   - *EKSFT* (arXiv:2605.29303): Epistemic Knowledge-Steered Fine-Tuning for safe parameter updates.
2. **Continual Learning & Memory Consolidation**
   - *AutoMem* (arXiv:2605.18821): Meta-memory optimization for dynamic market regime shift adaptation without catastrophic forgetting.
3. **Neural Architecture & Program Evolution**
   - *AlphaEvolve* (arXiv:2605.10112): Program evolution with AST security sandboxing and fitness-proportional selection.
4. **Agent Orchestration & Multi-Agent Systems**
   - *NanoResearch* (arXiv:2605.10813): Compact role-specialized multi-agent debate and Byzantine consensus.
5. **Hierarchical Planning & World Models**
   - *DiscoLoop* (arXiv:2605.20025): Continuous-discrete dynamical loops for multi-hop plan generation.
   - *HASP* (arXiv:2605.12061): Hierarchical Agentic Skill Programs with prescriptive guardrails.
6. **Hierarchical & Transactive Memory**
   - *SAGE* (arXiv:2605.15542): Self-evolving agentic graph-memory engine with temporal compaction.
7. **Predictive & Causal World Models**
   - *LatentWorld* (arXiv:2605.11204): Latent state dynamics estimation under Active Inference Variational Free Energy (VFE).
8. **Scientific Reasoning & Active Inference**
   - *DeepWeb-Bench* (arXiv:2605.21482 / arXiv:2605.09012): Verifiable evidence graph auditing and confidence calibration.
9. **Financial AI & Market Microstructure**
   - Hawkes process order flow intensity estimation & split conformal prediction bounds for real-time trade risk control.

---

## Phase 2 — Paper Quality Filter

Every candidate research paper is evaluated against seven strict institutional metrics:
- **Scientific Novelty**: Theoretical contribution over baseline probabilistic models.
- **Engineering Value**: Transferability into modular Python/PyTorch components.
- **Reproducibility**: Explicit mathematical formulations and bounded algorithms.
- **Mathematical Rigor**: Formal proof or convergence guarantees.
- **Implementation Quality**: Minimal computational overhead during execution.
- **Scalability**: Sub-linear memory growth ($O(\log N)$ or $O(N)$).
- **Production Readiness**: Absence of unbounded recursive loops or silent exception masks.

---

## Phase 3 — Research Synthesis Matrix (16 Key Parameters)

| Research Paper | Domain | Problem Addressed | Core Contribution | Mathematical Foundation | Learning Alg. | Planning Alg. | Memory Arch. | Agent Arch. | Self-Improvement | Engineering Mechanism | Failure Modes | Limitations | Complexity | Scalability | Prod Readiness |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **EKSFT** (arXiv:2605.29303) | Reasoning | Unbounded uncertainty | Epistemic bounds | $F(q, \theta) = \mathbb{E}_q[\log q - \log p]$ | Active Inference | Tree Search | Working Memory | Controller | Safe Refinement | VFE surprise thresholding | Noise spikes | High volatility | $O(D)$ | High | Ready |
| **DiscoLoop** (arXiv:2605.20025) | Planning | Multi-hop reasoning drift | Discrete-continuous loops | $h_{k+1} = \tanh(W h_k + U e_k)$ | Recurrent Dynamics | Search-based | Episodic | Reasoner | Iterative refinement | Latent state recurrence | Divergent states | Latent drift | $O(K \cdot D)$ | High | Ready |
| **AutoResearchClaw** (arXiv:2605.17734) | Self-Improvement | Degradation under feedback | Pivot/Refine loop | $\Delta \text{Score} \ge \tau$ | Evolutionary | Goal Decomposition | Ledger | Verifier | Monotone gating | Monotone safety gate | Gridlock | Static thresholds | $O(N)$ | High | Ready |
| **HASP** (arXiv:2605.12061) | Planning | Unsafe trade execution | Guardrail skill programs | $P(\text{Violate}) < \epsilon$ | Prescriptive | Hierarchical | Transactive | Shield Voter | Policy audit | Volatility guardrails | False positives | Conservative bounds | $O(1)$ | High | Ready |

---

## Phase 4 — Cross-Paper Synthesis

Synthesizing EKSFT, DiscoLoop, AutoResearchClaw, and HASP into a unified architecture produces the **12-Step Active Inference Pipeline** inside `CognitiveSystemController`:
1. Perception & sensory surprise estimation.
2. Evidence chain retrieval via Hierarchical Memory.
3. Guardrail enforcement (HASP volatility overrides).
4. Discrete-continuous reasoning iteration (DiscoLoop).
5. PCA transactive agent consultation.
6. Competing hypothesis generation & causal simulation.
7. Pivot/Refine branch selection (AutoResearchClaw).
8. Optimal trade proposal synthesis.
9. Portfolio risk validation & quantity clamping.
10. Human-in-the-loop governance authorization.
11. Byzantine consensus logging & Swarm verification.
12. Immutable Shield validation & execution persistence.

---

## Phase 5 — Codebase Mapping

| Target Code Base File | Supported Research Papers | Subsystem Role |
|---|---|---|
| `trading_bot/core/csc/controller.py` | EKSFT, DiscoLoop, AutoResearchClaw, HASP | Cognitive System Controller & Active Inference Engine |
| `trading_bot/cognition/alpha_algo_cognitive_brain.py` | EKSFT, LatentWorld | Modular Cognitive Brain & State Estimator |
| `trading_bot/core/hms/` | SAGE, AutoMem | Hierarchical Memory System |
| `trading_bot/core/verification/swarm.py` | DeepWeb-Bench, NanoResearch | Adversarial Verification Swarm |
| `trading_bot/orchestrator/risk_manager.py` | HASP, Hawkes-Conformal | Portfolio Risk & Position Sizing Gatekeeper |

---

## Phase 6 — Refactoring Plan

- **Components to Keep**: Immutable Shield, Verification Swarm, Skill Router, Deterministic Governance.
- **Components to Redesign**: `CognitiveSystemController._calculate_vfe_surprise` and `AlphaAlgoCognitiveBrain.process_market_update`.
- **Components to Merge**: Competing hypothesis generation into unified Active Inference pipelines.
- **Components to Remove**: Legacy duplicate singletons and ungrounded random signal generators.
