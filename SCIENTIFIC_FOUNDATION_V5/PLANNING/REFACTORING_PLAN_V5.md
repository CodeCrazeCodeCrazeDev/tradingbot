# Refactoring Plan: AlphaAlgo UCA V5 Implementation

## 1. Dependency Graph
- `WMV3_CORE` (Foundation)
- `SAGE_GRAPH` -> `HMS_SYSTEM` (Memory)
- `HASP_HARNESS` -> `SKILL_ROUTER` -> `CSC_CONTROLLER` (Intelligence)
- `EKSFT_LOSS` -> `EVOLUTION_GATE` (Evolution)

## 2. Migration Roadmap

### Phase 1: Core Reasoning (CSC & DiscoLoop)
- **Files**: `trading_bot/core/csc/controller.py`
- **Actions**: Replace forward-only pass with $K$-step DiscoLoop recurrence. Implement actual `Pivot/Refine` logic.

### Phase 2: Memory Evolution (SAGE & AutoMem)
- **Files**: `trading_bot/core/hms/memory.py`
- **Actions**: Replace mock BFS with multi-hop SAGE retrieval. Implement `AutoMem` Loop 1 structure optimization.

### Phase 3: Executable Skills (HASP & S2L)
- **Files**: `trading_bot/core/csc/router.py`
- **Actions**: Implement `HASPExecutor` for Python-based skill programs. Populate `SkillRouter` with initial S2L adapters.

## 3. Risk Analysis & Mitigation
- **Latency**: DiscoLoop $K > 3$ may exceed 500ms limit. *Mitigation*: Adaptive $K$ based on confidence.
- **Complexity**: SAGE graph may drift. *Mitigation*: Periodic pruning via AutoMem.
- **Safety**: Executable PFs could crash. *Mitigation*: Strict `try/except` wrappers and validation in `HASPExecutor`.

## 4. Rollback Strategy
- Maintain `_v4.py` copies of all major files.
- `CognitiveSystemController` instance check for `V5_ENABLED` flag.

## 5. Validation Plan
- **DeepWeb-Bench**: Measure calibration and derivation depth.
- **CL-Bench**: Measure "Gain Metric" ($G$) to ensure online learning.
- **Latency Benchmark**: Ensure decision time < 500ms.
