# AlphaAlgo Production Issue Tracker — 2026 Audit

This document tracks identified, resolved, and monitored engineering defects and scientific regressions across the AlphaAlgo codebase.

---

## Registry of Resolved Production Engineering Defects (Key Issues)

### **DEFECT-UCA-2026-01**: Portfolio Risk Manager Dollar Position Sizing Scaling Flaw
*   **Component**: `trading_bot/orchestrator/risk_manager.py`
*   **Severity**: **CRITICAL**
*   **Root Cause**: `validate_trade` evaluated raw `risk * size` without scaling against portfolio capital for dollar trade sizes (`size > 1.0`), causing false positive trade rejections.
*   **Files Affected**: `trading_bot/orchestrator/risk_manager.py`
*   **Technical Explanation**: Trade sizes passed in dollar terms (e.g. `$1000`) caused `position_risk` to calculate as `500.0`, vastly exceeding `max_position_risk = 0.02`.
*   **Solution Implemented**: Scaled position risk against total portfolio capital when `size > 1.0` (`position_risk = (risk * size) / capital`). Set `max_concentration` default fallback to `0.4`.
*   **Verification Performed**: `python3 -m pytest -o addopts="" tests/orchestrator/test_orchestrator_risk_manager.py` passed 100%.

### **DEFECT-UCA-2026-02**: Unsafe Dynamic `eval()` Expressions in Analysis Demo
*   **Component**: `examples/advanced_market_analysis_demo.py`
*   **Severity**: **HIGH**
*   **Root Cause**: Used built-in `eval()` to parse JSON stringified dictionary parameters from Dash callbacks.
*   **Files Affected**: `examples/advanced_market_analysis_demo.py`
*   **Technical Explanation**: Direct `eval()` invocation allows arbitrary code execution if untrusted payload strings are passed to callback inputs.
*   **Solution Implemented**: Replaced all `eval()` calls with safe AST parsing using `ast.literal_eval()`.
*   **Verification Performed**: AST static analysis check verified clean safe parsing.

### **DEFECT-UCA-2026-03**: Missing `TradingDecision` Import in Orchestrator Integration Test
*   **Component**: `tests/orchestrator/test_orchestrator_integration.py`
*   **Severity**: **MEDIUM**
*   **Root Cause**: `test_predict_and_execute_flow` instantiated `TradingDecision(...)` without importing it in the local test function scope.
*   **Files Affected**: `tests/orchestrator/test_orchestrator_integration.py`
*   **Technical Explanation**: Local scope instantiation raised `NameError: name 'TradingDecision' is not defined`.
*   **Solution Implemented**: Added `from trading_bot.orchestrator.master_orchestrator import TradingDecision` to `test_predict_and_execute_flow`.
*   **Verification Performed**: `python3 -m pytest -o addopts="" tests/orchestrator/test_orchestrator_integration.py` passed 100%.

### **DEFECT-UCA-2026-04**: Non-Affirmative Mock Shield Voter in Superior Architecture Tests
*   **Component**: `tests/test_superior_architecture_minimal.py`, `tests/verification/test_e2e_decision_pipeline.py`
*   **Severity**: **HIGH**
*   **Root Cause**: Mock shield voter did not define `audit_log_action.return_value`, causing `UnifiedDecisionBus` fail-closed veto.
*   **Files Affected**: `tests/test_superior_architecture_minimal.py`, `tests/verification/test_e2e_decision_pipeline.py`
*   **Technical Explanation**: The event bus checks registered shield voters for affirmative decision returns (`{"approved": True, "decision": "APPROVED"}`). Unmocked voters default to `MagicMock`, returning `'no decision'` and triggering a veto.
*   **Solution Implemented**: Configured `mock_shield.audit_log_action.return_value = {"approved": True, "decision": "APPROVED"}`.
*   **Verification Performed**: `python3 -m pytest -o addopts="" tests/test_superior_architecture_minimal.py tests/verification/test_e2e_decision_pipeline.py` passed 100%.

### **DEFECT-UCA-2026-05**: Blocking Synchronous HTTP Requests in Async News Pipeline
*   **Component**: `trading_bot/intel/news_pipeline.py`
*   **Severity**: **HIGH**
*   **Root Cause**: `requests.get` called directly inside async fetching method.
*   **Files Affected**: `trading_bot/intel/news_pipeline.py`
*   **Technical Explanation**: Synchronous I/O blocks the single-threaded asyncio event loop during network requests.
*   **Solution Implemented**: Wrapped synchronous HTTP call with `await asyncio.to_thread(requests.get, url, timeout=10)`.
*   **Verification Performed**: Event loop profiler verified non-blocking execution.

### **DEFECT-UCA-2026-06**: Missing Path Import in Risk Unit Tests
*   **Component**: `tests/risk/` test suite
*   **Severity**: **LOW**
*   **Root Cause**: Pathlib `Path` referenced without top-level import in multiple risk test headers.
*   **Files Affected**: 50 test files in `tests/risk/`
*   **Technical Explanation**: Unimported `Path` symbol caused Pytest collection failures when running standalone risk test modules.
*   **Solution Implemented**: Prepended `from pathlib import Path` to all test files in `tests/risk/`.
*   **Verification Performed**: `python3 -m pytest -o addopts="" tests/risk/` passed 1,063 tests without collection errors.
