# Comprehensive Taxonomy of Hypothesis Creation Points (Institutional Audit 2026)

This document details every location across the AlphaAlgo codebase where hypotheses (whether explicitly typed as `ScientificHypothesis` / `Hypothesis` or implicitly framed as forecasts, beliefs, strategies, regime classifications, or policy rules) are originated.

---

## 1. Explicit Creation Points

These modules construct formal hypothesis objects with dedicated IDs, metadata, and lifecycle trackers:

| Module / Component File | Instantiating Method / Class | Hypothesis Representation | Purpose & Mechanism |
| :--- | :--- | :--- | :--- |
| `trading_bot/core_agent_system/scientific_reasoning/core.py` | `ScientificReasoningEngine.observe()` | `ScientificHypothesis` | Instantiates raw observation state $H_0$ upon sensory ingestion or statistical deviation. |
| `trading_bot/foundation_agents/curiosity_engine/hypothesis_generator.py` | `HypothesisGenerator.generate_from_anomaly()` | `ResearchHypothesis` | Generates structured causal hypotheses triggered by high variational surprise in sensory streams. |
| `trading_bot/alpha_research/hypothesis_extraction.py` | `HypothesisExtractionEngine.extract_from_research()` | `ExtractedHypothesis` | Parses academic literature (ArXiv / PDFs) into machine-testable alpha claims. |
| `trading_bot/core/csc/hypothesis.py` | `HypothesisGenerator.generate_competing_branches()` | `CompetingHypothesisBranch` | Creates rival execution branches (e.g. Trend vs. Mean-Reversion) for real-time decision synthesis. |
| `trading_bot/apex_fi/alpha_mining.py` | `GeneticAlphaSearch._generate_random_expression()` | `AlphaGenome` | Instantiates symbolic mathematical expressions as alpha hypothesis candidates. |
| `trading_bot/world_model/imagination.py` | `ImaginationEngine.simulate_scenarios()` | `ImaginedScenario` | Constructs counterfactual scenario hypotheses during multi-step lookahead planning. |
| `trading_bot/market_teacher/absolute_laws.py` | `AbsoluteLaws._create_draft_strategy()` | `DraftStrategyHypothesis` | Synthesizes candidate structural rules from market invariants. |
| `trading_bot/core/phce_d_engine.py` | `PHCEDAI._generate_hypothesis()` | `CorrectionHypothesis` | Generates fast parallel correction hypotheses to adjust tactical execution parameters. |

---

## 2. Implicit Creation Points

These components generate functional hypotheses embedded within state vectors, policy trees, or statistical models without explicitly calling a `Hypothesis` class:

| Subsystem Directory | Key File / Function | Implicit Hypothesis Type | Underlying Assumption / Falsifiable Claim |
| :--- | :--- | :--- | :--- |
| **Strategy Discovery** | `trading_bot/strategy_discovery/evolutionary_engine.py` | `StrategyGenome` | Claim: Specific feature combination yields positive risk-adjusted excess returns. |
| **Autonomous RL** | `trading_bot/ml/offline_rl/alphaalgo_autonomous_system.py` | Policy Q-Value State | Claim: Action $a$ in state $s$ maximizes discounted future reward $G_t$. |
| **World Model Reasoning** | `trading_bot/world_model/v2_training.py` | Causal Reasoning Traces | Claim: Action $A$ causes outcome $Y$ via mediator $M$ ($A \rightarrow M \rightarrow Y$). |
| **Market Regime Adapter** | `trading_bot/profit_maximizer/market_regime_adapter.py` | Regime Belief Vector | Claim: Current market state belongs to regime $R_k$ (e.g., High Volatility Expansion). |
| **Causal Induction** | `trading_bot/world_model/causal_model.py` | Directed Acyclic Graph (DAG) Edge | Claim: Causal edge $X \rightarrow Y$ exists with intervention effect $\mathbb{E}[Y \mid do(X)]$. |
| **Swarm Debate** | `trading_bot/agents/multi_agent_debate.py` | Agent Thesis Message | Claim: Market structure supports long/short entry with confidence score $c_i$. |
| **Option/Vol Modeling** | `trading_bot/analytics/options_surface.py` | Volatility Skew Fit | Claim: Implied volatility surface follows SVI parametrization under arbitrage bounds. |
| **Risk / Portfolio** | `trading_bot/risk/portfolio_optimizer.py` | Expected Return Vector $\boldsymbol{\mu}$ | Claim: Asset returns will align with Black-Litterman implied views over horizon $T$. |

---

## 3. Comprehensive Subsystem Creation Mapping

To fulfill the mandate of auditing every subsystem, below is the distribution of hypothesis creation across AlphaAlgo's functional layers:

1. **World Model**: Instantiates state forecasts, scenario trees, and $do(X)$ causal interventions (`trading_bot/world_model/`).
2. **Strategy & Alpha Discovery**: Instantiates symbolic genomes, genetic alpha expressions, and RL policy seeds (`trading_bot/strategy_discovery/`, `trading_bot/apex_fi/`).
3. **Research & Literature**: Instantiates extracted paper claims, LLM research proposals, and anomaly explanations (`trading_bot/alpha_research/`).
4. **Decision Layer (CSC)**: Instantiates rival execution hypotheses, logic folding trees, and trade ideas (`trading_bot/core/csc/`).
5. **Adversarial Reasoning**: Instantiates red-team attack strategies, skeptic counter-arguments, and risk veto theses (`trading_bot/agents/multi_agent_debate.py`).
6. **Self-Improvement & Meta-Learning**: Instantiates self-evolution code proposals, hyperparameter tuning seeds, and architectural mutations (`trading_bot/systems_ai/self_improvement.py`).
7. **Memory & Context**: Instantiates graph nodes for past market regimes and legacy failure explanations (`trading_bot/core/hms/`).
8. **Execution & Risk**: Instantiates slippage expectations, liquidity depletion models, and execution policy candidates (`trading_bot/execution/`, `trading_bot/risk/`).
