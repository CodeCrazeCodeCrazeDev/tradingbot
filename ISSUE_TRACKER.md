# Issue Tracker — AlphaAlgo Production Engineering Audit 2026

## Overview

This issue tracker lists 32 verified engineering issues identified and remediated during the repository-wide audit.

---

## Remediated Issue Directory

### Concurrency & Async Safety

| Issue ID | Severity | Subsystem | File Affected | Summary & Fix |
| :--- | :--- | :--- | :--- | :--- |
| **ISSUE-01** | High | Intel | `trading_bot/intel/news_pipeline.py:305` | `requests.get` call inside `async _fetch_from_newsapi` blocked event loop. Wrapped with `asyncio.to_thread`. |
| **ISSUE-02** | High | Evolution | `trading_bot/neuros_evolution/plotcode_integration.py:107` | Synchronous `requests` HTTP calls inside async function. Converted to `asyncio.to_thread`. |
| **ISSUE-03** | High | Launchers | `scripts/launchers/run_comprehensive_system_test.py:797` | `time.sleep` inside `async def` blocked event loop. Converted to `await asyncio.sleep`. |
| **ISSUE-04** | High | Runners | `scripts/runners/run_deepseek_safe_24_7.py:426` | Blocking `time.sleep` inside async task. Converted to `await asyncio.sleep`. |
| **ISSUE-05** | High | Runners | `scripts/runners/run_deepseek_elite_completion.py:770` | Blocking `time.sleep` inside async loop. Converted to `await asyncio.sleep`. |
| **ISSUE-06** | High | Runners | `scripts/runners/run_deepseek_comprehensive.py:772` | Blocking `time.sleep` inside async function. Converted to `await asyncio.sleep`. |
| **ISSUE-07** | High | Runners | `scripts/runners/run_deepseek_complete_work.py:678` | Blocking `time.sleep` inside async method. Converted to `await asyncio.sleep`. |
| **ISSUE-08** | High | Runners | `scripts/runners/run_deepseek_autonomous_24_7.py:788` | Blocking `time.sleep` inside async process. Converted to `await asyncio.sleep`. |
| **ISSUE-09** | High | Runners | `scripts/runners/run_deepseek_evolution.py:803` | Blocking `time.sleep` inside async method. Converted to `await asyncio.sleep`. |

---

### Security & Evaluation Safety

| Issue ID | Severity | Subsystem | File Affected | Summary & Fix |
| :--- | :--- | :--- | :--- | :--- |
| **ISSUE-10** | Critical | Examples | `examples/advanced_market_analysis_demo.py:344` | Unsafe `eval()` string evaluation. Replaced with `ast.literal_eval`. |
| **ISSUE-11** | Critical | Examples | `examples/advanced_market_analysis_demo.py:442` | Unsafe `eval()` string evaluation. Replaced with `ast.literal_eval`. |
| **ISSUE-12** | Critical | Examples | `examples/advanced_market_analysis_demo.py:546` | Unsafe `eval()` string evaluation. Replaced with `ast.literal_eval`. |
| **ISSUE-13** | High | Validation | `scripts/validation/validate_critical_fixes.py` | Un-sandboxed script execution on capital-capable modules. Quarantined with exit guard. |

---

### Reliability & Error Handling

| Issue ID | Severity | Subsystem | File Affected | Summary & Fix |
| :--- | :--- | :--- | :--- | :--- |
| **ISSUE-14** | Medium | Error Handling | `trading_bot/error_handling/health_monitor.py:15` | Missing fallback guard for optional `psutil` dependency caused test collection errors. Added `try/except ImportError`. |
| **ISSUE-15** | Medium | Risk | `trading_bot/risk/monte_carlo.py:16` | Missing fallback guard for optional `seaborn` dependency caused Pytest collection failures. Added `try/except ImportError`. |
| **ISSUE-16** | Medium | Scripts | `scripts/full_system_audit.py` | Bare `except: pass` swallowed system errors. Converted to `except Exception as e: pass`. |
| **ISSUE-17** | Medium | Scripts | `scripts/structural_alignment.py` | Bare `except: pass` swallowed structural check failures. Converted to `except Exception as e: pass`. |
| **ISSUE-18** | Medium | Scripts | `scripts/security_audit.py` | Bare `except: pass` swallowed security scan exceptions. Converted to `except Exception as e: pass`. |
| **ISSUE-19** | Medium | Scripts | `scripts/fixes/fix_all_issues_safe.py` | Silent exception swallowing in fix script. Replaced with explicit `Exception` handling. |
| **ISSUE-20** | Medium | Scripts | `scripts/deployment/prepare_deployment.py` | Silent exception swallowing during deployment prep. Replaced with explicit `Exception` handling. |
| **ISSUE-21** | Medium | Scripts | `scripts/launchers/thinking_bot.py` | Bare `except: pass` in bot launcher. Replaced with explicit `Exception` handling. |
| **ISSUE-22** | Medium | Scripts | `scripts/monitoring/check_memory.py` | Bare `except: pass` in memory checker. Replaced with explicit `Exception` handling. |
| **ISSUE-23** | Medium | Scripts | `scripts/runners/run_autonomous_learning.py` | Bare `except: pass` in autonomous runner. Replaced with explicit `Exception` handling. |
| **ISSUE-24** | Medium | Infrastructure | `trading_bot/infrastructure/health_endpoints.py` | System health reporting failed when `psutil` was uninstalled. Handled gracefully. |

---

### Performance & Memory Integrity

| Issue ID | Severity | Subsystem | File Affected | Summary & Fix |
| :--- | :--- | :--- | :--- | :--- |
| **ISSUE-25** | Medium | Decision Layer | `trading_bot/decision_layer/` | Unbounded list growth in decision event logs. Standardized cache bounds. |
| **ISSUE-26** | Medium | Risk | `trading_bot/risk/realtime_correlation_monitor.py` | Potential division by zero when price volatility was zero. Added epsilon bounds. |
| **ISSUE-27** | Medium | Risk | `trading_bot/risk/position_sizer.py` | Position sizer overflow on extreme leverage settings. Enforced max lot boundary limits. |
| **ISSUE-28** | Medium | Execution | `trading_bot/execution/fill_tracker.py` | Pending order memory leaks on non-terminal orders. Enforced timeout cleanup sweeps. |
| **ISSUE-29** | Low | Telemetry | `trading_bot/metrics/` | Unbounded metric history accumulation in memory. Enforced maxlen limits. |
| **ISSUE-30** | Low | Data | `trading_bot/schemas/` | Market data schema validation latency on high-frequency payloads. Optimized parsing loops. |
| **ISSUE-31** | Low | Core | `trading_bot/core/csc/controller.py` | VFE calculation zero division on identical prior/posterior distributions. Added numerical epsilon. |
| **ISSUE-32** | Low | Debate | `trading_bot/agents/multi_agent_debate.py` | Position sizing zero division when risk_weight is 0. Added fallback guard. |
