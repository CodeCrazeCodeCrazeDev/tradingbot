# 05. Target Architecture Design: Producer-Consumer Separation

The redesigned AlphaAlgo Research Operating System (Research OS V2) enforces a strict **Producer-Consumer Separation** pattern.

Under this design, Research OS is a decoupled **producer of validated knowledge and immutable strategies**. It writes structured, approved artifacts to a secure `ResearchLedger` (SQLite-backed). The Cognitive System Controller (CSC)—representing the "One Brain"—is a pure **consumer** of these approved artifacts.

This prevents research from executing trades directly or interfering with live decision state machines, ensuring architectural separation of concerns.

---

## 1. System Architectural Diagram (ASCII Flow)

```text
       +--------------------------------------------------------------+
       |                  RESEARCH OPERATING SYSTEM (V2)             |
       |                                                              |
       |  +--------------------+             +---------------------+  |
       |  | Hypothesis Registry|             |  Data/Feature DAG   |  |
       |  +---------+----------+             +----------+----------+  |
       |            |                                   |             |
       |            +-----------------+-----------------+             |
       |                              |                               |
       |                              ▼                               |
       |                    +-------------------+                     |
       |                    |  Experiment Loop  |                     |
       |                    +---------+---------+                     |
       |                              |                               |
       |                              ▼                               |
       |                    +-------------------+                     |
       |                    | Statistical Gate  |                     |
       |                    |    (DSR, Purge)   |                     |
       |                    +---------+---------+                     |
       |                              |                               |
       |                              ▼                               |
       |                    +-------------------+                     |
       |                    |  Independent Peer |                     |
       |                    |    Review Board   |                     |
       |                    +---------+---------+                     |
       +------------------------------|-------------------------------+
                                      |
============================== PRODUCER / CONSUMER BOUNDARY ====================
                                      | Writes Approved Artifacts
                                      ▼
                      +-------------------------------+
                      | RESEARCH LEDGER & REGISTRIES  |  <--- SQLite (research.db)
                      |  (Immutable Database Store)   |
                      +---------------+---------------+
                                      |
                                      | Read-Only Queries
                                      ▼
       +--------------------------------------------------------------+
       |             COGNITIVE SYSTEM CONTROLLER (CSC) / "ONE BRAIN"   |
       |                                                              |
       |  +--------------------+             +---------------------+  |
       |  |  Component Registry|             |   Decision Pipeline |  |
       |  +----------+---------+             +----------+----------+  |
       |             |                                  |             |
       |             +-----------------+----------------+             |
       |                               |                              |
       |                               ▼                              |
       |                      +-----------------+                     |
       |                      | Execution Model |                     |
       |                      +-----------------+                     |
       +--------------------------------------------------------------+
```

## 2. Integration with the One Brain / CSC

1.  **Strict Separation:** The Research OS has no knowledge of active order queues, trade accounts, or market execution states. It only reads raw historical and live market streams, generates hypotheses, runs experiments, and exports validated strategy parameters to the database.
2.  **The Registry Singleton Pattern:** The `ResearchOSV2` orchestrator is registered as a singleton with the platform's `UnifiedComponentRegistry` under component type `'research_operating_system'`.
3.  **Active Query Mode:** When the Cognitive System Controller (CSC) boots or plans a re-allocation of capital, it requests the approved strategy parameters from the `ResearchOSV2` database using standard read-only queries on the `ResearchLedger`.
4.  **No Direct Promotion:** A researcher cannot push a file directly to the active live traders. The strategy must be fully registered in the `StrategyRegistry`, have its `ProvenanceHash` recorded in the `ResearchLedger`, and receive a status of `APPROVED` from the scientific board before it becomes visible to the CSC.
5.  **Fail-Closed Feedback Loop:** If the CSC detects that a running strategy's live performance deviates significantly from its backtested parameters (monitored via drift indicators), it triggers a production feedback alert. The Research OS captures this alert, automatically flags the strategy in the registry as `Retired` or `UnderReview`, and updates the `Research Debt Tracker` with a post-mortem project.
