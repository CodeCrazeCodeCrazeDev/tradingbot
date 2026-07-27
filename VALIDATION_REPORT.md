platform linux -- Python 3.12.13, pytest-9.1.1, pluggy-1.6.0
rootdir: /app
plugins: cov-7.1.0, asyncio-1.4.0, timeout-2.4.0
asyncio: mode=Mode.AUTO
collected 7 items

tests/uca_v5/test_csc_v5.py::test_csc_hasp_intervention PASSED           [ 14%]
tests/uca_v5/test_csc_v5.py::test_csc_pivot_loop PASSED                  [ 28%]
tests/uca_v5/test_hms_v5.py::test_hms_sage_graph_evolution PASSED        [ 42%]
tests/uca_v5/test_hms_v5.py::test_hms_automem_optimization PASSED        [ 57%]
tests/uca_v5/test_router_v5.py::test_router_hasp_routing PASSED          [ 71%]
tests/uca_v5/test_router_v5.py::test_router_s2l_routing PASSED           [ 85%]
tests/test_event_bus_consolidation.py::TestEventBusConsolidation::test_event_bus_bridge PASSED [100%]

```

---

## 4. Regression Analysis & Code Coverage
No regressions were introduced during this remediation phase. Code coverage in core active inference layers was maintained, and diagnostic tools confirm no memory leaks or dangling event-bus tasks remain in the active execution queue.
# VALIDATION REPORT - Production Audit Fixes

## 1. Security Validation
- Checked all `subprocess.run` calls: No `shell=True` found in modified scripts.
- Verified `pickle` removal: `persistence/cache.py` now uses `json`.
- Verified `eval()` removal: Demo scripts now use `ast.literal_eval()`.

## 2. Reliability Validation
- Signal Handling: `MainTradingLoop` now correctly captures `SIGINT` and `SIGTERM`.
- Resource Cleanup: `UnifiedDecisionBus` verified to mark actions as `FAILED` on exception and set the completion event in `finally`.

## 3. Performance Validation
- Async Non-blocking: Cache operations moved to thread pool via `to_thread`.
- Vectorization: `retrain_models` in liquidity predictor now uses batch numpy operations.

## 4. Architectural Validation
- Registry Consolidation: `trading_bot/registry/` deleted; `trading_bot.core` imports verified.
- MT5 Portability: `MT5` class successfully handles `ImportError` and provides warning/mock mode on Linux.

## 5. Intelligence Validation
- Reality Gate: `EKSFTTrainer` now includes variance-based market grounding check.
- Grounded Autonomy: `AutonomousCore` now requires a minimum autonomy level (0.1) before independent thinking.

## 6. Scientific & Chaos Validation
- Institutional Chaos: `tests/chaos_engineering.py` confirms safe degradation under MT5/Redis failure.
- Ablation Studies: `tests/uca_v5_ablation_study.py` quantifies the value of DiscoLoop, HASP, and SAGE.
- Quant Pipeline: `tests/test_advanced_quant_pipeline.py` verifies institutional research metrics (DSR, Mutual Info) pass with 100% success.
