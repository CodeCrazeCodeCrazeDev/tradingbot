# Phase 5.4: Controlled Archive Plan

The following directories and files are identified as redundant based on the Phase 5.3 audit. They will be moved to `_archive_phase1/` to simplify the architecture while preserving logic for potential migration.

## 1. Redundant Orchestrators
- `master_orchestrator.py` (root) -> Delegator logic already in shims.
- `trading_bot/core/orchestrator.py` -> Replaced by `LegacyOrchestratorAdapter`.
- `trading_bot/aamis_v3/aamis_master_orchestrator.py` -> Integrated into IAS.
- `trading_bot/elite_ai_system/elite_trading_orchestrator.py` -> Integrated into IAS.
- `trading_bot/perplexity_trading/orchestrator.py` -> Integrated into IAS.

## 2. Redundant Registries
- `trading_bot/system_registry.py` -> Consolidated into `ServiceRegistry`.
- `trading_bot/registry/module_registry.py` -> Consolidated into `ServiceRegistry`.

## 3. Redundant Memory Systems
- `trading_bot/perplexity_trading/persistent_memory.py` -> Replaced by `MemorySystem`.
- `trading_bot/intelligence_core/structural_memory.py` -> Replaced by `MemorySystem`.

## 4. Redundant World Models
- `trading_bot/world_model/fwm_core.py` -> Replaced by `WorldModelV2`.
- `trading_bot/simulation/market_simulator.py` -> Replaced by `WorldModelV2` simulator.

## 5. Implementation Strategy
1. Create `_archive_phase1` structure mirroring `trading_bot`.
2. Move files using `git mv` (or `mv` if git not available).
3. Update `__init__.py` files to remove references.
4. Verify with `pytest tests/integration/test_one_brain_flow.py`.
