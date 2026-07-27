# 04. Missing Capability Inventory and Redesign Justification

This document catalogs the critical missing capabilities in AlphaAlgo, explains *why* elite quantitative institutions implement them, and justifies their inclusion in the redesigned Research Operating System (Research OS V2).

---

## 1. Durable SQLite Persistence (vs. In-Memory Dictionaries)
*   **Why institutions perform it:** Financial research processes run continuously for years. Storing research findings, validation metrics, and experiment logs in memory or fragile JSON files leads to catastrophic state loss during server failures, code crashes, or deployment updates. A relational database guarantees ACID consistency, concurrent reading, and quick indexed queries across millions of backtests.
*   **Problem solved:** Risk of unrecorded discoveries, duplicate effort due to lost experiment histories, and inability to run multi-process parallel search loops without database locking.
*   **Expected Impact:** Extreme operational resilience and scalable research metadata.
*   **Implementation Complexity:** Medium.
*   **Priority:** **CRITICAL**. Should be part of AlphaAlgo's permanent Research OS.

## 2. Hypothesis-Driven Scientific Tracking (`HypothesisRegistry`)
*   **Why institutions perform it:** Without a hypothesis registry, a research team degrades into ad-hoc "data-mining"—running random backtests until they find a line that curves upward. This leads to severe overfitting. Starting with a theoretical hypothesis (grounded in economics, market microstructure, or behavioral friction) and declaring its falsification boundaries upfront keeps research rigorous.
*   **Problem solved:** Data-dredging, unscientific strategy discovery, and lack of accountability in alpha generation.
*   **Expected Impact:** Eliminates the discovery of trivial or spurious strategies.
*   **Implementation Complexity:** Low-Medium.
*   **Priority:** **HIGH**. Should be part of AlphaAlgo's permanent Research OS.

## 3. NetworkX-Backed Lineage Graphs (Feature and Dataset Lineage)
*   **Why institutions perform it:** If a feature's code changes, or a raw dataset is updated with better adjustments (such as splits or dividend corrections), every model and backtest built on top of that feature becomes invalid or stale. A Directed Acyclic Graph (DAG) mathematically maps these dependencies. This allows researchers to perform impact analysis, trace circular flows, and automatically trigger downstream retrains.
*   **Problem solved:** Stale features, corrupted model training, lack of auditability, and silent errors in feature preparation.
*   **Expected Impact:** Perfect traceability from raw tick to live signal.
*   **Implementation Complexity:** Medium.
*   **Priority:** **HIGH**. Should be part of AlphaAlgo's permanent Research OS.

## 4. Multi-Baseline Benchmarking Repository
*   **Why institutions perform it:** Finding a strategy that makes money is easy; finding a strategy that outperforms simple, low-cost alternatives (like Equal Weight or simple EMA crossovers) after costs is hard. Over 90% of proposed alphas are actually just leveraged beta or delayed momentum. Testing new strategies against a comprehensive suite of 10+ standard statistical, financial, and ML baselines is the only way to prove a model has genuine, independent alpha.
*   **Problem solved:** Over-complexity bias (proposing complex neural networks where a simple linear regression or moving average would outperform).
*   **Expected Impact:** Protects against capital misallocation and reduces portfolio transaction costs.
*   **Implementation Complexity:** Medium.
*   **Priority:** **HIGH**. Should be part of AlphaAlgo's permanent Research OS.

## 5. Statistical Overfitting Defense (Deflated Sharpe Ratio)
*   **Why institutions perform it:** Standard Sharpe Ratio calculations assume that the strategy was designed in a vacuum. In reality, if a researcher runs 500 experiments and selects the best one, its nominal Sharpe is heavily inflated. The Deflated Sharpe Ratio (DSR) penalizes the performance metric based on the number of trials and statistical characteristics (skewness, kurtosis, sample size).
*   **Problem solved:** Post-selection bias, backtest overfitting, and rapid out-of-sample degradation.
*   **Expected Impact:** High correlation between backtested Sharpe and live realized Sharpe.
*   **Implementation Complexity:** Medium.
*   **Priority:** **CRITICAL**. Should be part of AlphaAlgo's permanent Research OS.

## 6. Immutable Provenance Fingerprinting
*   **Why institutions perform it:** Science requires replication. If a researcher claims a Sharpe of 2.5, another researcher must be able to reproduce that exact number to the last digit. An immutable hash representing all inputs (code, config, data, seeds, environments) guarantees that the experiment is lock-reproducible.
*   **Problem solved:** The "reproducibility crisis" in quant research, where backtests cannot be reproduced on local developer environments or live servers.
*   **Expected Impact:** Eliminates human error and differences between local environments and production systems.
*   **Implementation Complexity:** Low-Medium.
*   **Priority:** **HIGH**. Should be part of AlphaAlgo's permanent Research OS.

## 7. Fail-Closed Leakage Guard (Data Integrity)
*   **Why institutions perform it:** The most common backtest error is "leakage"—accidentally shift-matching a feature with future prices (lookahead bias) or training on test data. Even a tiny leak will produce a beautiful, fake backtest. If lookahead bias is found, the system should instantly fail-closed, reject the run, and record the leakage in the debt log.
*   **Problem solved:** Invisible lookahead leakage causing catastrophic live losses.
*   **Expected Impact:** Guarantees absolute safety prior to allocating any capital.
*   **Implementation Complexity:** Medium.
*   **Priority:** **CRITICAL**. Should be part of AlphaAlgo's permanent Research OS.
