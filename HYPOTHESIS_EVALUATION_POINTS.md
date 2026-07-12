# Hypothesis Evaluation Points

Hypotheses are evaluated at various stages and depths across the system:

| Subsystem | File Path | Method | Criteria |
|-----------|-----------|--------|----------|
| **PHCE-D** | `trading_bot/phce_d/verifier.py` | `verify_hypothesis()` | Sharpe, edge after cost, sign consistency. |
| **CDS** | `trading_bot/core_agent_system/cds/epistemology_engine.py` | `analyze_hypothesis()` | Belief score, uncertainty, adversarial risk. |
| **Gateway** | `trading_bot/phce_d/validation_gateway.py` | `validate_hypothesis()` | Lineage leakage, freshness, circuit breakers. |
| **SRE** | `trading_bot/core_agent_system/scientific_reasoning/core.py` | `evaluate_results()` | Statistical significance, Bayesian posterior. |
| **Scenario** | `trading_bot/phce_d/scenario_conditioner.py` | `evaluate_scenarios()` | Applicability score, discrimination improvement. |
| **Risk** | `trading_bot/core/risk/unified_risk_manager.py` | `assess_risk()` | VaR, CVaR, Kelly sizing constraints. |
| **Adversarial** | `trading_bot/phce_d/adversarial_stress_test.py` | `stress_test()` | Performance under regime shift/hostile conditions. |
| **Compliance** | `trading_bot/compliance/policy_enforcer.py` | `check_compliance()` | Institutional constraints, regulatory alignment. |
| **Drift** | `trading_bot/phce_d/drift_monitor.py` | `assess_drift()` | Feature drift, expected vs realized edge. |
