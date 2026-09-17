# Comprehensive Taxonomy of Hypothesis Evaluation Points (Institutional Audit 2026)

This document maps every location across the AlphaAlgo codebase where hypotheses, strategies, beliefs, and predictions are evaluated, tested, simulated, debated, or statistically verified.

---

## 1. Core Scientific & Epistemic Evaluation

| Subsystem File | Evaluating Class / Method | Evaluation Mechanism | Metric / Output |
| :--- | :--- | :--- | :--- |
| `trading_bot/core_agent_system/scientific_reasoning/core.py` | `ScientificReasoningEngine.evaluate_results()` | Empirical statistical evaluation over historical & live runs. | Validation Score ($\in [0, 1]$), Effect Size |
| `trading_bot/core_agent_system/scientific_reasoning/core.py` | `ScientificReasoningEngine.bayesian_update()` | Governed Bayesian posterior update with Leni AI trust multiplier. | Posterior Probability $P(\mathcal{H} \mid \mathcal{E})$ |
| `trading_bot/core_agent_system/scientific_reasoning/core.py` | `ScientificReasoningEngine.calibrate_confidence()` | Expected Calibration Error (ECE) and credal interval contraction. | Credal Bounds $[p_{\text{lower}}, p_{\text{upper}}]$, Uncertainty Score |
| `trading_bot/core_agent_system/cds/epistemology_engine.py` | `EpistemologyEngine.analyze_hypothesis()` | Adversarial epistemic questioning against structural axioms. | Epistemic Integrity Score |

---

## 2. World Model & Counterfactual Evaluation

| Subsystem File | Evaluating Class / Method | Evaluation Mechanism | Metric / Output |
| :--- | :--- | :--- | :--- |
| `trading_bot/world_model/causal_model.py` | `CausalWorldModel.simulate_intervention()` | $do(X)$ causal interventional simulation to test mechanism stability. | Causal Stability Score, Counterfactual Surprise |
| `trading_bot/world_model/imagination.py` | `PlanEvaluator.evaluate_plan()` | Multi-step forward scenario rollout across state distributions. | Expected Lookahead Utility |
| `trading_bot/world_model/v2_training.py` | `WorldModelTrainer.evaluate_reasoning_trace()` | Validates internal reasoning trace consistency against ground truth. | Causal Chain Accuracy |

---

## 3. Adversarial Debate & Consensus Evaluation

| Subsystem File | Evaluating Class / Method | Evaluation Mechanism | Metric / Output |
| :--- | :--- | :--- | :--- |
| `trading_bot/agents/multi_agent_debate.py` | `VerificationSwarm.run_swarm()` | Peer-review swarm debate combining skeptic, optimist, and risk verifier. | Falsification Reports, Veto Decisions |
| `trading_bot/agents/multi_agent_debate.py` | `RiskVerifier.verify_risk()` | Deterministic non-negotiable risk boundary evaluation (drawdown, exposure). | Pass/Fail Boolean, Risk Score |
| `trading_bot/agents/multi_agent_debate.py` | `synthesize_decision()` | Bayesian weighted consensus over multi-agent debate claims. | Consensus Decision, Falsification Provenance |

---

## 4. Tactical & Decision Layer Evaluation

| Subsystem File | Evaluating Class / Method | Evaluation Mechanism | Metric / Output |
| :--- | :--- | :--- | :--- |
| `trading_bot/core/phce_d_engine.py` | `ParallelHypothesisCorrectionEngine.process()` | Synthesizes real-time market sensory evidence against active hypotheses. | Tactical Correction Factors |
| `trading_bot/core/csc/controller.py` | `CSC._verify_evidence_hard_constraint()` | Hard graph constraint check on evidence and boundary conditions. | Verification Mask |
| `trading_bot/core_agent_system/cds/verdict_engine.py` | `VerdictEngine.synthesize_verdict()` | Multi-attribute weighted logic folding across competing branches. | Final Selected Strategy / Action |

---

## 5. Statistical, Backtest, & Alpha Diagnostics

| Subsystem File | Evaluating Class / Method | Evaluation Mechanism | Metric / Output |
| :--- | :--- | :--- | :--- |
| `trading_bot/alpha_research/strategy_diagnostics.py` | `StrategyDiagnostics.audit()` | Multi-regime out-of-sample stress testing & parameter sensitivity. | Deflated Sharpe Ratio (DSR), PBO Score |
| `trading_bot/strategy_discovery/validation.py` | `StrategyValidationPipeline.run()` | Transaction cost, slippage, and regime-switch sensitivity evaluation. | Out-of-Sample Return / Max Drawdown |
| `trading_bot/alpha_research/alpha_death_clock.py` | `AlphaDeathClockManager.evaluate_decay()` | Half-life and information coefficient decay tracking over time. | Alpha Decay Rate, Half-Life Index |

---

## 6. Governance & Evolution Safety Evaluation

| Subsystem File | Evaluating Class / Method | Evaluation Mechanism | Metric / Output |
| :--- | :--- | :--- | :--- |
| `trading_bot/governance/evolution_gate.py` | `EvolutionGate.validate_evolution()` | Multi-attribute regression test comparing candidates against champions. | Evolution Gate Pass / Reject Decision |
| `trading_bot/core/immutable_shield.py` | `ImmutableShield.validate_action()` | Hard non-bypassable architectural safety and risk checks. | Unconditional Veto / Permit |
