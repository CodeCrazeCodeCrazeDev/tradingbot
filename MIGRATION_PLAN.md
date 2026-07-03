# AlphaAlgo Phase 1 Migration Plan: Orchestration Consolidation

## 1. Overview
The goal of Phase 1 is to consolidate the three competing orchestration systems into a single, unified decision authority: the `IntegratedAgentSystem` (IAS).

## 2. Migration Map

| Current System | Role | Migration Path |
|---|---|---|
| `master_orchestrator.py` (root) | Multi-process layer coordinator | Logic moved to IAS `start()` and a unified launcher. |
| `trading_bot/core/orchestrator.py` | Basic trading loop coordinator | Replaced by IAS `think()` -> `execute()` loop. |
| `IntegratedAgentSystem` (IAS) | Research-grade brain | **PROMOTED** to the primary system controller. |
| `MetaOrchestrator` | Task decomposition | Becomes the IAS Planning/Evolution component. |
| `WorldModel` | Perception/Simulation | Becomes the IAS Perception component. |

## 3. Affected Files

### Core Orchestration
- `trading_bot/core_agent_system/integrated_system.py`: Enhanced to handle multi-process background services.
- `master_orchestrator.py`: Refactored to delegate to `IntegratedAgentSystem`.
- `trading_bot/core/orchestrator.py`: Replaced by an adapter or deprecated.

### Entry Points
- `trading_bot/main.py`: Refactored to initialize IAS as the primary service.
- `run_full_autonomous_system.py`: Simplified to call `IntegratedAgentSystem.start()`.

### Services
- `trading_bot/core/service_factory.py`: Updated to include IAS in Tier 1.
- `trading_bot/services/decision_layer_service.py`: Routes to IAS.

## 4. Dependency Changes
- IAS will now depend on the `EventBus` and `ServiceRegistry` from `trading_bot.core`.
- Legacy systems will depend on `LegacyOrchestratorAdapter`.

## 5. Implementation Steps

### Step 1: Brain Promotion
- Enhance `IntegratedAgentSystem` to handle the lifecycle of background services (Market Student, Eternal Evolution, etc.) previously managed by `MasterOrchestrator`.

### Step 2: Launcher Refactoring
- Update `run_full_autonomous_system.py` to use `IntegratedAgentSystem`.
- Update `trading_bot/main.py` to use IAS via the `DecisionLayerService`.

### Step 3: Legacy Adapter
- Create `trading_bot/core_agent_system/legacy_adapter.py` providing a shim for components expecting `TradingOrchestrator`.

### Step 4: Verification
- Ensure all agents are registered in the IAS `AgentRegistry`.
- Verify communication via `CoordinationLayer` and `EventBus`.

## 6. Rollback Plan
1. **File Backup:** All refactored files will be backed up (e.g., `main.py.bak`).
2. **Feature Flag:** A config flag `use_integrated_brain: true/false` will be used to toggle between IAS and legacy flow.
3. **Atomic Commits:** Changes will be committed in small, verifiable chunks.
