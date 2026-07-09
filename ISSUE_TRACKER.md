# ISSUE_TRACKER.md - AlphaAlgo Production Engineering Audit

This document tracks identified engineering issues within the AlphaAlgo codebase.

| Issue ID | Severity | Category | Root Cause | Files Affected |
| :--- | :--- | :--- | :--- | :--- |
| ISSUE-001 | High | Security | Use of `pickle` for model and data serialization. | `ml_pipeline.py`, `sentiment_core.py`, `liquidity_ml_predictor.py` |
| ISSUE-002 | Critical | Security | Unsafe use of `eval()` on potentially untrusted strings. | `ml_pipeline.py`, `self_evolving_intelligence.py` |
| ISSUE-003 | High | Security | Use of `shell=True` in `subprocess` calls. | `self_diagnosis_engine.py`, `recursive_self_improvement.py` |
| ISSUE-004 | High | Reliability | Reference to undefined `FoldingOperator` in CSC. | `trading_bot/core/csc/controller.py` |
| ISSUE-005 | Medium | Reliability | Uninitialized attributes (`step_counter`, `fold_interval`) in `InformationFolder`. | `trading_bot/core/csc/folding.py` |
| ISSUE-006 | Medium | Reliability | Logic errors in `InformationFolder.fold` (undefined variables). | `trading_bot/core/csc/folding.py` |
| ISSUE-007 | High | Architecture | Extreme fragmentation of Risk Management logic. | `trading_bot/risk/*` |
| ISSUE-008 | Medium | Architecture | Competing Event Bus implementations. | `trading_bot/core/unified_event_bus.py`, `trading_bot/core/event_bus.py` |
| ISSUE-009 | Low | Maintainability | God Class: `autonomy_control_plane.py` (142KB). | `trading_bot/core/autonomy_control_plane.py` |
| ISSUE-010 | Low | Security | Use of weak MD5 hashing for model identification. | `trading_bot/ml/ml_pipeline.py` |
| ISSUE-011 | Low | Performance | Inefficient dataframe copies in `FeatureStore`. | `trading_bot/ml/ml_pipeline.py` |
| ISSUE-012 | Medium | Architecture | Competing Orchestrators across different modules. | `trading_bot/aads/`, `trading_bot/hivemind/`, `trading_bot/orchestration/` |
| ISSUE-013 | Medium | Reliability | Singleton pattern implementation issues with `asyncio.Lock` in `__new__`. | `trading_bot/core/csc/controller.py` |
| ISSUE-014 | Low | Maintainability | Root-level `loguru.py` name clash with standard library/pip package. | `./loguru.py` |
| ISSUE-015 | Medium | Architecture | Multiple entry points causing configuration and execution confusion. | `main.py`, `thinking_bot.py`, `run_full_autonomous_system.py` |
| ISSUE-016 | Low | Data | Poor error handling for corrupted registry JSON. | `trading_bot/ml/ml_pipeline.py` |
| ISSUE-017 | Medium | ML | Overly simplistic model comparison logic in `RetrainingPipeline`. | `trading_bot/ml/ml_pipeline.py` |
| ISSUE-018 | Medium | Intelligence | Stubbed decision logic in `CognitiveSystemController`. | `trading_bot/core/csc/controller.py` |
| ISSUE-019 | Low | Documentation | Obsolete files and directories still present in the tree. | `_archive/`, redundant `test_*.py` in root |
| ISSUE-020 | High | Concurrency | Potential race conditions in `ModelRegistry` save/load if not atomic. | `trading_bot/ml/ml_pipeline.py` |
| ISSUE-021 | Medium | Architecture | Circular dependency risk in CSC trade proposal logic. | `trading_bot/core/csc/controller.py` |
| ISSUE-022 | Medium | Reliability | Missing scheduler cleanup in `RetrainingPipeline`. | `trading_bot/ml/ml_pipeline.py` |
| ISSUE-023 | Low | Production | Missing environment validation for Windows-only MT5 dependencies. | `trading_bot/data/mt5_interface.py` |
| ISSUE-024 | Low | Maintainability | Inconsistent naming conventions for Risk classes. | `trading_bot/risk/` |
| ISSUE-025 | Low | Performance | Blocking I/O in `ModelRegistry._save_registry`. | `trading_bot/ml/ml_pipeline.py` |
| ISSUE-026 | Medium | Architecture | Fragmented registries (Component Registry vs System Registry). | `trading_bot/core/unified_registry.py`, `trading_bot/system_registry.py` |
| ISSUE-027 | Low | ML | Missing validation for training data samples. | `trading_bot/ml/ml_pipeline.py` |
| ISSUE-028 | Medium | Reliability | `InformationFolder.fold_step` is async but `process_market_observation` calls it sync (it's not called yet, but likely intended). | `trading_bot/core/csc/folding.py` |
| ISSUE-029 | Medium | Security | Credential handling in `deploy.py` needs audit. | `deploy.py` |
| ISSUE-030 | High | Architecture | "One Brain" directive not fully enforced (multiple controllers exist). | `trading_bot/brain/`, `trading_bot/core/csc/` |
| ISSUE-031 | Medium | Concurrency | Lack of thread-safety in `UnifiedComponentRegistry` registrations. | `trading_bot/core/unified_registry.py` |
