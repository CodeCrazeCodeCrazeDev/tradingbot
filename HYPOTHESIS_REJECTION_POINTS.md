# Comprehensive Taxonomy of Hypothesis Rejection Points (Institutional Audit 2026)

This document maps every point across the AlphaAlgo codebase where hypotheses, strategies, beliefs, or trade candidates are rejected, falsified, pruned, decayed, or retired.

---

## 1. Scientific & Bayesian Rejection Gates

| Subsystem File | Component / Class | Rejection Mechanism | Trigger Condition / Threshold |
| :--- | :--- | :--- | :--- |
| `trading_bot/core_agent_system/scientific_reasoning/core.py` | `ScientificReasoningEngine.retire_hypothesis()` | Moves hypothesis state directly to `HypothesisState.REJECTED`. | Posterior probability $P(\mathcal{H} \mid \mathcal{E}) < 0.20$. |
| `trading_bot/core_agent_system/scientific_reasoning/core.py` | `ScientificReasoningEngine.design_experiment()` | Triggers automatic falsification upon constraint violation. | Simulated drawdown $> 5\%$ or Out-of-Sample Sharpe $< 1.2$. |
| `trading_bot/core_agent_system/cds/epistemology_engine.py` | `EpistemologyEngine.analyze_hypothesis()` | Rejects hypothesis due to internal logical inconsistency or axiom breach. | Epistemic Integrity Score $< 0.50$. |

---

## 2. Adversarial & Swarm Rejection Gates

| Subsystem File | Component / Class | Rejection Mechanism | Trigger Condition / Threshold |
| :--- | :--- | :--- | :--- |
| `trading_bot/agents/multi_agent_debate.py` | `RiskVerifier.verify_risk()` | Non-negotiable risk veto forcing `NO_TRADE` or hypothesis rejection. | Max Drawdown breach, negative prices, or black swan volatility index breach ($VIX > 45$). |
| `trading_bot/agents/multi_agent_debate.py` | `VerificationSwarm.run_swarm()` | Vetoes hypothesis branch when skeptic agent identifies unmitigated tail-risk. | Verifier disagreement with skeptic confidence $> 0.85$. |
| `trading_bot/agents/multi_agent_debate.py` | `synthesize_decision()` | Filters out uncalibrated agent trade proposals. | Market context check failure (missing price, extreme spread, or invalid exposure). |

---

## 3. Alpha Decay, Health & Diagnostics Rejection Gates

| Subsystem File | Component / Class | Rejection Mechanism | Trigger Condition / Threshold |
| :--- | :--- | :--- | :--- |
| `trading_bot/alpha_research/alpha_death_clock.py` | `AlphaDeathClockManager` | Transitions active alpha to `DEPRECATED` or `REJECTED`. | Information coefficient decay $> 50\%$ or IC $p$-value $> 0.05$ over rolling window. |
| `trading_bot/alpha_research/strategy_diagnostics.py` | `StrategyDiagnostics` | Rejects candidate strategy for high probability of backtest overfitting. | Probability of Backtest Overfitting ($PBO > 0.30$) or Deflated Sharpe Ratio ($DSR < 0.95$). |
| `trading_bot/strategy_discovery/validation.py` | `StrategyValidationPipeline` | Rejects evolved genome candidate before research promotion. | Failure under regime-shift sensitivity or high transaction cost simulation. |

---

## 4. Search Space & Genetic Pruning

| Subsystem File | Component / Class | Rejection Mechanism | Trigger Condition / Threshold |
| :--- | :--- | :--- | :--- |
| `trading_bot/apex_fi/alpha_mining.py` | `GeneticAlphaSearch._prune_population()` | Eliminates bottom-performing expression trees from evolutionary pool. | Fitness score rank below top $20\%$ percentile or expression complexity penalty threshold breach. |
| `trading_bot/strategy_discovery/evolutionary_engine.py` | `EvolutionaryEngine._select_survivors()` | Prunes duplicate or overfitted strategy genomes. | Genome distance similarity score $> 0.90$ (diversity enforcement) or negative Sharpe. |

---

## 5. Evolution Gate & Safety Shields

| Subsystem File | Component / Class | Rejection Mechanism | Trigger Condition / Threshold |
| :--- | :--- | :--- | :--- |
| `trading_bot/governance/evolution_gate.py` | `EvolutionGate.validate_evolution()` | Rejects self-improvement code or model evolution proposals. | Latency regression $> 20\%$, Sharpe regression $> 0.0$, or ECE calibration regression $> 0.02$. |
| `trading_bot/core/immutable_shield.py` | `ImmutableShield.validate_action()` | Immediate hard veto halting action or strategy execution. | Breach of position limit, margin threshold, or unauthorized self-modification target. |
| `trading_bot/systems_ai/self_improvement.py` | `SelfImprovementLoop.validate_proposal()` | Sandboxing gate rejection of self-evolution proposals. | Proposal attempts modification of evaluator, risk limits, or promotion criteria. |
