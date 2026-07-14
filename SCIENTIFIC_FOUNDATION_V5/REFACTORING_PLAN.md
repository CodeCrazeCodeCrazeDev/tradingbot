# Refactoring Plan: AlphaAlgo UCA V5 Implementation

## 1. Dependency Graph
- **Tier 0 (Foundational Reliability)**: `LOGACT_BACKBONE` -> `VOTER_REGISTRY` -> `IMMUTABLE_SHIELD`.
- **Tier 1 (Knowledge Substrate)**: `SAGE_GRAPH` -> `QKG_CONTEXT` -> `HMS_V5`.
- **Tier 2 (Strategic Routing)**: `META_HARNESS` -> `SKILL_ROUTER` -> `HASP_EXECUTOR`.
- **Tier 3 (Cognitive Loop)**: `DISCOLOOP` -> `VFE_OBJECTIVE` -> `CSC_CONTROLLER`.
- **Tier 4 (Evolutionary Safety)**: `CL_BENCH_GAIN` -> `FORMAL_INVARIANT_GATE` -> `EVOLUTION_GATE`.

## 2. Migration Roadmap

### Phase 5a: Reliability & Knowledge (LogAct / HMS / SAGE)
- **Target**: `trading_bot/core/hms/`
- **Actions**:
    - Refactor `unified_event_bus.py` into LogAct Shared-Log Backbone (arXiv:2604.07988).
    - Implement SAGE Dynamic Graph-Memory in `memory.py` (arXiv:2605.12061).
    - Add context-dependent validity (QKG) to `models.py` (arXiv:2604.23972).
- **Risk**: High. Data migration from old research ledger to new graph-memory.
- **Rollback**: Keep old `.json` ledger files as read-only fallbacks.

### Phase 5b: Intelligence & Routing (CSC / HASP / Meta-Harness)
- **Target**: `trading_bot/core/csc/`
- **Actions**:
    - Implement Meta-Harness optimized `SkillRouter` (arXiv:2603.28052).
    - Upgrade `CognitiveSystemController` with DiscoLoop (arXiv:2607.00341) and VFE (Minimizing Surprise).
    - Deploy HASP executable guardrails (arXiv:2605.17734).
- **Risk**: Critical. This is the heart of the system.
- **Rollback**: Maintain `CognitiveSystemController_V4` as a fallback delegator.

### Phase 5c: Evolution & Validation (HyEvo / CL-Bench)
- **Target**: `trading_bot/governance/` and `tests/`
- **Actions**:
    - Implement HyEvo multi-island evolution with Formal Invariant Checking (arXiv:2603.19639).
    - Update training scripts to use `EKSFT` selective masking.
- **Risk**: Medium. May slow down learning rates initially.

## 3. Risk Analysis & Mitigation
- **Complexity Explosion**: mitigate by strictly adhering to "One Brain" and avoiding multiple orchestrators.
- **Latency Increase**: mitigate by moving `Folding` (HIPIF) and `S2L` (LoRA) to background processes or efficient inference kernels.
- **Inference Hardware**: S2L requires multi-LoRA support. Fallback to high-tier prompts if LoRA server is unavailable.

## 4. Benchmark & Validation Plan
- **Primary Metric**: Success rate on `DeepWeb-Bench` (Calibration & Derivation).
- **Secondary Metric**: Latency-per-decision (Institutional SLA < 500ms).
- **Validation**:
    - Unit tests for every new algorithm in `tests/core/`.
    - Integrated architecture verification in `tests/verification/test_uca_v5.py`.
    - "Gain Metric" analysis (CL-Bench) to ensure genuine online learning.

## 5. Rollback Strategy
- All refactored files will be new versions (`controller_v5.py`) or use feature flags.
- `master_orchestrator.py` will have a `V5_ENABLED` flag to toggle the new pipeline.
