# Comprehensive Validation Framework & Subsystem Migration Strategy (2026)

This document represents Phase 4 (Validation Plan, Risk Analysis, and Migration Strategy) of the AlphaAlgo Scientific Refactoring Directive. It establishes objective quantitative metrics, subsystem classification boundaries, and non-disruptive rollback procedures.

---

## 1. Quantitative Validation Framework

Every refactored or synthesized component in AlphaAlgo must satisfy the following strict, measurable validation gates before production promotion:

### 1.1. Reasoning Quality & Horizon
- **Metric**: Complete execution of the 12-stage Recursive Active Inference loop without early termination or unhandled exceptions under normal regimes.
- **Acceptance Criteria**: 100% of pipeline stages logged with clear, non-empty tracing outputs.
- **Validation Test**: `tests/test_csc_v5.py::test_csc_12_step_pipeline`

### 1.2. Expected Calibration Error (ECE)
- **Metric**: Distance between model prediction confidence and true frequency of success across $B=10$ validation bins.
  $$\text{ECE} = \sum_{b=1}^B \frac{|B_b|}{N} \left| \text{acc}(B_b) - \text{conf}(B_b) \right|$$
- **Acceptance Criteria**: $\text{ECE} \le 0.05$.
- **Validation Test**: `tests/uca_v5/test_csc_contract_and_determinism.py`

### 1.3. Decision Latency
- **Metric**: Time elapsed between receiving a raw market observation and emitting a fully validated `CoreDecision` (in milliseconds).
- **Acceptance Criteria**: Mean Latency $\le 1.0\text{ms}$; p99 Latency $\le 5.0\text{ms}$ on CPU.
- **Validation Test**: `tests/uca_v5/test_acpe.py::test_acpe_sub_millisecond_latency`

### 1.4. Monotone-Safe Gain (G)
- **Metric**: Performance improvement over baseline across continual learning tasks without causing regression in any safety, latency, or ECE thresholds.
  $$G = R(\theta_{candidate}) - R(\theta_{baseline}) \ge 0.05$$
- **Acceptance Criteria**: Gate must return `False` if any metric has statistically significant regression.
- **Validation Test**: `tests/test_skills_and_evolution.py::test_evolution_gate_multi_dim`

---

## 2. Subsystem Migration Strategy

To guarantee zero regression during the refactoring process, all subsystems are classified under one of the following six disciplines:

### 2.1. Subsystem Classification Matrix

| Subsystem Domain | Classification | Rationale | Code Files Involved | Rollback Procedure |
| :--- | :--- | :--- | :--- | :--- |
| **Cognitive Core (CSC)** | **Canonical** | Single authoritative brain. No duplication permitted. | `trading_bot/core/csc/controller.py` | Restore original file via git checkout. |
| **Memory Substrate (HMS)** | **Canonical** | Central persistent repository for ledger and SAGE. | `trading_bot/core/hms/memory.py` | Restore original database schema from SQLite backup. |
| **Skill Router** | **Refactor** | Needs adapter unification and Chameleon string mappings. | `trading_bot/core/csc/router.py` | Revert to version 1.0 using `git restore`. |
| **Unified Event Bus** | **Merge** | Combine all async event loops into a single shared LogAct instance. | `trading_bot/core/unified_event_bus.py` | Revert event loop changes via git checkout. |
| **Legacy Prompts** | **Replace** | Passive instructions replaced with executable HASP Program Functions. | `trading_bot/core/csc/router.py` | Restore passive prompt files. |
| **Duplicate Directories** | **Delete** | Eliminate duplicate directories (`agents 2`, `advanced_systems 2`) to clean import tree. | `_archive/` | Move deleted folders back from garbage bin. |

---

## 3. Rollback & Contingency Procedures

In the event of verification or benchmark failures:
1. **Immediate Step-Back**: Revert any active files to the last known stable SHA.
2. **Deterministic Replay Check**: Run `poetry run pytest tests/test_deterministic_replay.py` to isolate state corruption.
3. **Database Restore**: Restructure schemas to Version 1.0 using the `HierarchicalMemorySystem.migrate_to_version("1.0")` backward-migration step.
