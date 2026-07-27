# Prioritized Implementation Roadmap
### Phased Implementation Strategy for Valued Gaps

This roadmap structures the execution of missing capabilities strictly based on institutional value priorities.

## Implementation Roadmap

### Phase 1: Foundation Governance & Security (Priority 0)
* **Goal:** Implement the sub-millisecond retrieval-based **Adaptive Control Policy Engine (ACPE)** inside the CSC and HMS, utilizing pre-distilled failure patterns.
* **Duration:** Current Milestone.
* **Deliverable:** `trading_bot/core/csc/acpe.py` integrated into the CSC observation pipeline.

### Phase 2: Statistical Correctness & Lineage (Priority 1)
* **Goal:** Expand validation checks for data lineage hashing and DSR multiple-testing corrections inside `trading_bot/research/research_os.py`.
* **Duration:** Immediate execution.
* **Deliverable:** Code refinements to guarantee strict parent ID DAG tracing and Granger causality score constraints.
