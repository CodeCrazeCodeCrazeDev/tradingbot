# PHASE 5 — Modification Rules & Implementation Roadmap

## 1. Modification Rules

### 1.1 Integrity Principles
- **Explainability First**: Every code modification must include a `reasoning` and `expected_impact` block in the proposal.
- **Testing Parity**: No logic change without a corresponding unit or integration test.
- **Rollback mandatory**: Every automated change must have a registered `rollback_plan` in the `ImprovementMemory`.

### 1.2 Boundary Enforcement
- **Level 0-5**: Autonomous if validation passes.
- **Level 6-7**: **MANDATORY** human review via `pending_approvals.json`.
- **Core System Lock**: Files in `core_agent_system/` and `governance/` are Level 7 and require the highest level of scrutiny.

## 2. Immediate Implementation Roadmap

### Task 1: Ground-Truth Re-Anchoring (Tier 0)
- **Objective**: Fix the "Delusion Loop" by forcing the `WorldModel` to re-synchronize with real tick data every 100 timesteps.
- **Affected**: `trading_bot/world_model/latent_dynamics.py` (Implementation of `ObservationReAnchorer` logic).

### Task 2: Unified Event Bus (Tier 1)
- **Objective**: Reduce coupling between agents by introducing a central `ZMQEventBus` for cross-layer communication.
- **Affected**: `trading_bot/core_agent_system/master_orchestrator.py`.

### Task 3: Symbolic Discovery Loop (Tier 2)
- **Objective**: Implement the conceptual `SymbolicResearcher` in the `FeatureImprovementLoop`.
- **Affected**: `trading_bot/recursive_improvement/loops/feature_loop.py`.

### Task 4: AI Sentinel Deployment (Tier 1)
- **Objective**: Deploy the `SentinelAgent` for logical drift detection in logs.
- **Affected**: `trading_bot/core_agent_system/agent_registry.py`.

---

**Summary**: The system has been mapped, understood, and reviewed. We are now ready to evolve AlphaAlgo from a research prototype into a production-grade autonomous intelligence.
