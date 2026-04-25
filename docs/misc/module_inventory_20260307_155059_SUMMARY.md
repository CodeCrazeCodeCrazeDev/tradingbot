# Module Inventory Summary

**Generated**: 2026-03-07T15:50:59.569860

## Overview

| Metric | Value |
|--------|-------|
| Total Modules | 21,471 |
| Total Lines of Code | 8,947,501 |
| Total Classes | 93,371 |
| Total Functions | 263,081 |
| Async Modules | 6,448 |
| Modules with Parse Errors | 795 |

## Domain Distribution

| Domain | Module Count | Lines of Code |
|--------|-------------|---------------|
| D01_data_infrastructure | 1,759 | 764,814 |
| D02_risk_management | 2,007 | 1,014,593 |
| D03_execution | 2,355 | 1,259,559 |
| D04_signal_generation | 2,608 | 1,358,771 |
| D05_ai_ml | 3,651 | 1,527,961 |
| D06_security_compliance | 267 | 149,501 |
| D07_infrastructure | 3,293 | 1,098,675 |
| D08_governance | 295 | 153,323 |
| D09_performance | 759 | 400,268 |
| D10_integration | 151 | 71,914 |
| D11_testing | 3,939 | 1,002,969 |
| D12_documentation | 387 | 145,153 |

## Hub Modules (Most Dependencies)

These modules are imported by many other modules and should be integrated first:

| Module | Dependent Count |
|--------|-----------------|
| `trading_bot` | 1168 |
| `dash_bootstrap_components` | 135 |
| `trading_bot.brain.tier_structure` | 115 |
| `trading_bot.data` | 104 |
| `trading_bot.risk` | 104 |
| `event_monitor` | 95 |
| `trading_bot.ml.predictive_models` | 92 |
| `trading_bot.core.service_registry` | 88 |
| `trading_bot.strategy.strategy_engine` | 79 |
| `market_structure` | 78 |
| `trading_bot.brokers.broker_adapter` | 77 |
| `exit_strategy` | 75 |
| `trading_bot.data.market_data_stream` | 73 |
| `market_regime` | 68 |
| `trading_bot.execution` | 66 |
| `unified_types` | 64 |
| `trading_bot.analysis.market_structure` | 63 |
| `trading_bot.core.survival_core` | 60 |
| `trading_bot.analysis.sentiment_analyzer` | 59 |
| `trading_bot.execution.market_impact` | 56 |

## Modules with Parse Errors

These modules have syntax errors and need fixing:

| Module | Error |
|--------|-------|
| `autonomous_backups\20251208_175958\examples\autonomous_validation_demo.py` | SyntaxError: invalid syntax (<unknown>, line 31) |
| `autonomous_backups\20251208_175958\examples\internet_learning_demo.py` | SyntaxError: invalid syntax (<unknown>, line 14) |
| `autonomous_backups\20251208_175958\examples\level2_data_demo.py` | SyntaxError: unexpected indent (<unknown>, line 243) |
| `autonomous_backups\20251208_175958\examples\loss_learning_demo.py` | SyntaxError: invalid syntax (<unknown>, line 16) |
| `autonomous_backups\20251208_175958\examples\profit_ready_demo.py` | SyntaxError: unexpected indent (<unknown>, line 99) |
| `autonomous_backups\20251208_175958\examples\self_checklist_demo.py` | SyntaxError: invalid syntax (<unknown>, line 25) |
| `autonomous_backups\20251208_175958\tests\__init__.py` | SyntaxError: invalid syntax (<unknown>, line 49) |
| `autonomous_backups\20251208_175958\tests\integration\test_broker_integration.py` | SyntaxError: invalid syntax (<unknown>, line 32) |
| `autonomous_backups\20251208_175958\tests\test_broker_connection.py` | SyntaxError: unexpected indent (<unknown>, line 379) |
| `autonomous_backups\20251208_175958\tests\test_complete_system.py` | SyntaxError: unexpected indent (<unknown>, line 86) |
| `autonomous_backups\20251208_175958\tests\test_comprehensive_coverage.py` | SyntaxError: unexpected indent (<unknown>, line 217) |
| `autonomous_backups\20251208_175958\tests\test_comprehensive_e2e.py` | SyntaxError: unmatched ')' (<unknown>, line 858) |
| `autonomous_backups\20251208_175958\tests\test_error_handler.py` | SyntaxError: invalid syntax (<unknown>, line 7) |
| `autonomous_backups\20251208_175958\tests\test_internet_learning.py` | SyntaxError: invalid syntax (<unknown>, line 15) |
| `autonomous_backups\20251208_175958\tests\test_load_testing.py` | SyntaxError: unexpected indent (<unknown>, line 96) |
| `autonomous_backups\20251208_175958\tests\test_system_quick.py` | SyntaxError: unexpected indent (<unknown>, line 60) |
| `autonomous_backups\20251208_175958\trading_bot\adaptive_systems\code_generation\code_validator.py` | SyntaxError: unexpected indent (<unknown>, line 72) |
| `autonomous_backups\20251208_175958\trading_bot\ai_engineer\deepseek_integration.py` | SyntaxError: unexpected indent (<unknown>, line 376) |
| `autonomous_backups\20251208_175958\trading_bot\alerts\alert_system.py` | SyntaxError: unexpected indent (<unknown>, line 279) |
| `autonomous_backups\20251208_175958\trading_bot\alphaalgo_core\governance_system.py` | SyntaxError: unexpected indent (<unknown>, line 182) |

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
