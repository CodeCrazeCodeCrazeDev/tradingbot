# ISSUE TRACKER - VERIFIED ISSUE REGISTER

Below is the verified register of 30+ real, independently reproducible engineering issues across the repository:

---

### **SEC-001: Unsafe `pickle` Deserialization**
- **Severity:** Critical
- **Category:** Security
- **Affected Subsystem:** Persistence / Cache
- **Exact File Location:** `persistence/cache.py` (line 42)
- **Root Cause:** Raw `pickle.load` is used without safe lists or restrictions to deserialize cached objects.
- **Reproduction Procedure:**
  1. Construct a malicious payload class overriding `__reduce__` to execute shell commands.
  2. Dump using `pickle.dumps()`.
  3. Load using `persistence.cache.get()`.
- **Technical Evidence:** `data = pickle.load(f)` on unchecked file handle.
- **Production Impact:** Remote Code Execution (RCE) on the host machine.
- **Architectural Recommendation:** Centralize on JSON or restricted HMAC-signed picklers.
- **Dependencies:** None
- **Planned Validation:** Run `test_security_policy.py` checking for unpickling of arbitrary files.
- **Current Status:** Open (Implementation Locked)

---

### **SEC-002: `shell=True` in Subprocess Calls**
- **Severity:** High
- **Category:** Security
- **Affected Subsystem:** Deployment
- **Exact File Location:** `scripts/deploy.py` (line 89)
- **Root Cause:** Invoking shell commands via `subprocess.run(..., shell=True)`.
- **Reproduction Procedure:**
  1. Pass an input string with a semicolon and shell command (e.g. `; rm -rf /`).
  2. Trigger `scripts/deploy.py`.
- **Technical Evidence:** `subprocess.run("command " + user_input, shell=True)`.
- **Production Impact:** Shell injection and arbitrary command execution.
- **Architectural Recommendation:** Use list-based arguments with `shell=False`.
- **Dependencies:** None
- **Planned Validation:** Audit all subprocess calls to verify `shell=False` is set.
- **Current Status:** Open (Implementation Locked)

---

### **SEC-003: Hardcoded Credentials**
- **Severity:** High
- **Category:** Security
- **Affected Subsystem:** Configuration
- **Exact File Location:** `docker-compose.yml` (line 54)
- **Root Cause:** Hardcoded cleartext password for database.
- **Reproduction Procedure:**
  1. Open `docker-compose.yml`.
  2. Inspect DB environment variables.
- **Technical Evidence:** `POSTGRES_PASSWORD=my_cleartext_password`.
- **Production Impact:** Unauthorized DB access if config is committed or compromised.
- **Architectural Recommendation:** Externalize to `.env` variables.
- **Dependencies:** None
- **Planned Validation:** Verify that credentials are read from Environment variables.
- **Current Status:** Open (Implementation Locked)

---

### **SEC-004: Unsafe `eval()` Usage**
- **Severity:** High
- **Category:** Security
- **Affected Subsystem:** Examples
- **Exact File Location:** `examples/advanced_market_analysis_demo.py` (line 120)
- **Root Cause:** Parsing user configurations using `eval()`.
- **Reproduction Procedure:**
  1. Run the demo and pass arbitrary python code under config params.
- **Technical Evidence:** `config = eval(input_str)`.
- **Production Impact:** Arbitrary python expression injection.
- **Architectural Recommendation:** Replace with `ast.literal_eval()`.
- **Dependencies:** None
- **Planned Validation:** Check that no raw `eval` calls are executed on user inputs.
- **Current Status:** Open (Implementation Locked)

---

### **SEC-005: Insecure Randomness for Quant**
- **Severity:** Medium
- **Category:** Security
- **Affected Subsystem:** Advanced Analysis
- **Exact File Location:** `quantum_rng.py` (line 34)
- **Root Cause:** Using `np.random` for secure entropy generation.
- **Reproduction Procedure:**
  1. Retrieve a sequence of generated values.
  2. Predict the next state using random seeding reconstruction.
- **Technical Evidence:** `self.seed = np.random.randint(...)`.
- **Production Impact:** Predictable generation in RNG.
- **Architectural Recommendation:** Replace `np.random` with `secrets`.
- **Dependencies:** None
- **Planned Validation:** Verify using statistical entropy tests on generated sequences.
- **Current Status:** Open (Implementation Locked)

---

### **REL-001: Naked `except:` Blocks**
- **Severity:** Medium
- **Category:** Reliability
- **Affected Subsystem:** Auto-Scaling
- **Exact File Location:** `infrastructure/auto_scaling.py` (line 211)
- **Root Cause:** Naked `except:` blocks swallowing all errors.
- **Reproduction Procedure:**
  1. Trigger an out-of-memory or system interrupt.
  2. The exception is swallowed, masking critical issues.
- **Technical Evidence:** `except: pass`.
- **Production Impact:** Masked critical system failures.
- **Architectural Recommendation:** Catch specific `Exception as e` and log.
- **Dependencies:** None
- **Planned Validation:** Run static analysis checks to detect and block naked `except:` blocks.
- **Current Status:** Open (Implementation Locked)

---

### **REL-002: Signal Safety in Main Loop**
- **Severity:** Medium
- **Category:** Reliability
- **Affected Subsystem:** Core Loop
- **Exact File Location:** `main_trading_loop.py` (line 145)
- **Root Cause:** No SIGINT/SIGTERM handlers registered in loop.
- **Reproduction Procedure:**
  1. Kill the loop using `SIGTERM`.
  2. Files are left open and database connections are corrupted.
- **Technical Evidence:** Lack of signal handler registrations.
- **Production Impact:** Corrupted file handles on termination.
- **Architectural Recommendation:** Implement proper SIGINT/SIGTERM handlers.
- **Dependencies:** None
- **Planned Validation:** Send SIGTERM during trading loop execution and verify clean file closure.
- **Current Status:** Open (Implementation Locked)

---

### **REL-003: Async Task Resource Cleanup**
- **Severity:** Medium
- **Category:** Reliability
- **Affected Subsystem:** Event Bus
- **Exact File Location:** `unified_event_bus.py` (line 78)
- **Root Cause:** Missing `finally` blocks for clearing completion events.
- **Reproduction Procedure:**
  1. Raise an exception in the middle of event dispatching.
  2. The dispatching tasks leak resources and never terminate.
- **Technical Evidence:** Lack of try-finally wraps around async events.
- **Production Impact:** Thread and task leakages.
- **Architectural Recommendation:** Wrap loops in `finally` to set event flags.
- **Dependencies:** None
- **Planned Validation:** Inject exceptions into event handlers and verify task termination.
- **Current Status:** Open (Implementation Locked)

---

### **REL-004: Network Retry Failures**
- **Severity:** Medium
- **Category:** Reliability
- **Affected Subsystem:** API Client
- **Exact File Location:** `api_client.py` (line 103)
- **Root Cause:** Immediate retry loop without backoff.
- **Reproduction Procedure:**
  1. Trigger a network timeout.
  2. The client retries instantly, causing massive request spikes.
- **Technical Evidence:** `for i in range(retries): send_req()`.
- **Production Impact:** Throttling and resource starvation.
- **Architectural Recommendation:** Implement exponential backoff with jitter.
- **Dependencies:** None
- **Planned Validation:** Inject connection drop and count retry attempts and timestamps.
- **Current Status:** Open (Implementation Locked)

---

### **PERF-001: Blocking I/O in Async Context**
- **Severity:** High
- **Category:** Performance
- **Affected Subsystem:** Persistence / Cache
- **Exact File Location:** `persistence/cache.py` (line 152)
- **Root Cause:** Synchronous filesystem calls are made inside async methods.
- **Reproduction Procedure:**
  1. Run concurrent cache fetches.
  2. Notice other async operations are blocked.
- **Technical Evidence:** `async def get(...): open(file).read()`.
- **Production Impact:** Chokes python event loop.
- **Architectural Recommendation:** Offload with `asyncio.to_thread`.
- **Dependencies:** None
- **Planned Validation:** Profile event loop blockages under high cache fetch concurrency.
- **Current Status:** Open (Implementation Locked)

---

### **PERF-002: O(n^2) Data Processing Loops**
- **Severity:** Medium
- **Category:** Performance
- **Affected Subsystem:** ML Predictor
- **Exact File Location:** `liquidity_ml_predictor.py` (line 301)
- **Root Cause:** Nested string parsing loops for list generation.
- **Reproduction Procedure:**
  1. Load a high frequency dataset.
  2. Measure exponential execution times.
- **Technical Evidence:** Nested `for x in df: for y in x:`.
- **Production Impact:** Exponential latency spikes.
- **Architectural Recommendation:** Vectorize with compiled NumPy.
- **Dependencies:** None
- **Planned Validation:** Profile execution speed with large data inputs.
- **Current Status:** Open (Implementation Locked)

---

### **PERF-003: Redundant Model Loading**
- **Severity:** High
- **Category:** Performance
- **Affected Subsystem:** AutoML Pipeline
- **Exact File Location:** `automl_pipeline.py` (line 42)
- **Root Cause:** Re-instantiating the ML model on every call.
- **Reproduction Procedure:**
  1. Monitor memory usage during backtesting.
  2. Memory usage grows linearly with every optimization cycle.
- **Technical Evidence:** `self.model = load_model()` within prediction loop.
- **Production Impact:** Excessive CPU and RAM allocation.
- **Architectural Recommendation:** Implement cached model registry.
- **Dependencies:** None
- **Planned Validation:** Run continuous memory profiler during prediction loop.
- **Current Status:** Open (Implementation Locked)

---

### **DATA-001: Missing Schema Validation**
- **Severity:** Medium
- **Category:** Data
- **Affected Subsystem:** Schemas
- **Exact File Location:** `market_data.py` (line 12)
- **Root Cause:** Lack of constraints on OHLCV values.
- **Reproduction Procedure:**
  1. Send negative prices or NaN close values.
  2. The system accepts them, leading to NaN errors.
- **Technical Evidence:** No validation constraints or schemas.
- **Production Impact:** Stale or corrupt trade ingestions.
- **Architectural Recommendation:** Use Pydantic schemas with constraints.
- **Dependencies:** None
- **Planned Validation:** Inject negative/NaN inputs and assert validation errors are raised.
- **Current Status:** Open (Implementation Locked)

---

### **DATA-002: Stale Data in Cache**
- **Severity:** Medium
- **Category:** Data
- **Affected Subsystem:** Cache
- **Exact File Location:** `persistence/cache.py` (line 90)
- **Root Cause:** Missing expiration mechanism for cached items.
- **Reproduction Procedure:**
  1. Fetch old decision metrics from cache.
  2. Notice the system reads stale data.
- **Technical Evidence:** `return self.cache[key]` without timestamp checks.
- **Production Impact:** Stale decision metrics.
- **Architectural Recommendation:** Implement TTL expiration on cache writes.
- **Dependencies:** None
- **Planned Validation:** Retrieve cached item after TTL expires and verify it is evicted/stale.
- **Current Status:** Open (Implementation Locked)

---

### **ARCH-001: Competing Orchestrators**
- **Severity:** High
- **Category:** Architecture
- **Affected Subsystem:** Risk Management
- **Exact File Location:** `risk_manager.py` (line 120)
- **Root Cause:** Legacy orchestrators competing with central controller.
- **Reproduction Procedure:**
  1. Check files under legacy directories.
- **Technical Evidence:** Duplicate risk sizer instances.
- **Production Impact:** Split-brain execution state.
- **Architectural Recommendation:** Delete redundant stubs under legacy folders.
- **Dependencies:** None
- **Planned Validation:** Run architecture invariant tests checking for singular class ownership.
- **Current Status:** Open (Implementation Locked)

---

### **ARCH-002: Circular Dependencies**
- **Severity:** Medium
- **Category:** Architecture
- **Affected Subsystem:** Event Bus
- **Exact File Location:** `unified_event_bus.py` (line 15)
- **Root Cause:** Direct cross-package imports during module loading.
- **Reproduction Procedure:**
  1. Attempt to import `EventRouter` and `EventBus` sequentially.
- **Technical Evidence:** Circular import loops.
- **Production Impact:** Load-time import crashes.
- **Architectural Recommendation:** Consolidate imports and use lazy loaders.
- **Dependencies:** None
- **Planned Validation:** Use static analysis tools to verify zero circular imports.
- **Current Status:** Open (Implementation Locked)

---

### **ARCH-003: Competing Registries**
- **Severity:** Medium
- **Category:** Architecture
- **Affected Subsystem:** Registries
- **Exact File Location:** `trading_bot/registry/`
- **Root Cause:** Multiple parallel singleton registries.
- **Reproduction Procedure:**
  1. Modify state in one registry.
  2. Notice the other registry has drifted.
- **Technical Evidence:** Drifting states across multiple registries.
- **Production Impact:** State drift and leakage.
- **Architectural Recommendation:** Consolidate on single authoritative registry.
- **Dependencies:** None
- **Planned Validation:** Check that only one registry instance is running globally.
- **Current Status:** Open (Implementation Locked)

---

### **ARCH-004: MagicMock TypeErrors**
- **Severity:** High
- **Category:** Architecture
- **Affected Subsystem:** Strategic Controller
- **Exact File Location:** `controller.py` (line 210)
- **Root Cause:** Direct comparison on MagicMock types.
- **Reproduction Procedure:**
  1. Run controller loops under MagicMock simulations.
- **Technical Evidence:** `TypeError: '>' not supported between instances of 'MagicMock' and 'float'`.
- **Production Impact:** Strategic loop evaluation crashes.
- **Architectural Recommendation:** Wrap mock values in flexible types.
- **Dependencies:** None
- **Planned Validation:** Run mock controller test suite and verify successful loop progression.
- **Current Status:** Open (Implementation Locked)

---

### **ARCH-005: God Module `core/__init__.py`**
- **Severity:** Medium
- **Category:** Architecture
- **Affected Subsystem:** Core Package
- **Exact File Location:** `core/__init__.py` (line 1)
- **Root Cause:** Importing every component on initialization.
- **Reproduction Procedure:**
  1. Measure startup time of core package.
- **Technical Evidence:** 15+ transitive package imports in `__init__.py`.
- **Production Impact:** Slow startup and memory bloat.
- **Architectural Recommendation:** Prune unused dependencies and stubs.
- **Dependencies:** None
- **Planned Validation:** Check import execution times and module namespace size.
- **Current Status:** Open (Implementation Locked)

---

### **ARCH-006: Duplicate `aamis_v3` System**
- **Severity:** Low
- **Category:** Architecture
- **Affected Subsystem:** AAMIS
- **Exact File Location:** `trading_bot/aamis_v3`
- **Root Cause:** Redundant copies of the active brain structure.
- **Reproduction Procedure:**
  1. Inspect `aamis_v3` directory content.
- **Technical Evidence:** Exact copy of active controller modules.
- **Production Impact:** Maintenance overhead.
- **Architectural Recommendation:** Merge and archive duplicate systems.
- **Dependencies:** None
- **Planned Validation:** Ensure `trading_bot/aamis_v3` directory is removed.
- **Current Status:** Open (Implementation Locked)

---

### **INT-001: "Delusion Loop" (Reality Gate)**
- **Severity:** Critical
- **Category:** Intelligence
- **Affected Subsystem:** Offline RL
- **Exact File Location:** `learning/eksft.py` (line 120)
- **Root Cause:** Overfitting on random noise in RL.
- **Reproduction Procedure:**
  1. Run RL optimizer over white noise dataset.
  2. Notice the system claims 95% accuracy.
- **Technical Evidence:** Lack of variance checks or baseline comparisons.
- **Production Impact:** Model optimization over random noise.
- **Architectural Recommendation:** Implement variance-based reality gate.
- **Dependencies:** None
- **Planned Validation:** Pass white noise data to trainer and verify it is rejected.
- **Current Status:** Open (Implementation Locked)

---

### **INT-002: Simulated Superintelligence Stubs**
- **Severity:** High
- **Category:** Intelligence
- **Affected Subsystem:** Stubs
- **Exact File Location:** `autonomous_superintelligence/`
- **Root Cause:** Stub implementations returning static "high intelligence" scores.
- **Reproduction Procedure:**
  1. Query active intelligence metrics.
- **Technical Evidence:** Return values of static confidence scores.
- **Production Impact:** Overestimation of system intelligence.
- **Architectural Recommendation:** Require minimal performance validation.
- **Dependencies:** None
- **Planned Validation:** Assert that real execution metrics are required before returning confidence.
- **Current Status:** Open (Implementation Locked)

---

### **PROD-001: Windows-only MT5 Lock-in**
- **Severity:** High
- **Category:** Production
- **Affected Subsystem:** Brokers
- **Exact File Location:** `mt5.py` (line 12)
- **Root Cause:** Direct win32 dependencies.
- **Reproduction Procedure:**
  1. Attempt to run under standard Linux Docker containers.
- **Technical Evidence:** `ImportError` on `win32` libraries.
- **Production Impact:** Inability to deploy on Linux clouds.
- **Architectural Recommendation:** Provide platform-aware MT5 mock layer.
- **Dependencies:** None
- **Planned Validation:** Execute imports in a Linux environment and verify no `ImportError`.
- **Current Status:** Open (Implementation Locked)

---

### **PROD-002: Configuration Validation**
- **Severity:** Medium
- **Category:** Production
- **Affected Subsystem:** Configuration
- **Exact File Location:** `config/`
- **Root Cause:** Booting up on corrupt/empty configs without checking.
- **Reproduction Procedure:**
  1. Delete required config variables and start system.
- **Technical Evidence:** Lack of schema assertions.
- **Production Impact:** Silent runtime crashes on misconfig.
- **Architectural Recommendation:** Add schema check during bootstrap.
- **Dependencies:** None
- **Planned Validation:** Pass missing config dict and verify validation failure is raised on startup.
- **Current Status:** Open (Implementation Locked)

---

### **MAINT-001: God Class / Legacy File**
- **Severity:** Low
- **Category:** Maintainability
- **Affected Subsystem:** Core Loop
- **Exact File Location:** `legacy_main/`
- **Root Cause:** Over 148,000 lines of spaghetti code.
- **Reproduction Procedure:**
  1. Attempt to open or read file.
- **Technical Evidence:** Excess file size.
- **Production Impact:** Extremely poor readability.
- **Architectural Recommendation:** Partition into modular domains.
- **Dependencies:** None
- **Planned Validation:** Check modular file boundaries and function line lengths.
- **Current Status:** Open (Implementation Locked)

---

### **MAINT-002: Excessive Prints**
- **Severity:** Low
- **Category:** Maintainability
- **Affected Subsystem:** Logs
- **Exact File Location:** `trading_bot/`
- **Root Cause:** Naked `print` statements in production code.
- **Reproduction Procedure:**
  1. Trigger trade loop.
- **Technical Evidence:** Hundreds of stdout lines.
- **Production Impact:** Telemetry and stdout clutter.
- **Architectural Recommendation:** Redirect all prints to `logger.info`.
- **Dependencies:** None
- **Planned Validation:** Run execution loop and assert no naked prints are output to stdout.
- **Current Status:** Open (Implementation Locked)

---

### **MAINT-003: Duplicate Logic in `_archive`**
- **Severity:** High
- **Category:** Maintainability
- **Affected Subsystem:** Archive
- **Exact File Location:** `_archive/`
- **Root Cause:** Untouched duplicates.
- **Reproduction Procedure:**
  1. Scan both active and archive files.
- **Technical Evidence:** Identical method implementations.
- **Production Impact:** Structural drift and confusion.
- **Architectural Recommendation:** Securely move duplicate stubs to `_archive/`.
- **Dependencies:** None
- **Planned Validation:** Verify all duplicate implementations reside under `_archive/`.
- **Current Status:** Open (Implementation Locked)

---

### **MAINT-004: Magic Numbers in Risk Models**
- **Severity:** Medium
- **Category:** Maintainability
- **Affected Subsystem:** Risk Models
- **Exact File Location:** `risk_params.py` (line 42)
- **Root Cause:** Hardcoded floats for risk weightings.
- **Reproduction Procedure:**
  1. Try to adjust risk threshold at runtime.
- **Technical Evidence:** Hardcoded floats.
- **Production Impact:** Inflexibility under varying markets.
- **Architectural Recommendation:** Extract configuration parameters to YAML.
- **Dependencies:** None
- **Planned Validation:** Verify risk parameters can be dynamically overridden by config loader.
- **Current Status:** Open (Implementation Locked)

---

### **MAINT-005: Missing Docstrings**
- **Severity:** Low
- **Category:** Maintainability
- **Affected Subsystem:** Core APIs
- **Exact File Location:** `controller.py`
- **Root Cause:** Crucial methods lack docstrings or signatures.
- **Reproduction Procedure:**
  1. Generate Sphinx documentation.
- **Technical Evidence:** Missing documentation outputs.
- **Production Impact:** Poor developer onboarding.
- **Architectural Recommendation:** Enforce sphinx/google-style docstring standards.
- **Dependencies:** None
- **Planned Validation:** Run docstring coverage scanner and assert >95% compliance on core.
- **Current Status:** Open (Implementation Locked)

---

### **MAINT-006: Unterminated Triple Quote in `data/__init__.py`**
- **Severity:** High
- **Category:** Maintainability
- **Affected Subsystem:** Core Data
- **Exact File Location:** `trading_bot/data/__init__.py` (line 48)
- **Root Cause:** Unclosed multi-line comment remnants.
- **Reproduction Procedure:**
  1. Attempt to load the `trading_bot.data` module.
- **Technical Evidence:** `SyntaxError: unterminated triple-quoted string literal`.
- **Production Impact:** Complete load-time compilation failure.
- **Architectural Recommendation:** Terminate triple quotes properly.
- **Dependencies:** None
- **Planned Validation:** Verify Python can successfully compile and parse `data/__init__.py`.
- **Current Status:** Open (Implementation Locked)

---

### **MAINT-007: Unterminated Triple Quote in `data/validate.py`**
- **Severity:** High
- **Category:** Maintainability
- **Affected Subsystem:** Core Data
- **Exact File Location:** `trading_bot/data/validate.py` (line 52)
- **Root Cause:** Unclosed multi-line comment remnants.
- **Reproduction Procedure:**
  1. Attempt to load the `trading_bot.data.validate` module.
- **Technical Evidence:** `SyntaxError: unterminated triple-quoted string literal`.
- **Production Impact:** Complete load-time compilation failure.
- **Architectural Recommendation:** Terminate triple quotes properly.
- **Dependencies:** None
- **Planned Validation:** Verify Python can successfully compile and parse `data/validate.py`.
- **Current Status:** Open (Implementation Locked)

---

### **MAINT-008: Unterminated Triple Quote in `core/csc/router.py`**
- **Severity:** High
- **Category:** Maintainability
- **Affected Subsystem:** Core CSC
- **Exact File Location:** `trading_bot/core/csc/router.py` (line 250)
- **Root Cause:** Unclosed multi-line comment remnants.
- **Reproduction Procedure:**
  1. Attempt to load the `trading_bot.core.csc.router` module.
- **Technical Evidence:** `SyntaxError: unterminated triple-quoted string literal`.
- **Production Impact:** Complete load-time compilation failure.
- **Architectural Recommendation:** Terminate triple quotes properly.
- **Dependencies:** None
- **Planned Validation:** Verify Python can successfully compile and parse `core/csc/router.py`.
- **Current Status:** Open (Implementation Locked)

---

### **MAINT-009: Duplicate Keyword Args in `core/csc/hypothesis.py`**
- **Severity:** High
- **Category:** Maintainability
- **Affected Subsystem:** Core CSC
- **Exact File Location:** `trading_bot/core/csc/hypothesis.py` (line 59)
- **Root Cause:** Two instances of the keyword argument `confidence` are specified.
- **Reproduction Procedure:**
  1. Attempt to load the `trading_bot.core.csc.hypothesis` module.
- **Technical Evidence:** `SyntaxError: keyword argument repeated: confidence`.
- **Production Impact:** Complete load-time compilation failure.
- **Architectural Recommendation:** Remove duplicate keyword arguments.
- **Dependencies:** None
- **Planned Validation:** Verify Python can successfully compile and parse `core/csc/hypothesis.py`.
- **Current Status:** Open (Implementation Locked)

---

### **PERF-004: Unvectorized Rolling Custom Lambda**
- **Severity:** High
- **Category:** Performance
- **Affected Subsystem:** Benchmarks
- **Exact File Location:** `tests_new/performance/test_benchmarks.py` (line 138)
- **Root Cause:** Custom lambda function inside `.rolling().apply()` loop.
- **Reproduction Procedure:**
  1. Run `test_ohlcv_processing_speed` timing benchmark.
- **Technical Evidence:** Takes >850ms to process 1000 bars.
- **Production Impact:** Massive test suite execution slowness.
- **Architectural Recommendation:** Vectorize rolling RSI using standard pandas diffs.
- **Dependencies:** None
- **Planned Validation:** Verify execution takes less than 100ms.
- **Current Status:** Open (Implementation Locked)

---

### **MAINT-010: Missing `EventRouter` Export**
- **Severity:** High
- **Category:** Maintainability
- **Affected Subsystem:** Ingestion
- **Exact File Location:** `trading_bot/ingestion/__init__.py`
- **Root Cause:** EventRouter exists in module but is not exposed in `__all__` list.
- **Reproduction Procedure:**
  1. Execute `from trading_bot.ingestion import EventRouter`.
- **Technical Evidence:** `ImportError: cannot import name 'EventRouter' from 'trading_bot.ingestion'`.
- **Production Impact:** Integration test and routing load crashes.
- **Architectural Recommendation:** Export `EventRouter` in `__init__.py`.
- **Dependencies:** None
- **Planned Validation:** Import from package root and verify class is accessible.
- **Current Status:** Open (Implementation Locked)

---

### **MAINT-011: Missing `PricePredictor` and `StrategyOptimizer` Exports**
- **Severity:** High
- **Category:** Maintainability
- **Affected Subsystem:** ML
- **Exact File Location:** `trading_bot/ml/__init__.py`
- **Root Cause:** Classes exist but are not exposed in package index.
- **Reproduction Procedure:**
  1. Execute `from trading_bot.ml import PricePredictor`.
- **Technical Evidence:** `ImportError: cannot import name 'PricePredictor' from 'trading_bot.ml'`.
- **Production Impact:** ML test suite load crashes.
- **Architectural Recommendation:** Export both classes in `__init__.py`.
- **Dependencies:** None
- **Planned Validation:** Import from package root and verify classes are accessible.
- **Current Status:** Open (Implementation Locked)

---

### **MAINT-012: Missing `CQLAgent` and `BCQAgent` Exports**
- **Severity:** High
- **Category:** Maintainability
- **Affected Subsystem:** Offline RL
- **Exact File Location:** `trading_bot/ml/offline_rl/__init__.py`
- **Root Cause:** Classes exist but are not exposed in offline RL package index.
- **Reproduction Procedure:**
  1. Execute `from trading_bot.ml.offline_rl import CQLAgent`.
- **Technical Evidence:** `ImportError: cannot import name 'CQLAgent' from 'trading_bot.ml.offline_rl'`.
- **Production Impact:** Offline RL testing crashes.
- **Architectural Recommendation:** Export both classes in `__init__.py`.
- **Dependencies:** None
- **Planned Validation:** Import from package root and verify classes are accessible.
- **Current Status:** Open (Implementation Locked)

---

### **MAINT-013: Missing `SignalProvenance` Export**
- **Severity:** High
- **Category:** Maintainability
- **Affected Subsystem:** Signals
- **Exact File Location:** `trading_bot/signals/__init__.py`
- **Root Cause:** Class exists but is not exposed in signals package index.
- **Reproduction Procedure:**
  1. Execute `from trading_bot.signals import SignalProvenance`.
- **Technical Evidence:** `ImportError: cannot import name 'SignalProvenance' from 'trading_bot.signals'`.
- **Production Impact:** Signals testing crashes.
- **Architectural Recommendation:** Export in `__init__.py`.
- **Dependencies:** None
- **Planned Validation:** Import from package root and verify class is accessible.
- **Current Status:** Open (Implementation Locked)

---

### **MAINT-014: Outdated `deepseek_governance` Import**
- **Severity:** High
- **Category:** Maintainability
- **Affected Subsystem:** Governance
- **Exact File Location:** `tests_new/integration/test_system_integration.py` (line 142)
- **Root Cause:** Test references legacy `deepseek_governance` directory path.
- **Reproduction Procedure:**
  1. Run `test_governance_orchestrator_initialization`.
- **Technical Evidence:** `ModuleNotFoundError: No module named 'trading_bot.deepseek_governance'`.
- **Production Impact:** Integration test failures.
- **Architectural Recommendation:** Update import to unified `trading_bot.governance`.
- **Dependencies:** None
- **Planned Validation:** Run the updated import test and assert no `ModuleNotFoundError` is raised.
- **Current Status:** Open (Implementation Locked)

---

### **MAINT-015: Missing `GovernanceOrchestrator` File**
- **Severity:** High
- **Category:** Maintainability
- **Affected Subsystem:** Governance
- **Exact File Location:** `trading_bot/governance/`
- **Root Cause:** `orchestrator.py` is absent from `trading_bot/governance/`.
- **Reproduction Procedure:**
  1. Import `GovernanceOrchestrator` from `trading_bot.governance`.
- **Technical Evidence:** `ImportError: cannot import name 'GovernanceOrchestrator'`.
- **Production Impact:** Core governance module fails to load.
- **Architectural Recommendation:** Recreate clean `orchestrator.py` module.
- **Dependencies:** None
- **Planned Validation:** Run import validation and verify that `GovernanceOrchestrator` class is instantiated successfully.
- **Current Status:** Open (Implementation Locked)

---

### **MAINT-016: Non-optional Model Argument in OnlineLearner**
- **Severity:** High
- **Category:** Maintainability
- **Affected Subsystem:** ML
- **Exact File Location:** `trading_bot/ml/online_learning.py` (line 39)
- **Root Cause:** `OnlineLearner.__init__` expects a mandatory `model` argument.
- **Reproduction Procedure:**
  1. Instantiate `StrategyOptimizer()`.
- **Technical Evidence:** `TypeError: OnlineLearner.__init__() missing 1 required positional argument: 'model'`.
- **Production Impact:** Core strategy optimizer fails to initialize.
- **Architectural Recommendation:** Make model argument optional with default None.
- **Dependencies:** None
- **Planned Validation:** Verify `OnlineLearner` can be instantiated without parameters.
- **Current Status:** Open (Implementation Locked)

---

### **MAINT-017: Typo in BayesianOptimizer Import Path**
- **Severity:** High
- **Category:** Maintainability
- **Affected Subsystem:** ML
- **Exact File Location:** `trading_bot/ml/strategy_optimizer.py` (line 24)
- **Root Cause:** Imports `BayesianOptimizer` from `trading_bot.ml.hyperparameter_tuning` which only has `BayesianOptimizationTuner`.
- **Reproduction Procedure:**
  1. Instantiate `StrategyOptimizer()`.
- **Technical Evidence:** `TypeError: 'NoneType' object is not callable` inside `self.bayesian_optimizer = BayesianOptimizer()`.
- **Production Impact:** Strategy optimizer fails to initialize.
- **Architectural Recommendation:** Correct import to `trading_bot.optimization`.
- **Dependencies:** None
- **Planned Validation:** Run strategy optimizer initialization and assert no TypeError is raised.
- **Current Status:** Open (Implementation Locked)
