# ISSUE TRACKER — Production Audit Logs

| ID | Title | Severity | Category | Impact | Status | Remediation File |
|---|---|---|---|---|---|---|
| **SEC-001** | Insecure `pickle` Deserialization | Critical | Security | RCE Risk | Resolved | `disaster_recovery.py` / `backup_recovery.py` |
| **SEC-002** | Unsafe `shell=True` in Subprocess Calls | High | Security | Shell injection | Resolved | `self_healing.py` / `continuous_orchestrator.py` |
| **SEC-003** | Hardcoded Mock Broker Credentials | High | Security | Password leak | Resolved | `tests/conftest.py` |
| **SEC-004** | Unsafe `eval()` in Simulation Orchestrator | High | Security | Code injection | Resolved | `simulation_orchestrator.py` |
| **SEC-005** | Weak Hashing / Insecure Randomness | Medium | Security | Predictable Salts | Resolved | `jwtauthenticator.py` |
| **REL-001** | Missing `AsyncMock` in `test_csc_v5.py` | High | Reliability | Test collection failures | Resolved | `tests/uca_v5/test_csc_v5.py` |
| **REL-002** | Schema Versioning AutoMem Optimization Gap | Medium | Reliability | Test failure on versioning | Resolved | `trading_bot/core/hms/memory.py` |
| **REL-003** | Incorrect HASP Volatility Nesting Check | High | Reliability | Safety bypass in high volatility| Resolved | `trading_bot/core/csc/controller.py` |
| **REL-004** | CoreDecision Missing `trade_id` Parameter | Critical | Reliability | Runtime pipeline crashes | Resolved | `trading_bot/core/alphaalgo_core_engine.py` |
| **REL-005** | Naked `except:` Blocks causing Silent Failures | Medium | Reliability | Hard-to-debug behaviors | Resolved | `trading_bot/core/survival_core.py` |
| **PERF-001** | Redundant Double LogAction Proposals | High | Performance | Log duplication & memory leak| Resolved | `trading_bot/core/csc/controller.py` |
| **PERF-002** | Missing PyTorch NN Fallback Stubs | High | Performance | Collection failure / import crash | Resolved | `dynamic_risk_matrix.py` |
| **PERF-003** | Repeated Model Loading on CPU/GPU | High | Performance | OOM risk under load | Resolved | `model_registry.py` |
| **ARCH-001** | Missing `event_bus.py` in `trading_bot/core` | Critical | Architecture | ModuleNotFoundError | Resolved | `trading_bot/core/event_bus.py` |
| **ARCH-002** | Competing Legacy Orchestrator Clutter | Medium | Architecture | Duplicate strategic orchestrators| Resolved | `_archive` purge |
| **ARCH-003** | Redundant Component Registry Registrations | Medium | Architecture | Memory leak & duplicate components| Resolved | `unified_registry.py` |
| **ARCH-004** | Duplicate Execution Loops in CSC Controller | High | Architecture | Split-brain consensus | Resolved | `trading_bot/core/csc/controller.py` |
| **INT-001** | "Delusion Loop" (RSI Random Drift) | Critical | Intelligence | Hallucinated Alpha signals | Resolved | `run_aletheia.py` / `validate.py` |
| **INT-002** | Simulated Superintelligence Stubs | High | Intelligence | Empty placeholders | Resolved | `autonomy_control_plane.py` |
| **INT-003** | Baseline Reasoning Branch Confidence set to 0.0 | High | Intelligence | Failed pivots / decision freeze | Resolved | `trading_bot/core/csc/hypothesis.py` |
| **CONC-001**| `wait_for_decision` Hang in Tests | Critical | Concurrency | Test suite hangs | Resolved | `tests/conftest.py` |
| **DATA-001**| Missing Schema Validation on Cache Miss | Medium | Data | Bad tick database corruption | Resolved | `data_manager.py` |
| **DATA-002**| Stale Level 2 Liquidity Orderbook | Medium | Data | Outdated orderbook depths | Resolved | `level2_manager.py` |
| **PROD-001**| Windows-only `mt5` Adapter Lock-in | High | Production | Inability to run on Unix hosts | Resolved | `mt5_connector.py` / `mt5_adapter.py` |
| **PROD-002**| Missing Config Field Validation | Medium | Production | Incomplete env configuration | Resolved | `config_validator.py` |
| **MAINT-001**| God Class `CognitiveSystemController` | Medium | Maintainability| Complexity exceeding 1500 LOC | Resolved | `folding.py` decoupling |
| **MAINT-002**| Excessive Print Statements | Low | Maintainability| Log pollution | Resolved | `logging` migration |
| **MAINT-003**| Obsolete Files in `_archive` | Medium | Maintainability| Large unused build artifacts | Resolved | Moved to `_archive` |
| **MAINT-004**| Magic Numbers in Volatility Thresholds | Medium | Maintainability| Hardcoded values in risk matrix | Resolved | `elite_config.yaml` |
| **MAINT-005**| Missing Docstrings in Core APIs | Low | Maintainability| Onboarding friction | Resolved | Core API Docstrings |
