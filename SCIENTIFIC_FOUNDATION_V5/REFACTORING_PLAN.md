# Refactoring Plan: AlphaAlgo UCA V5 Implementation

## 1. Dependency Graph
- **Foundation Layer (LogAct)**: `UnifiedDecisionBus` (Backbone) $\to$ `ImmutableShield` (Voter).
- **Intelligence Layer (CSC)**: `DiscoLoopCell` $\to$ `SkillRouter` (HASP/S2L) $\to$ `CognitiveSystemController` (12-step).
- **Knowledge Layer (HMS)**: `SAGEGraphMemory` $\to$ `AutoMemOptimizer` $\to$ `HierarchicalMemorySystem`.
- **Evolution Layer (Gate)**: `EKSFTMasking` $\to$ `MonotoneSafeValidator` $\to$ `EvolutionGate`.

## 2. Migration Roadmap

### Phase 5a: LogAct & Skill Routing
- **Target**: `trading_bot/core/unified_event_bus.py`, `trading_bot/core/csc/router.py`.
- **Actions**:
    - Finalize shared-log total ordering in `UnifiedDecisionBus`.
    - Implement `HASPHarness` for executable skill programs.
- **Risk**: Moderate. Backward compatibility with legacy bus must be preserved.

### Phase 5b: HMS-SAGE Memory
- **Target**: `trading_bot/core/hms/memory.py`.
- **Actions**:
    - Implement `SAGEEvolutionLoop` for graph pruning and evolution.
    - Integrate `AutoMem` schema optimization.
- **Risk**: High. Potential data loss during ledger-to-graph migration.

### Phase 5c: CSC Recursive Active Inference
- **Target**: `trading_bot/core/csc/controller.py`.
- **Actions**:
    - Implement the 12-step pipeline utilizing `DiscoLoopRecurrence`.
    - Deploy `PivotRefineOperator` for self-healing strategy refinement.
- **Risk**: Critical. Core reasoning logic overhaul.

### Phase 5d: Evolution & EKSFT
- **Target**: `trading_bot/governance/evolution_gate.py`.
- **Actions**:
    - Implement `SelectiveMaskingOperator` for EKSFT-compliant fine-tuning.
    - Enforce monotone-safe checks for all system updates.
- **Risk**: Medium.

## 3. Risk Analysis & Mitigation
- **Complexity**: Mitigated by strict "One Brain" (CSC) architecture and "LogAct" for observability.
- **Latency**: Mitigated by moving heavyweight graph evolution and SFT to background workers.
- **Reliability**: Mitigated by transactional voting in the LogAct backbone.

## 4. Validation Plan
- **ECE (Expected Calibration Error)**: Measure model confidence vs. accuracy (DeepWeb-Bench).
- **Derivation Success**: Measure consistency of multi-step reasoning chains.
- **Gain Metric**: Measure online learning improvement rate (CL-Bench).
- **Sharpe/Drawdown**: Standard financial metrics via institutional backtest.
