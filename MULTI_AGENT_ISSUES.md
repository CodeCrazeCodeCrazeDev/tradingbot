# Multi-Agent Issue Tracker & Technical Debt Register

## Verified Technical Debt & Remediation Log

### Issue ID: MA-01 (Severity: Critical)
- **Reproduction:** Running the `test_deterministic_replay.py` test suite failed with a `NameError: name 'final_qty' is not defined`.
- **Evidence:** `E  NameError: name 'final_qty' is not defined` inside `CognitiveSystemController._select_optimal_action`.
- **Root Cause:** A refactoring step did not define `final_qty` prior to calling `max(0.01, final_qty)`.
- **Affected Files:** `trading_bot/core/csc/controller.py`
- **Production Impact:** Any downstream trading signal produced by the CSC was subject to immediate runtime crashes.
- **Fix:** Correctly calculated `final_qty = base_qty * slippage_penalty` before performing safety-bounds capping.
- **Validation:** Both `test_deterministic_replay.py` and `test_multi_agent_debate_fix.py` now pass perfectly.
- **Regression Result:** None. Fully stabilized.

### Issue ID: MA-02 (Severity: High)
- **Reproduction:** Attempting to reset UCA singletons in test setup triggered `AttributeError: type object 'UnifiedDecisionBus' has no attribute 'reset'`.
- **Evidence:** Test setup failed to isolate tests.
- **Root Cause:** Standard classmethods for resetting singletons between test runs were absent, leading to test-to-test pollution and database locks.
- **Affected Files:** `trading_bot/core/unified_event_bus.py`, `trading_bot/core/csc/controller.py`, `trading_bot/core/hms/memory.py`
- **Fix:** Implemented safe, deterministic `reset()` classmethods that completely clear state and reset singletons without recursive import side-effects.
- **Validation:** Singleton isolation tests pass 100%.

### Issue ID: MA-03 (Severity: Moderate)
- **Reproduction:** Importing `trading_bot.agents.multi_agent_debate` raised module loading collisions.
- **Evidence:** Multiple declarations of `AgentScorecard` in `multi_agent_debate.py`.
- **Root Cause:** Merge conflicts created three identical duplicate class declarations.
- **Affected Files:** `trading_bot/agents/multi_agent_debate.py`
- **Fix:** Consolidated definitions into one unified, strongly typed class with `to_dict()` support.
- **Validation:** Imports compile in 0.0s without warnings.
