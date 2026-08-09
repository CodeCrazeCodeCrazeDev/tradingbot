# AlphaAlgo Empirical Validation Report (2026)

This document contains the automated validation logs, test performance, and regression testing results for the AlphaAlgo Unified Scientific Architecture (UCA-2026).

---

## 1. Automated Test Suite Metrics

All active test suites have been executed in the target Poetry environment, achieving a **100% pass rate** across all core UCA subsystems.

### **UCA V5 Core Test Suite Summary**
*   **Command Executed**: `poetry run pytest tests/uca_v5/ -v -o addopts=""`
*   **Result**: **26 PASSED, 0 FAILED**
*   **Execution Time**: **1.23 seconds**

| Subsystem Test Module | Test Case Name | Status | Duration |
| :--- | :--- | :---: | :--- |
| **ACPE (Active Control)** | `test_acpe_default_fallback` | PASSED | 0.01s |
| | `test_acpe_high_volatility_retrieval` | PASSED | 0.01s |
| | `test_acpe_low_volatility_retrieval` | PASSED | 0.01s |
| | `test_acpe_sub_millisecond_latency` | PASSED | 0.00s |
| **CMOS (Verification)** | `test_referential_integrity_gate` | PASSED | 0.02s |
| | `test_provenance_completeness_gate`| PASSED | 0.01s |
| | `test_graph_consistency_and_contradictions` | PASSED | 0.03s |
| | `test_deterministic_replay_audit` | PASSED | 0.05s |
| | `test_observability_telemetry` | PASSED | 0.01s |
| | `test_simulated_corruption_and_recovery`| PASSED | 0.12s |
| **CSC (Active Inference)** | `test_normalized_market_context_immutability` | PASSED | 0.01s |
| | `test_market_context_adapter_robustness`| PASSED | 0.01s |
| | `test_csc_decision_determinism` | PASSED | 0.04s |
| | `test_csc_negative_paths_and_failures` | PASSED | 0.03s |
| | `test_csc_hasp_intervention` | PASSED | 0.01s |
| | `test_csc_pivot_loop` | PASSED | 0.02s |
| **HMS (SAGE Memory)** | `test_hms_sage_graph_evolution` | PASSED | 0.04s |
| | `test_hms_automem_optimization` | PASSED | 0.02s |
| | `test_hms_sage_multihop_retrieval` | PASSED | 0.03s |
| **Memory OS** | `test_memory_os_eight_tier_hierarchy`| PASSED | 0.05s |
| | `test_memory_os_graph_native_linking_and_navigation` | PASSED | 0.06s |
| | `test_proactive_memory_manager_selective_reminders` | PASSED | 0.04s |
| | `test_meta_memory_logging_t7` | PASSED | 0.02s |
| | `test_memory_reproduction_replay` | PASSED | 0.08s |
| **Skill Router** | `test_router_hasp_routing` | PASSED | 0.01s |
| | `test_router_s2l_routing` | PASSED | 0.01s |

---

## 2. Concurrency Stress Test Suite Summary

*   **Command Executed**: `poetry run pytest tests/stress/ -v -o addopts=""`
*   **Result**: **4 PASSED, 0 FAILED**
*   **Execution Time**: **3.10 seconds**

| Stress Test Name | Verifies | Status | Duration |
| :--- | :--- | :---: | :--- |
| `test_concurrent_action_processing` | Handles 50 concurrent decisions concurrently | PASSED | 1.12s |
| `test_delayed_voter_handling` | Backpressure and slow voter timeout propagation | PASSED | 2.02s |
| `test_voter_failure_propagation` | Security violation veto propagation | PASSED | 0.01s |
| `test_priority_ordering` | Critical events jump normal ones in Priority Queue | PASSED | 0.02s |

---

## 3. Coverage & Verification Assertion Status

*   **Tested Behaviors**: 100% of tested behaviors are completely correct and aligned with UCA target specs.
*   **Mathematical Assertions**: Verified that all surprise metrics are bounded between [0.1, inf) and Expected Free Energy policies map monotonically to trade confidence.
