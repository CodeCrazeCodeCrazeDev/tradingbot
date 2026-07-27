# 02. Current State Assessment of AlphaAlgo Research

This document performs an evidence-based audit of AlphaAlgo's existing research pipeline. It evaluates AlphaAlgo's current methods against institutional-grade scientific discovery standards.

---

## 24-Stage Lifecycle Audit

### 1. Problem Discovery
*   **Current State:** Highly ad-hoc. Anomalies or strategies are identified individually or triggered via rule-based alerts in production.
*   **Evaluation:** Lacks structured scientific prioritizing or a unified backlog of research questions.

### 2. Research Prioritization
*   **Current State:** Existing `IdeaRegistry` implements a basic priority score:
    $$\text{Priority} = \frac{\text{Expected Sharpe} \times \text{Feasibility}}{\text{Cost}}$$
*   **Evaluation:** Simple but useful. However, it does not factor in portfolio capacity, correlation with existing active alphas, or strategic research theme alignment.

### 3. Literature Review
*   **Current State:** Legacy `LiteratureReviewBacklog` has hardcoded dictionary items verifying standard topics (e.g., EMA crossovers, order flow imbalance).
*   **Evaluation:** Extremely simplistic. No dynamic indexing of internal findings, academic papers, or structural failure studies.

### 4. Market Observation
*   **Current State:** Handled by individual components scanning or streaming market feeds directly without formalizing the regimes or microstructure indicators first.
*   **Evaluation:** Decoupled. Regime indicators exist in `RegimeAndMicrostructureAnalyzer` but are not saved as metadata tagged to datasets.

### 5. Data Ingestion & Acquisition
*   **Current State:** Relies on third-party integrations (e.g. MetaTrader 5, brokers) or synthetic generation scripts.
*   **Evaluation:** Basic caching exists, but there is no structured dataset registry managing historical files or split histories.

### 6. Data Quality Management
*   **Current State:** Restored `DataValidator` performs basic OHLC shape checks, NaN checks, and volume sanitization.
*   **Evaluation:** Missing formal schema contracts, automated point-in-time validation, and automated data quarantine.

### 7. Feature Engineering
*   **Current State:** legacy `FeatureFactory` computes standard features (log returns, ATR volatility, VWAP distance, Hurst exponent).
*   **Evaluation:** Features are hardcoded. There is no feature versioning, feature lineage graph, or modular register for sharing computed feature columns.

### 8. Hypothesis Generation
*   **Current State:** Handled by a basic `ResearchLab` producing simple `Hypothesis` dataclass objects.
*   **Evaluation:** Hypotheses are isolated structures. They do not track supporting/contradicting evidence dynamically, and are not linked to down-stream experiment nodes.

### 9. Experiment Design
*   **Current State:** Existing `ExperimentRegistry` hashes a Pandas DataFrame to lock reproducibility, storing parameters in a simple dataclass.
*   **Evaluation:** Missing immutable provenance hashes, environment fingerprinting (Python version, system resources), and runtime scheduler execution tracking.

### 10. Backtesting
*   **Current State:** legacy `InstitutionalBacktester` applies spreads, commissions, and slippage.
*   **Evaluation:** Robust transaction cost model, but lacks multi-broker compliance simulation, latency jitter testing, and execution-probabilistic limit order simulation.

### 11. Simulation
*   **Current State:** Simple `SimulatedPaperEnvironment` simulates api delays and spread slippage.
*   **Evaluation:** Good, but isolated. Does not support counterfactual order matching, trade crowd modeling, or liquidity impact simulations.

### 12. Benchmarking
*   **Current State:** Non-existent. AlphaAlgo does not verify that proposed models beat statistical or financial baselines (e.g. Buy & Hold, Simple Crossover) in a formalized test suite.
*   **Evaluation:** High risk of "discovering" trivial, sub-benchmark alpha.

### 13. Statistical Validation
*   **Current State:** Basic walk-forward analysis splits are implemented. Granger causality and Chow structural break tests are mapped as helpers.
*   **Evaluation:** Good, but walk-forward is un-purged. Lacks rigorous p-value deflation for multiple trials (DSR), leaving the system highly vulnerable to p-hacking.

### 14. Robustness Testing
*   **Current State:** No formal parameter sensitivity, bootstrap analysis, or regime-conditional stress testing.
*   **Evaluation:** Severe scientific weakness. Alphas can easily fall off cliffs if regime parameters shift slightly.

### 15. Risk Evaluation
*   **Current State:** Volatility circuit breakers exist inside the `StrategyEngine` and basic drawdown tracking in the `ProductionMonitor`.
*   **Evaluation:** Adequate operational safety, but misses ex-ante risk-budget decomposition and tail-risk stress tests (e.g., historical crash simulations).

### 16. Portfolio Research
*   **Current State:** legacy `PortfolioOptimizer` utilizes inverse-volatility scaling.
*   **Evaluation:** Elementary. No mean-variance optimization (Markowitz), Black-Litterman, Kelly Criterion with fractional scaling, or non-normal risk attribution.

### 17. Execution Research
*   **Current State:** Microstructure indicators exist (e.g. Order Book Imbalance, limit order execution probability).
*   **Evaluation:** Good mathematical foundations, but execution parameters are not backtested as separate features.

### 18. Model Evaluation
*   **Current State:** Looked at nominal Sharpe ratios and raw returns.
*   **Evaluation:** Severe lack of machine-learning-specific evaluation metrics (e.g., calibration curve Brier Score, feature attribution stability, model entropy).

### 19. Reproducibility
*   **Current State:** `ReproducibilityAssurer` provides standard random seed locking and simple DataFrame split hashing.
*   **Evaluation:** Weak. If system packages, Git versions, or code features change, the identical seed will generate different signals. Lacks comprehensive Provenance Hashing.

### 20. Experiment Tracking
*   **Current State:** Basic `ExperimentRegistry` memory database.
*   **Evaluation:** Missing persistent tracking, metadata tagging, and dependency graphing.

### 21. Research Governance
*   **Current State:** `PeerReviewBoard` runs a basic checks list (Sharpe > 4.5, Bars < 100, OOS degradation).
*   **Evaluation:** Rule-based and easily bypassed. Lacks audit trails, multi-signature approvals, and formal separation of researcher/reviewer roles.

### 22. Decision Logging
*   **Current State:** Event-bus `LogAction` structures.
*   **Evaluation:** Operational, but not tied to a centralized scientific `ResearchLedger` for tracking *why* strategies were promoted or retired.

### 23. Knowledge Management
*   **Current State:** `KnowledgeArchive` stores failed ideas in a basic Python dict.
*   **Evaluation:** High research debt. Search capability is limited to string matches and lacks semantic/relation-based retrieval.

### 24. Continuous Learning
*   **Current State:** `ProductionFeedbackLoop` triggers anomaly alerts and spawns post-mortem ideas.
*   **Evaluation:** Excellent loop direction, but lacks automatic model retrain triggers, walk-forward drift updates, and reinforcement-learning-safe evaluator gates.
