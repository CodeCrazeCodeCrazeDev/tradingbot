# Hypothesis Rejection Points

The following conditions and locations result in the rejection or retirement of a hypothesis:

| Subsystem | File Path | Trigger | Resulting State |
|-----------|-----------|---------|-----------------|
| **PHCE-D** | `trading_bot/phce_d/core_types.py` | `SkeletonKeyResult.DUMB_MATCHES` | `REJECTED` |
| **Gateway** | `trading_bot/phce_d/validation_gateway.py` | `is_rejected_for_leakage()` | `FAIL` (Rejected) |
| **Drift** | `trading_bot/phce_d/drift_monitor.py` | `DriftAction.SUSPEND_HYPOTHESIS` | `SUSPENDED` / `RETIRED` |
| **SRE** | `trading_bot/core_agent_system/scientific_reasoning/core.py` | `posterior < 0.2` | `REJECTED` |
| **SRE** | `trading_bot/core_agent_system/scientific_reasoning/core.py` | `RETIRED` | Authoritative End-States (Rejected/Deprecated) |
| **Risk** | `trading_bot/core/risk/circuit_breaker.py` | `CircuitBreakerTrigger` | `HOLD` (Temporary Rejection) |
| **Epistemology**| `trading_bot/core_agent_system/cds/epistemology_engine.py` | `adversarial_risk_score > 0.8` | `REJECTED` |
| **Research** | `trading_bot/_archive/alphaalgo_institutional/research_loop.py` | `failed_validation` | `REJECTED_CANDIDATE` |
| **Audit** | `trading_bot/phce_d/failure_memory.py` | Recurrence of known failure pattern. | `REJECTED` |
