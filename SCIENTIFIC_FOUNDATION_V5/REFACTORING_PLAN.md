# Refactoring Plan: AlphaAlgo UCA V5 Implementation

## 1. Dependency Graph
- **Tier 0 (Foundation)**: `HASP_HARNESS` -> `SKILL_ROUTER` -> `CSC_CONTROLLER`.
- **Tier 1 (Memory)**: `SAGE_MEMORY` -> `AUTOMEM_OPTIMIZER` -> `HMS_SYSTEM`.
- **Tier 2 (Reasoning)**: `DISCOLOOP_CELL` -> `PIVOT_REFINE` -> `HYPOTHESIS_GENERATOR`.
- **Tier 3 (Evolution)**: `EKSFT_TRAINING` -> `EVOLUTION_GATE` -> `SELF_IMPROVEMENT_CORE`.

## 2. Migration Roadmap

### Phase 5a: Memory & Knowledge (HMS/SAGE/AutoMem)
- **Target**: `trading_bot/core/hms/`
- **Actions**:
    - Update `HierarchicalMemorySystem` to support agentic actions.
    - Integrate `SAGE` graph-memory as the primary knowledge backend.
    - Implement the `AutoMem` two-loop optimization service.
- **Risk**: High. Data migration from old research ledger to new graph-memory.
- **Rollback**: Keep old `.json` ledger files as read-only fallbacks.

### Phase 5b: Core Intelligence (CSC/HASP/DiscoLoop)
- **Target**: `trading_bot/core/csc/`
- **Actions**:
    - Refactor `CognitiveSystemController` to implement the 12-step pipeline.
    - Implement `SkillProgramHarness` (HASP) for executable guardrails.
    - Update `HypothesisGenerator` with the `Pivot/Refine` decision loop.
    - (Partial) Implement `DiscoLoop` reasoning hooks (requires model-specific support).
- **Risk**: Critical. This is the heart of the system.
- **Rollback**: Maintain `CognitiveSystemController_V4` as a fallback delegator.

### Phase 5c: Self-Improvement & Training (RSEA/EKSFT)
- **Target**: `trading_bot/governance/` and `trading_bot/learning/`
- **Actions**:
    - Hard-code the `Evolution Gate` in `evolution_gate.py` with monotone-safe checks.
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
