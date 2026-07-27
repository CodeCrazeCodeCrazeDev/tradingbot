# 06. Research Operating System Core Specifications

This document defines the core runtime structure, agent roles, and state progression model of the redesigned AlphaAlgo Research Operating System (Research OS V2).

---

## 1. Organization Structure and Agent Roles

The Research OS V2 models a virtual research institute with distinct, machine-executable roles:

```text
               +--------------------------------------+
               |          Research Director           |
               | (Theme Priority, Capacity Allocator) |
               +-------------------+------------------+
                                   |
            +----------------------+----------------------+
            |                                             |
            ▼                                             ▼
+-----------------------+                     +-----------------------+
|  Quantitative Scholar |                     |  Independent Auditor  |
|  (Hypothesis Creator, |                     |  (Leakage Detector,   |
|  Backtest Architect)  |                     |   DSR Statistical QC) |
+-----------------------+                     +-----------------------+
```

1.  **Research Director (Orchestrator):**
    *   Defines the thematic focus (e.g., Microstructure, Macro).
    *   Coordinates the execution schedule of active experiment batches.
    *   Manages budget priorities and the research debt backlog.
2.  **Quantitative Scholar (Hypothesis Proposer & Builder):**
    *   Formulates economically grounded claims (`HypothesisObject`).
    *   Creates derivative features and specifies parameter bounds.
    *   Constructs the target strategy models.
3.  **Independent Auditor (Statistical Validator):**
    *   Audits data quality and executes leakage-detection guards.
    *   Computes multiple testing correction (Deflated Sharpe Ratio).
    *   Independently executes backtests against baseline models.

---

## 2. The Research Ledger (Append-Only Audit DB)

All organizational actions, experiment runs, and governance decisions are written to the SQLite database `research.db` in the table `ledger`.

*   **Immutable Design:** The ledger table does not support `UPDATE` or `DELETE` commands.
*   **Hash Chain:** Every ledger entry includes a reference to the preceding record's SHA-256 hash, creating a tamper-evident audit trail of the research process.

### Schema Structure (SQLite)

```sql
CREATE TABLE IF NOT EXISTS ledger (
    entry_id TEXT PRIMARY KEY,
    previous_hash TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    entity_type TEXT NOT NULL, -- e.g., HYPOTHESIS, EXPERIMENT, APPROVAL
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,      -- e.g., PROPOSED, RUNNING, COMPLETED, APPROVED
    operator_id TEXT NOT NULL, -- e.g., scholar_agent_1, auditor_agent_1
    metrics TEXT,              -- JSON string of metrics
    record_hash TEXT NOT NULL
);
```

---

## 3. The Scientific Review Pipeline

For any strategy to be promoted, it must traverse a strict, linear state progression:

```text
[Draft] ---> [Running] ---> [Completed] ---> [Validated] ---> [Approved] ---> [Archived]
  |                                                |             |
  +------------------ (Leakage Found) -------------+             |
  |                                                              |
  +------------------ (Failed peer review) ----------------------+
```

1.  **Draft:** The hypothesis is proposed, falsifications declared, and code setup created.
2.  **Running:** The experiment is scheduled and currently executing backtests.
3.  **Completed:** Metrics are computed, and raw results generated.
4.  **Validated:** The Independent Auditor confirms lookahead-bias safety, calculates the Deflated Sharpe Ratio, and benchmarks against multiple baseline models. If validation fails, the status moves to `Rejected`.
5.  **Approved:** The Independent Review Board completes the governance checklist, approves the provenance, and writes the deployment-ready strategy parameters to the `StrategyRegistry`.
6.  **Archived:** Historically archived runs or retired production strategies.
