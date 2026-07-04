# World Model Architectural Audit Report - 2026

## Phase 1: Missing Symbol Root Cause Analysis

The following symbols were identified in `trading_bot/world_model/__init__.py` but were missing from their designated implementation files.

| Symbol | Status | Classification | Evidence |
| :--- | :--- | :--- | :--- |
| **StreamModality** | Missing | Planned but never written | Not found in codebase. Design comment in L1. |
| **MultimodalFrame** | Missing | Planned but never written | Not found in codebase. |
| **TemporalSegmentNetwork** | Missing | Planned but never written | Not found in codebase. |
| **SurpriseReservoir** | Missing | Planned but never written | Not found in codebase. |
| **MultimodalPerceptionEncoder** | Missing | Planned but never written | Not found in codebase. |
| **JEPALatentPredictor** | Missing | Replaced by Architecture | Superseded by WM-V2 (Transformer-Mamba). |
| **ProbabilisticEdge** | Missing | Planned but never written | Not found in codebase. |
| **InterventionOperator** | Missing | Planned but never written | Not found in codebase. |
| **ObjectSlot** | Missing | Planned but never written | Not found in codebase. |
| **ObjectSceneGraph** | Missing | Planned but never written | Not found in codebase. |
| **SlotAttentionEncoder** | Missing | Planned but never written | Not found in codebase. |
| **RelationalGraphNetwork** | Missing | Planned but never written | Not found in codebase. |
| **RolloutOutput** | Missing | Planned but never written | Not found in codebase. |
| **CausalReasoningModule** | Missing | Planned but never written | Not found in codebase. |
| **InterventionTargetSelector** | Missing | Planned but never written | Not found in codebase. |
| **EnvironmentInvarianceTester** | Missing | Planned but never written | Not found in codebase. |
| **ActiveProbingLoop** | Missing | Planned but never written | Not found in codebase. |
| **FastRSSMModel** | Misplaced | Exists elsewhere | Located in `latent_dynamics_utils.py`. |
| **EdgeType** | External | Exists elsewhere | Located in `msos/quant_factory.py`. |
| **CounterfactualSimulator** | External | Exists elsewhere | Located in `decision_governance/layer5_counterfactual.py`. |

## Phase 2: World Model Dependency Map

### Internal Architecture
- **WM-V2 (Canonical)**: `v2_core.py` -> `world_state.py`.
- **V1 Hierarchy**: `latent_dynamics.py` -> `perception.py`, `hierarchical_time.py`, `meta_dynamics.py`, `world_state.py`, `uncertainty_engine.py`.
- **Planning**: `imagination.py` -> `latent_dynamics.py`.
- **Simulation**: `simulation_orchestrator.py` -> `imagination.py`, `experience_replay.py`, `synthetic_data.py`.

### External Consumers
- **IntegratedAgentSystem (IAS)**: Primary entry point. Uses `LegacyWorldModelAdapter` to wrap `WorldModelV2`.
- **MasterOrchestrator**: Consumes strategic decisions and world state.

### Identified Issues
- **Architectural Drift**: Three overlapping World Model implementations (V1, V2, FWM).
- **Broken API**: `__init__.py` contains 20+ broken imports.
- **Missing Factories**: `create_counterfactual_engine` missing from `counterfactual_engine.py`.

## Phase 3: Canonical Foundation

**Canonical Implementation**: `WorldModelV2` (Institutional Predictive Planning)

**Reasoning**:
1. **Production Readiness**: It is the current functional core used by the IAS.
2. **Scientific Rigor**: Uses Mamba SSM for linear scaling with high-frequency data, superior to the RNN-based V1.
3. **Completeness**: Provides a unified cross-asset encoder and future scenario simulator.

**Migration Path**:
- Standardize `world_model/__init__.py` around WM-V2.
- Retain V1 `WorldModel` for legacy transition but exclude its missing sub-components from the API.
- Ensure all support infrastructure (uncertainty, ignorance, state) is compatible with V2.
