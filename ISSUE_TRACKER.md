# AlphaAlgo Production Audit - Issue Tracker

| Issue ID | Severity | Component | Description | Root Cause |
|---|---|---|---|---|
| ISSUE-001 | Critical | CSC | NameError: `FoldingOperator` is not defined in `controller.py`. | Reference to non-existent class (should be `InformationFolder`). |
| ISSUE-002 | Critical | HMS | Missing `json` import in `trading_bot/core/hms/memory.py`. | Incomplete import block. |
| ISSUE-003 | Critical | HMS | Missing `Tuple` import in `trading_bot/core/hms/memory.py`. | Incomplete import block. |
| ISSUE-004 | High | HMS | Redundant `__init__` methods in `HierarchicalMemorySystem`. | Duplicate code/Logic error in file merging. |
| ISSUE-005 | High | HMS | `self.tiers` used but not defined in `HierarchicalMemorySystem`. | Initialization failure/Missing attribute. |
| ISSUE-006 | Critical | Security | Unsafe `pickle.load` in `connectivity/cache_manager.py`. | Potential for arbitrary code execution. |
| ISSUE-007 | Critical | Security | Unsafe `pickle.loads` in `database/shared_memory_manager.py`. | Potential for arbitrary code execution. |
| ISSUE-008 | High | Intelligence | "Delusion Loop" in `self_play_loop.py` using `np.random` price changes. | Simulated environment not grounded in real data. |
| ISSUE-009 | Medium | Maintainability | Dead Code: `trading_bot/core/classa.py`. | Leftover boilerplate/unused file. |
| ISSUE-010 | Medium | Maintainability | Dead Code: `trading_bot/core/classb.py`. | Leftover boilerplate/unused file. |
| ISSUE-011 | Medium | Maintainability | Dead Code: `trading_bot/core/mytradingbot.py`. | Redundant orchestrator stub. |
| ISSUE-012 | Medium | Maintainability | Dead Code: `trading_bot/core/yourtradingbot.py`. | Redundant orchestrator stub. |
| ISSUE-013 | Medium | Maintainability | Dead Code: `trading_bot/core/testyourclass.py`. | Unused test/boilerplate file. |
| ISSUE-014 | High | Security | Unsafe `eval()` in `trading_bot/ml/ml_pipeline.py`. | Execution of arbitrary code from potentially unsafe strings. |
| ISSUE-015 | High | Reliability | `UnifiedDecisionBus` lacks timeouts in `asyncio.gather`. | Potential for dangling tasks or system hang on voter failure. |
| ISSUE-016 | Medium | Concurrency | Sync `__new__` in CSC uses `asyncio.Lock` improperly. | Logic error: `asyncio.Lock` cannot be used safely in sync `__new__`. |
| ISSUE-017 | High | Security | `os.system` used in `unified_approval/pipeline_approval.py`. | Command injection risk and lack of portability. |
| ISSUE-018 | Medium | Performance | Redundant graph saves in `HierarchicalMemorySystem.store_ledger_entry`. | Excessive I/O: Graph saved on every ledger entry. |
| ISSUE-019 | Low | Documentation | Mock strategic folding in `folding.py`. | Logic placeholder: Returns a static string. |
| ISSUE-020 | Medium | Performance | `MarketHostilityDetector.evaluate` uses non-vectorized list operations. | O(n) operations on history could be optimized with NumPy. |
| ISSUE-021 | High | Security | Unsafe `pickle` usage in `alpha_evolve/backtest_cache.py`. | Deserialization vulnerability. |
| ISSUE-022 | Medium | Data Integrity | Missing schema validation in HMS `_load_schema`. | Potential for corrupted memory state. |
| ISSUE-023 | Medium | Portability | Windows-only assumptions in `pipeline_approval.py`. | Hardcoded `cls` vs `clear` based on `os.name`. |
| ISSUE-024 | Low | Maintainability | Inconsistent Naming: `FoldingOperator` vs `InformationFolder`. | Architectural drift/Poor naming consistency. |
| ISSUE-025 | Medium | Reliability | `SAGEGraphMemory` uses `MultiDiGraph` but `HMS` initializes `DiGraph`. | Type mismatch in graph persistence. |
| ISSUE-026 | High | Intelligence | Random action fallback in `SelfPlayLoop` is too frequent. | Poor exploration strategy in self-play games. |
| ISSUE-027 | Medium | Security | `SecureCredentialVault` fallback to `.env` is insecure. | Credentials stored in plain text. |
| ISSUE-028 | High | Concurrency | Race condition in `SelfPlayLoop` experience buffer collection. | Thread-unsafe list appending during async games. |
| ISSUE-029 | Medium | Performance | Excessive allocations in `ConfidenceVector.min_confidence`. | Creating new dictionaries/lists on every call in hot path. |
| ISSUE-030 | High | Architecture | Architectural Fragmentation: Competing orchestrators in legacy directories. | "Three-Brain" problem: Multiple disconnected controllers. |
| ISSUE-031 | Critical | HMS | NameError: `Tuple` is not defined in `memory.py` (line 34). | Missing import. |
| ISSUE-032 | Critical | HMS | NameError: `json` is not defined in `memory.py` (line 37). | Missing import. |
| ISSUE-033 | Critical | HMS | NameError: `json` is not defined in `memory.py` (line 89). | Missing import. |
| ISSUE-034 | Critical | HMS | NameError: `json` is not defined in `memory.py` (line 144). | Missing import. |
| ISSUE-035 | High | HMS | Redundant `__init__` in `HierarchicalMemorySystem` overwrites `storage_root`. | Logic error: Second `__init__` wins, losing the first parameter. |
