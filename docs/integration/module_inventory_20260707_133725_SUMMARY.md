# Module Inventory Summary

**Generated**: 2026-07-07T13:37:25.927480

## Overview

| Metric | Value |
|--------|-------|
| Total Modules | 7,991 |
| Total Lines of Code | 2,633,923 |
| Total Classes | 32,645 |
| Total Functions | 104,929 |
| Async Modules | 2,619 |
| Modules with Parse Errors | 128 |

## Domain Distribution

| Domain | Module Count | Lines of Code |
|--------|-------------|---------------|
| D01_data_infrastructure | 407 | 171,497 |
| D02_risk_management | 495 | 220,172 |
| D03_execution | 540 | 269,532 |
| D04_signal_generation | 575 | 285,842 |
| D05_ai_ml | 1,003 | 419,868 |
| D06_security_compliance | 88 | 41,987 |
| D07_infrastructure | 1,127 | 277,217 |
| D08_governance | 118 | 55,341 |
| D09_performance | 191 | 101,562 |
| D10_integration | 54 | 19,118 |
| D11_testing | 3,229 | 705,858 |
| D12_documentation | 164 | 65,929 |

## Hub Modules (Most Dependencies)

These modules are imported by many other modules and should be integrated first:

| Module | Dependent Count |
|--------|-----------------|
| `trading_bot` | 1163 |
| `trading_bot.core.service_registry` | 90 |
| `trading_bot.core.event_bus` | 55 |
| `unified_types` | 32 |
| `trading_bot.risk` | 29 |
| `layer_interfaces` | 27 |
| `trading_bot.orchestrator` | 24 |
| `trading_bot.execution` | 23 |
| `trading_bot.data` | 23 |
| `capital_governance` | 20 |
| `trading_bot.brokers.broker_adapter` | 19 |
| `market_intelligence_core` | 17 |
| `dash_bootstrap_components` | 16 |
| `trading_bot.brokers` | 15 |
| `strategy_genome` | 15 |
| `trading_bot.core.survival_core` | 14 |
| `trading_bot.config` | 14 |
| `trading_bot.brain` | 14 |
| `self_improvement` | 14 |
| `trading_bot.core_agent_system` | 13 |

## Modules with Parse Errors

These modules have syntax errors and need fixing:

| Module | Error |
|--------|-------|
| `broker/binance_broker.py` | SyntaxError: invalid syntax (<unknown>, line 20) |
| `broker/broker_interface.py` | SyntaxError: invalid syntax (<unknown>, line 18) |
| `broker/ib_broker.py` | SyntaxError: invalid syntax (<unknown>, line 19) |
| `compliance/compliance_monitor.py` | SyntaxError: invalid syntax (<unknown>, line 11) |
| `compliance/trade_surveillance.py` | SyntaxError: invalid syntax (<unknown>, line 12) |
| `examples/aamis_v3_demo.py` | SyntaxError: expected an indented block after 'for' statement on line 113 (<unkn... |
| `examples/adaptive_trading_demo.py` | SyntaxError: expected an indented block after function definition on line 40 (<u... |
| `examples/advanced_analysis_demo.py` | SyntaxError: unmatched ')' (<unknown>, line 303) |
| `examples/advanced_exit_strategies_demo.py` | SyntaxError: invalid syntax (<unknown>, line 25) |
| `examples/advanced_market_analysis_dashboard_demo.py` | SyntaxError: expected an indented block after function definition on line 46 (<u... |
| `examples/advanced_market_analysis_demo.py` | SyntaxError: invalid syntax (<unknown>, line 32) |
| `examples/advanced_systems_demo.py` | SyntaxError: expected an indented block after 'for' statement on line 41 (<unkno... |
| `examples/advanced_trading_example.py` | SyntaxError: expected an indented block after 'if' statement on line 81 (<unknow... |
| `examples/alpha_engine_demo.py` | SyntaxError: expected an indented block after 'for' statement on line 106 (<unkn... |
| `examples/alphaalgo_core_complete_demo.py` | SyntaxError: unmatched ')' (<unknown>, line 311) |
| `examples/alphaalgo_governance_demo.py` | SyntaxError: expected an indented block after 'for' statement on line 73 (<unkno... |
| `examples/alphaalgo_internet_demo.py` | SyntaxError: expected an indented block after 'try' statement on line 30 (<unkno... |
| `examples/alphaalgo_offline_rl_demo.py` | SyntaxError: invalid syntax (<unknown>, line 23) |
| `examples/autonomous_evolution_demo.py` | SyntaxError: invalid syntax (<unknown>, line 25) |
| `examples/autonomous_validation_demo.py` | SyntaxError: expected an indented block after 'if' statement on line 51 (<unknow... |

## Integration Priority

Based on dependency analysis, integrate modules in this order:

1. **Foundation** (no dependencies): Core utilities, constants, types
2. **Infrastructure**: Logging, configuration, health checks
3. **Data Layer**: Database, caching, data pipelines
4. **Domain Services**: Risk, execution, signals
5. **Business Logic**: Strategies, ML models, analysis
6. **Integration**: APIs, brokers, external adapters
7. **Orchestration**: Coordinators, schedulers
8. **Interface**: CLI, dashboard, notifications

## Next Steps

1. Review modules with parse errors and fix syntax issues
2. Start integration with hub modules (most dependencies)
3. Follow domain-by-domain integration approach
4. Verify all imports resolve correctly
5. Add missing tests and documentation
