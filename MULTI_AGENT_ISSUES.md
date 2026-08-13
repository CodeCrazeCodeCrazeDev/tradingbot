# Multi-Agent Debate System Issue Registry

## Issue Registry

### Issue MA-001: Redundant Class Definitions & Signature Contamination
- **Severity**: P1 (Architectural Correctness)
- **Evidence**: `AgentScorecard` and `RiskVerifier` declared multiple times inside `multi_agent_debate.py`.
- **Affected Files**: `trading_bot/agents/multi_agent_debate.py`
- **Root Cause**: Uncoordinated merges of legacy files with modern V6 architectures.
- **Fix**: Merged all class declarations into single, clean, robust authoritative definitions.
- **Validation**: Programmatic imports, code compilation, and pytest runs are fully successful.

### Issue MA-002: Uninitialized 'vetoes' List Variable NameError
- **Severity**: P1 (Runtime Correctness)
- **Evidence**: NameError raised when attempting to append vetoes in `synthesize_decision` under risk-veto conditions.
- **Affected Files**: `trading_bot/agents/multi_agent_debate.py`
- **Root Cause**: Referencing the variable `vetoes` without declaration or initialization.
- **Fix**: Initialized `vetoes = []` cleanly at the top of the try-block and appended active veto details to final trade reasoning.
- **Validation**: Enforced via `test_byzantine_contradictory_evidence` and `test_silent_non_responsive_agents_and_degradation`.

### Issue MA-003: Lack of Input Integrity/Risk Context Checks
- **Severity**: P0 (Financial Safety Boundary)
- **Evidence**: Extremely high exposures or negative volatility inputs could bypass safety checks and result in active trading proposals.
- **Affected Files**: `trading_bot/agents/multi_agent_debate.py`
- **Root Cause**: Missing proactive safety validators inside the `debate` entry point.
- **Fix**: Implemented strict, proactive guardrails validating negative volatility, out-of-bounds exposure (>1.0), and invalid correlation risks, raising fail-closed `NO_TRADE` immediately.
- **Validation**: Enforced via a brand new adversarial unit test: `test_market_context_integrity_validation`.
