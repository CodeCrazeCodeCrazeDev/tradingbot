# ISSUE TRACKER - POST-AUDIT

This document stands as the single, authoritative issue register tracking all verified technical issues, fully cross-referenced by Issue ID across all documents.

---

## 1. Verified Issue Register

### 1.1. Issue ID: SEC-001 (Unsafe Pickle Deserialization)
*   **Severity:** Critical
*   **Category:** Security
*   **Discovery Date:** June 15, 2026
*   **Discovery Method:** Code Audit (Bandit Static Analysis)
*   **Files Affected:** `trading_bot/risk/correlation_persistence.py`
*   **Functions Affected:** `load_correlation_matrix`
*   **Root Cause:** Directly invoking standard `pickle.load()` on file descriptors without integrity hashing, HMAC signatures, or class-level safelisting.
*   **Reproduction Procedure:**
    1.  Craft a malicious payload using `__reduce__` that invokes `os.system('id')`.
    2.  Write the serialized bytes to the temporary persistence cache file.
    3.  Trigger `load_correlation_matrix()`. The process will execute the crafted payload, showing user credentials.
*   **Technical Evidence:**
    ```python
    # Vulnerable implementation
    with open(filepath, 'rb') as f:
        matrix = pickle.load(f)  # Invokes arbitrary code execution
    ```
*   **Risk Assessment:**
    *   *Production Impact:* Critical (Potential host takeover and exposure of API keys).
    *   *Likelihood:* High (If persistence files reside in shared writable folders).
*   **Engineering Priority:** Critical (Must resolve before deploy).
*   **Architectural Dependency:** Standalone risk cache layer.
*   **Estimated Implementation Effort:** 4 hours.
*   **Recommended Solution:** Implement a centralized `ArtifactManager` utilizing AES-256 decryption, HMAC verification, and custom `RestrictedUnpickler` class safelists to completely block arbitrary command execution.
*   **Validation Plan:** Unit test `test_restricted_pickle` attempting to deserialize malicious payloads and verifying they are blocked with `UnpicklingError`.
*   **Current Status:** RESOLVED / VERIFIED.

### 1.2. Issue ID: SEC-002 (Command Injection via shell=True)
*   **Severity:** High
*   **Category:** Security
*   **Discovery Date:** June 16, 2026
*   **Discovery Method:** Semgrep Static Scanning
*   **Files Affected:** `trading_bot/core/security/sandbox.py`
*   **Functions Affected:** `execute_untrusted_workload`
*   **Root Cause:** Dynamic string composition passed directly to `subprocess.run(..., shell=True)`.
*   **Reproduction Procedure:**
    1.  Submit an execution package named `test; rm -rf /`.
    2.  Trigger sandboxed execution. The shell parses the semicolon and executes the injection.
*   **Technical Evidence:**
    ```python
    # Vulnerable implementation
    subprocess.run(f"python {filename}", shell=True)
    ```
*   **Risk Assessment:**
    *   *Production Impact:* Critical.
    *   *Likelihood:* Medium.
*   **Engineering Priority:** High.
*   **Architectural Dependency:** Secure Sandbox.
*   **Estimated Implementation Effort:** 2 hours.
*   **Recommended Solution:** Pass arguments strictly as lists to `subprocess.run` with `shell=False`.
*   **Validation Plan:** Unit test passing filenames with special bash meta-characters, verifying they are processed as literal arguments and not shell commands.
*   **Current Status:** RESOLVED.

### 1.3. Issue ID: ARCH-001 (Competing Orchestrators)
*   **Severity:** High
*   **Category:** Architecture
*   **Discovery Date:** June 18, 2026
*   **Discovery Method:** Repos-wide dependency scan
*   **Files Affected:** `trading_bot/orchestration/master_orchestrator.py`, `trading_bot/core/csc/controller.py`
*   **Root Cause:** Duplicate, split-brain orchestrator classes competing for event routing.
*   **Reproduction Procedure:**
    1.  Boot the application using both legacy master orchestrator and new Cognitive controller.
    2.  Observe duplicate order signals proposed to the event bus.
*   **Technical Evidence:** Two distinct files running parallel decision loops over the same market event streams.
*   **Risk Assessment:**
    *   *Production Impact:* High (Duplicate trades depleting capital).
    *   *Likelihood:* High.
*   **Engineering Priority:** Critical.
*   **Architectural Dependency:** Core Event Routing.
*   **Estimated Implementation Effort:** 8 hours.
*   **Recommended Solution:** Deprecate `master_orchestrator.py` authoritatively, enforcing `CognitiveSystemController` (CSC) as the single brain.
*   **Validation Plan:** Automated repository-wide architectural invariant tests checking for a single, unique orchestrator.
*   **Current Status:** RESOLVED.

### 1.4. Issue ID: PERF-001 (Blocking I/O in Async Context)
*   **Severity:** High
*   **Category:** Performance
*   **Discovery Date:** June 19, 2026
*   **Discovery Method:** Profiler Trace
*   **Files Affected:** `trading_bot/core/validation.py`
*   **Functions Affected:** `benchmark_latency`
*   **Root Cause:** Direct invocation of synchronous `time.sleep` blocking the main asyncio event thread.
*   **Reproduction Procedure:**
    1.  Run the validation suite.
    2.  Observe all concurrent tasks and message routing halting for the duration of the sleep.
*   **Technical Evidence:** Latency profiler shows $100\%$ CPU thread sleep-block.
*   **Risk Assessment:**
    *   *Production Impact:* High (SLA breaches and transaction timeouts).
    *   *Likelihood:* High.
*   **Engineering Priority:** High.
*   **Architectural Dependency:** Telemetry/Validation.
*   **Estimated Implementation Effort:** 1 hour.
*   **Recommended Solution:** Replace `time.sleep` with `asyncio.sleep()`.
*   **Validation Plan:** Concurrent latency benchmarks demonstrating non-blocking execution during sleep periods.
*   **Current Status:** RESOLVED / VERIFIED.

---

*End of Issue Tracker.*
