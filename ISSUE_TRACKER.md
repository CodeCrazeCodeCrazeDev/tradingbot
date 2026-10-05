# ISSUE TRACKER — AlphaAlgo Production Engineering Audit

## Overview
This document tracks 35 real, engineering-significant issues discovered during the Production Engineering Audit, categorized by Issue ID, Severity, Category, Affected Files, Technical Explanation, and Resolution Status.

---

| Issue ID | Severity | Category | Affected Files | Technical Explanation | Resolution Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ISSUE-001** | **Critical** | Security / Sandbox | `trading_bot/aads/core/alpha_evolve_engine.py` | Dynamic `exec()` was called without prior AST security validation via `SecureASTVisitor`, risking arbitrary code execution. | **RESOLVED** (Enforced `SecureASTVisitor` check prior to `exec()`) |
| **ISSUE-002** | **Critical** | Concurrency / Async | `trading_bot/intel/news_pipeline.py` | Synchronous `requests.get()` call inside `async def _fetch_from_newsapi` blocked the asyncio event loop during news ingestion. | **RESOLVED** (Wrapped with `await asyncio.to_thread`) |
| **ISSUE-003** | **Critical** | Concurrency / Async | `trading_bot/neuros_evolution/plotcode_integration.py` | Synchronous `requests.post()` call inside `async def _execute_plotcode_test` blocked the event loop during visual testing. | **RESOLVED** (Wrapped with `await asyncio.to_thread`) |
| **ISSUE-004** | **High** | Risk Management | `risk/risk_manager.py` | Position size check compared total dollar position size (> 1.0) directly against fractional risk limit (1.0), rejecting large dollar trades or miscalculating risk. | **RESOLVED** (Added `account_balance` scaling for dollar trades) |
| **ISSUE-005** | **High** | Risk Management | `trading_bot/orchestrator/risk_manager.py` | `validate_trade` risk calculation multiplied raw dollar size by risk fraction, exceeding max position risk limit. | **RESOLVED** (Scaled position risk fraction by portfolio value) |
| **ISSUE-006** | **High** | Concurrency | `scripts/launchers/run_comprehensive_system_test.py` | Synchronous `time.sleep()` in async function blocked event loop execution. | **RESOLVED** (Converted to `await asyncio.sleep()`) |
| **ISSUE-007** | **High** | Concurrency | `scripts/runners/run_deepseek_safe_24_7.py` | Synchronous `time.sleep()` in async runner blocked event loop during long-running background tasks. | **RESOLVED** (Converted to `await asyncio.sleep()`) |
| **ISSUE-008** | **Medium** | Reliability | `scripts/full_system_audit.py:36` | Bare `except: pass` swallowed AST inspection errors without logging failure modes. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-009** | **Medium** | Reliability | `scripts/full_system_audit.py:67` | Bare `except: pass` swallowed system exceptions during system auditing. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-010** | **Medium** | Reliability | `scripts/full_system_audit.py:137` | Bare `except: pass` swallowed file read errors silently. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-011** | **Medium** | Reliability | `scripts/full_system_audit.py:160` | Bare `except: pass` swallowed subprocess execution exceptions. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-012** | **Medium** | Reliability | `scripts/full_system_audit.py:191` | Bare `except: pass` swallowed JSON parsing exceptions. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-013** | **Medium** | Reliability | `scripts/structural_alignment.py:73` | Bare `except: pass` swallowed AST inspection errors without recording failure modes. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-014** | **Medium** | Reliability | `scripts/security_audit.py:83` | Bare `except: pass` swallowed security inspection exceptions. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-015** | **Medium** | Reliability | `scripts/security_audit.py:113` | Bare `except: pass` swallowed credential audit exceptions. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-016** | **Medium** | Reliability | `scripts/security_audit.py:141` | Bare `except: pass` swallowed permissions audit exceptions. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-017** | **Medium** | Reliability | `scripts/security_audit.py:162` | Bare `except: pass` swallowed token audit exceptions. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-018** | **Medium** | Testing | `tests/test_superior_architecture_minimal.py` | Mock shield voter return value lacked `"approved": True` dictionary key expected by `CognitiveSystemController`. | **RESOLVED** (Updated return dictionary structure) |
| **ISSUE-019** | **Medium** | Testing | `tests/orchestrator/test_orchestrator_integration.py` | Missing `TradingDecision` import caused `NameError` during orchestrator integration tests. | **RESOLVED** (Added explicit import) |
| **ISSUE-020** | **Medium** | Testing | `tests/test_scientific_architecture_uca2026.py` | `CognitiveSystemController` docstring missing mandatory paper citations required by traceability audit. | **RESOLVED** (Updated docstring paper traceability matrix) |
| **ISSUE-021** | **Low** | Reliability | `scripts/maintenance/run_fix_all_remaining.py:352` | Bare `except: pass` hid script execution issues. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-022** | **Low** | Reliability | `scripts/fixes/fix_all_issues_safe.py:16` | Bare `except: pass` swallowed issue repair exceptions. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-023** | **Low** | Reliability | `scripts/deployment/prepare_deployment.py:270` | Silent exception swallowing obscured deployment pre-check failures. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-024** | **Low** | Reliability | `scripts/deployment/deployment_audit.py:212` | Bare `except: pass` swallowed docker config check errors. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-025** | **Low** | Reliability | `scripts/deployment/deployment_audit.py:252` | Bare `except: pass` swallowed deployment environment verification errors. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-026** | **Low** | Reliability | `scripts/validation/validate_deepseek.py:157` | Bare `except: pass` swallowed deepseek validation exceptions. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-027** | **Low** | Reliability | `scripts/launchers/thinking_bot_validated.py:252` | Bare `except: pass` swallowed bot validation exceptions. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-028** | **Low** | Reliability | `scripts/launchers/run_live_trading.py:204` | Bare `except: pass` swallowed live trading connection errors. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-029** | **Low** | Reliability | `scripts/launchers/thinking_bot.py:1285` | Bare `except: pass` swallowed bot runtime errors. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-030** | **Low** | Reliability | `scripts/monitoring/check_real_prices.py:86` | Bare `except: pass` swallowed price feed errors. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-031** | **Low** | Reliability | `scripts/monitoring/check_memory.py:14` | Bare `except: pass` swallowed memory profiling errors. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-032** | **Low** | Reliability | `scripts/runners/run_all_modules_light.py:331` | Bare `except: pass` swallowed light module execution errors. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-033** | **Low** | Reliability | `scripts/runners/run_all_modules_light.py:340` | Bare `except: pass` swallowed runner setup errors. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-034** | **Low** | Reliability | `scripts/runners/run_all_modules_light.py:357` | Bare `except: pass` swallowed runner cleanup errors. | **RESOLVED** (Replaced with structured logging) |
| **ISSUE-035** | **Low** | Platform | `trading_bot/dashboard/realtime_dashboard.py` | Direct import of `dash` without try/except fallback caused startup failures on headless environments. | **RESOLVED** (Wrapped in try/except fallback block) |
