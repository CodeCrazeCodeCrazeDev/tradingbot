# AlphaAlgo Production Issue Tracker (2026)

| Issue ID | Category | Severity | File Affected | Technical Description | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ISSUE-001** | Syntax / Reliability | **Critical** | `risk/risk_manager.py` | Invalid syntax when unpacking list comprehensions in report string formatting. | **RESOLVED** |
| **ISSUE-002** | Syntax / Reliability | **High** | `scripts/fixes/auto_fix_critical_issues_v2.py` | Indentation error on logger initialization crashing execution. | **RESOLVED** |
| **ISSUE-003** | Syntax / Reliability | **High** | `scripts/deployment/deploy_5star_production.py` | Indentation error in `run_trading_loop` and `try/except` loop block. | **RESOLVED** |
| **ISSUE-004** | Syntax / Reliability | **High** | `scripts/launchers/run_alphaalgo_5star.py` | Misaligned DataFrame initialization code block. | **RESOLVED** |
| **ISSUE-005** | Concurrency | **High** | `trading_bot/core/validation.py` | Blocking `time.sleep` called inside async `benchmark_latency`. | **RESOLVED** |
| **ISSUE-006** | Concurrency | **Medium** | `trading_bot/neuros_evolution/plotcode_integration.py` | Blocking `time.sleep` calls inside async UI simulation routines. | **RESOLVED** |
| **ISSUE-007** | Security | **High** | `trading_bot/distributed/parallel_backtester.py` | Dynamic `exec` execution of backtest strategy code without AST validation. | **RESOLVED** |
| **ISSUE-008** | Reliability / Math | **High** | `trading_bot/agents/multi_agent_debate.py` | Division-by-zero risk in `HeadAI._calculate_position_size` when `risk_weight` is zero. | **RESOLVED** |
| **ISSUE-009** | Testing / Test Suite | **Medium** | `tests/test_superior_architecture_minimal.py` | Dunder attribute lookups on `MockObj` causing Hypothesis test collection errors. | **RESOLVED** |
| **ISSUE-010** | Error Handling | **Medium** | `trading_bot/core/hms/memory.py` | Silent bare except clause in `reset()` schema saving. | **RESOLVED** |
| **ISSUE-011** | Error Handling | **Medium** | `trading_bot/core/hms/memory_os.py` | Bare except in `copy_dict` swallowing unexpected dictionary conversion errors. | **RESOLVED** |
