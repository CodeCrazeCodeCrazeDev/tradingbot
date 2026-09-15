# Issue Tracker - Production Engineering Audit

This document tracks all identified engineering defects, security vulnerabilities, performance bottlenecks, and reliability issues across the AlphaAlgo codebase.

---

## 1. Issue Summary

| Issue ID | Category | Severity | Description | Status |
|---|---|---|---|---|
| ERR-001 | Syntax | Critical | Parenthesized list comprehension unpacking error in `risk/risk_manager.py` | FIXED |
| ERR-002 | Syntax | High | Indentation/scoping syntax error in `scripts/fixes/auto_fix_critical_issues_v2.py` | FIXED |
| ERR-003 | Syntax | High | Indentation/scoping syntax error in `scripts/deployment/deploy_5star_production.py` | FIXED |
| ERR-004 | Syntax | High | Indentation/scoping syntax error in `scripts/launchers/run_alphaalgo_5star.py` | FIXED |
| ERR-005 | Syntax | High | Scoping error (`return` outside function) in `scripts/utilities/alphaalgo_autonomous_operator.py` | FIXED |
| ERR-006 | Syntax | High | Indentation/import errors in `tests/orchestrator/test_orchestrator_master.py` | FIXED |
| ERR-007 | Syntax | High | Indentation/import errors in `tests/orchestrator/test_orchestrator_ml_predictor.py` | FIXED |
| ERR-008 | Syntax | High | Indentation/import errors in `tests/orchestrator/test_orchestrator_performance.py` | FIXED |
| ERR-009 | Syntax | High | Indentation/import errors in `tests/orchestrator/test_orchestrator_standalone.py` | FIXED |
| ASYNC-010 | Concurrency | Medium | Blocking `time.sleep` in async benchmark method in `trading_bot/core/validation.py` | FIXED |
| SEC-011 | Security | Critical | Un-sandboxed `exec` call in `trading_bot/distributed/parallel_backtester.py` | FIXED |
| SEC-012 | Security | Critical | Un-sanitized `pickle.load` in `trading_bot/ml/automl_pipeline.py` | FIXED |
| REL-013 | Reliability | Medium | Silent exception swallowing (`except: pass`) in `trading_bot/core/csc/controller.py` | FIXED |
| PERF-014 | Performance | Medium | Non-vectorized candle loop in `VolumeDeltaHeatmap` in `trading_bot/indicators/advanced_liquidity.py` | FIXED |

---

## 2. Issue Details & Remediations

### ERR-001: Unpacking Syntax in Risk Manager
- **Root Cause**: Unparenthesized list comprehension unpacking `*[f"- {sym}: {limit:.2f}" ...]` in list literal.
- **Remediation**: Wrapped unpacking expression in parentheses `*([...])`.

### ASYNC-010: Blocking I/O in Async Validation
- **Root Cause**: `time.sleep(0.01)` inside `async def benchmark_latency()`.
- **Remediation**: Replaced with `await asyncio.sleep(0.01)`.

### SEC-011: Strategy Execution Sandboxing
- **Root Cause**: `exec()` called on strategy code string without validating AST.
- **Remediation**: Injected `SecureASTVisitor().validate_code(strategy_code)` before execution.

### PERF-014: Vectorization of Footprint Heatmap
- **Root Cause**: Row-by-row iteration over OHLC DataFrame using `df.iterrows()`.
- **Remediation**: Replaced with 2D NumPy array broadcasting and boolean masking.
