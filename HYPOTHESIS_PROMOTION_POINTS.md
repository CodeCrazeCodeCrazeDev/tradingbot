# Comprehensive Taxonomy of Hypothesis Promotion Points (Institutional Audit 2026)

This document maps every gate, transition, and milestone where a hypothesis, strategy, alpha candidate, or self-improvement proposal is promoted, elevated in confidence, integrated into knowledge, or authorized for deployment.

---

## 1. Scientific Promotion Hierarchy (SRE Promotion Levels)

The `ScientificReasoningEngine` (`trading_bot/core_agent_system/scientific_reasoning/core.py`) defines a formal 6-level promotion hierarchy:

```
LEVEL_0: Raw Observation
   │
   ▼  (SRE Step 4: Competing Branch Generation)
LEVEL_1: Candidate Hypothesis
   │
   ▼  (SRE Step 11 & 12: Empirical Validation & Bayesian Posterior P(H|E) > 0.70)
LEVEL_2: Validated Hypothesis
   │
   ▼  (SRE Step 14: Knowledge Integration & P(H|E) > 0.85)
LEVEL_3: Research Strategy
   │
   ▼  (SRE Step 16: Policy Improvement & Evolution Gate Validation)
LEVEL_4: Production Strategy
   │
   ▼  (SRE Step 18: Institutionalization & Cross-Regime Validation > 1 Year Equiv)
LEVEL_5: Institutional Knowledge
```

---

## 2. Subsystem Promotion Gates Matrix

| Subsystem File | Component / Class | Target State / Level | Promotion Criteria & Gates |
| :--- | :--- | :--- | :--- |
| `trading_bot/core_agent_system/scientific_reasoning/core.py` | `ScientificReasoningEngine.integrate_knowledge()` | `PromotionLevel.LEVEL_3` (Research) | Posterior probability $P(\mathcal{H} \mid \mathcal{E}) > 0.85$ and $ECE < 0.05$. |
| `trading_bot/core_agent_system/scientific_reasoning/core.py` | `ScientificReasoningEngine.retire_hypothesis()` | `HypothesisState.INSTITUTIONALIZED` (Level 5) | Long-term posterior stability $P(\mathcal{H} \mid \mathcal{E}) \ge 0.80$ with zero critical falsifications. |
| `trading_bot/core/hms/memory.py` | `HierarchicalMemorySystem.store_ledger_entry()` | Graph Knowledge Base Persistence | Research ledger snapshot created with composite confidence score and immutable evidence hashes. |
| `trading_bot/alpha_research/hypothesis_extraction.py` | `HypothesisExtractionEngine` | Candidate Alpha Portfolio | Extracted paper hypothesis passes out-of-sample backtest and DSR $> 1.0$. |
| `trading_bot/strategy_discovery/validation.py` | `StrategyValidationPipeline` | Research Alpha Pool | Genome passes regime-switch robustness, transaction cost sensitivity, and $PBO < 0.20$. |
| `trading_bot/governance/evolution_gate.py` | `EvolutionGate.validate_evolution()` | Production Deployment (`LEVEL_4`) | Out-of-sample Sharpe improvement $> 0.0$, latency regression $\le 20\%$, and calibration error change $\le 0.02$. |
| `trading_bot/core/csc/controller.py` | `CognitiveSystemController.synthesize_decision()` | Active Live Signal Execution | Swarm debate consensus reached, $do(X)$ causal stability verified, and hard risk shield cleared. |
| `trading_bot/systems_ai/self_improvement.py` | `SelfImprovementLoop.promote_evolution()` | Self-Evolution Code Commit | Evolution proposal passes automated sandboxed regression suite and human governance protocol (if high-weight). |

---

## 3. Epistemic Knowledge Conversion (Data to Institutional Policy)

1. **Sensory & Market Ingestion** $\rightarrow$ Raw Anomaly Observations ($H_0$).
2. **Causal & Counterfactual Testing** $\rightarrow$ Validated Causal Graph Edges in World Model.
3. **Adversarial Debate & Backtesting** $\rightarrow$ Calibrated Research Ledger Entries in HMS.
4. **Governance & Evolution Gate Approval** $\rightarrow$ Deployed Alpha Execution Policies in CSC.
5. **Multi-Regime Live Monitoring** $\rightarrow$ Immutable Institutional Knowledge Base.
