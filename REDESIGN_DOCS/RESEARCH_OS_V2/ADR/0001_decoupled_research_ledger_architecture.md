# ADR 0001: Decoupled Research Ledger and Producer-Consumer Separation

## Context and Problem

In legacy quant trading platforms, research components (like backtesters, feature generators, and model training loops) are often highly coupled with live execution components (like order execution, account risk management, and market data ingestion). This tight coupling introduces several critical architectural liabilities:

1.  **Shared State Corruption:** A crash or memory leak in an experimental ML model or heavy cross-validation loop can bring down the active trading thread.
2.  **Order Execution Contamination:** Research loops that can directly execute trades bypass compliance checks and risk gates, risking catastrophic out-of-control automated trading.
3.  **Governance Auditing Difficulties:** It is extremely difficult to audit *why* a particular model parameter is running in production when the promotion path consists of an engineer manually copying files or overwriting local database models.

We need a clean, institutional-grade design that decouples strategy discovery and scientific validation from operational execution, preserving the "One Brain" principle of the Cognitive System Controller (CSC).

## Proposed Solution

We enforce a strict **Producer-Consumer Separation** pattern mediated by a durable, append-only, transaction-safe **Research Ledger** implemented via an SQLite database (`research.db`).

```text
+-----------------------+              +-----------------------+
|  Research OS (V2)     |              |  One Brain / CSC      |
|  (The PRODUCER)       |              |  (The CONSUMER)       |
|                       |              |                       |
| Proposes Hypotheses,  |              | Reads Approved        |
| Computes Features,    | Writes To    | Strategy Params,      |
| Runs Backtests,       +------------->+ Coordinates Portfolio |
| Performs Statistical  |              | Sizing, and Safely   |
| Validation & Audits.  |              | Executes Orders.      |
+-----------------------+              +-----------------------+
```

1.  **Research OS V2 as a Pure Producer:** The research system executes experiments, hashes datasets, calculates features, evaluates deflated Sharpe ratios, and processes peer reviews in its own sandbox environment. It has **no access** to active order managers or real-time trading interfaces.
2.  **The Research Ledger (SQLite):** The ledger serves as the authoritative, tamper-evident boundary between research and execution. All validated hypotheses, feature lineages, model weights references, and final approved strategy configurations are durably stored here.
3.  **One Brain / CSC as a Pure Consumer:** The Cognitive System Controller queries the SQL registries read-only to fetch active, approved strategies. It loads the validated parameter configurations and executes trade signals within its strict compliance and risk frameworks.

## Consequences

### Positive Consequences
*   **Operational Safety:** An experimental research thread can crash, leak memory, or run infinite optimization loops without affecting live execution stability.
*   **Tamper-Evident Audit Trails:** Every active strategy parameter is traceable to a specific, immutable row in the `StrategyRegistry` linked to its originating `ProvenanceHash` and `StatisticalValidationReport`.
*   **Clean Architectural Scaling:** Research search loops can scale horizontally across multiple servers or worker processes, writing results to a centralized `research.db` without affecting the active trading environment.

### Negative Consequences
*   **Data Synchronization:** Real-time production feedback requires passing structured events back to the Research OS through decoupled alerts rather than direct function calls.
