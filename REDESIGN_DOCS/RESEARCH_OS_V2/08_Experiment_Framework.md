# 08. Experiment and Execution Framework

The Research OS V2 manages the orchestration, scheduling, and execution of quantitative experiments under a strict, reproduce-first methodology.

---

## 1. Multi-Stage Experiment Lifecycle

Every experiment run must proceed through a state progression backed by the SQLite database:

```text
    [DRAFT]  --> Create hypothesis, declare falsifications, setup configuration.
       │
       ▼
   [RUNNING] --> Lock resources, set random seeds, compute features.
       │
       ▼
  [COMPLETED]--> Save generated model artifacts, backtest returns, and transaction logs.
       │
       ▼
  [VALIDATED]--> Auditor runs lookahead tests, baseline checks, and Deflated Sharpe.
       │
       ├──────────────────────────┐
       ▼ (Passes validation)      ▼ (Fails validation or leak found)
  [APPROVED]                  [REJECTED]
       │                          │
       ▼                          ▼
  [ARCHIVED]                  Add to Research Debt Backlog.
```

*   **Auditable Transitions:** Every state transition is recorded in the `ledger` table with a timestamp and the operator's ID.

---

## 2. Scheduling and Dependencies

The `ExperimentScheduler` schedules runs based on a topological sort of the experiment dependency DAG:

*   **Dependency Matching:** If Experiment B depends on the output of Experiment A, the scheduler ensures Experiment A achieves a state of `COMPLETED` or `VALIDATED` before executing Experiment B.
*   **Hyperparameter Sweep Support:** The scheduler supports automatic parameter extraction (e.g. grid sweeps or random sweeps), registering each parameter set as an independent child experiment node carrying its own `ProvenanceHash`.
*   **Resource Allocation:** Restricts concurrent running experiments based on a global thread/process limit to prevent out-of-memory errors during heavy machine learning training sessions.
