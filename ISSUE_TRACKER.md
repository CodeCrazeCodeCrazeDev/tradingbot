# ISSUE TRACKER

| ID | Title | Severity | Category | Impact | Status |
|---|---|---|---|---|---|
| SEC-001 | Unsafe `pickle` Deserialization | Critical | Security | RCE Risk | **RESOLVED** |
| SEC-002 | `shell=True` in Subprocess Calls | High | Security | Command Injection | **RESOLVED** |
| SEC-004 | Unsafe `eval()` Usage | High | Security | Code Injection | **RESOLVED** |
| REL-001 | Naked `except:` Blocks | Medium | Reliability | Silent Failures | **RESOLVED** |
| PERF-001 | Blocking I/O in Async Context | High | Performance | Loop Starvation | **RESOLVED** |
| ARCH-003 | Redundant Registry Implementations | Medium | Architecture | Split-Brain Decisions | **RESOLVED** |
| INT-001 | "Delusion Loop" (Random Simulation) | Critical | Intelligence | Hallucinated Alpha | **RESOLVED** |
| ML-001 | Lookahead Data Leakage | High | ML | Training Contamination | **RESOLVED** |

## Resolution Details

### SEC-001: Unsafe pickle Deserialization
- **Severity:** Critical
- **Root Cause:** Replay buffers, cache manager, memory systems, and correlation persistence used `pickle.loads()` on potentially ungrounded inputs.
- **Fix:** Switched cache management, sentiment core, and memory systems to strict, structured `json` serialization/deserialization. Added backward-compatible reading with strict validation.

### SEC-002: shell=True in Subprocess
- **Severity:** High
- **Root Cause:** System commands executed via shell strings, permitting command injection.
- **Fix:** Switched all subprocess calls to secure, list-based arguments without `shell=True`. Remediated `os.system` with list-based `subprocess.run` in approval pipelines.

### SEC-004: Unsafe eval() Usage
- **Severity:** High
- **Root Cause:** Dynamic indicator discovery evaluated arbitrary formulas using Python's raw `eval()`.
- **Fix:** Interfaced symbolic indicator discovery with the custom, AST-restricted `safe_eval()` compiler, prohibiting arbitrary code execution.

### REL-001: Naked except: Blocks
- **Severity:** Medium
- **Root Cause:** Silent exception suppression led to difficult debugging and diagnostic gaps.
- **Fix:** Identified and systematically refactored over 30 naked `except:` blocks across core systems to use specific exception catchers or `except Exception as e:`.

### PERF-001: Blocking I/O in Async
- **Severity:** High
- **Root Cause:** Standard blocking calls (like `time.sleep`) starred the asyncio event loop in evolutionary learning loops.
- **Fix:** Systematic conversion of blocking `time.sleep()` blocks to `await asyncio.sleep()` in asynchronous loops.

### ARCH-003: Redundant Registries
- **Severity:** Medium
- **Root Cause:** Coexistence of conflicting registry implementations caused fragmented service discovery.
- **Fix:** Consolidated all system component registration under the authoritative `UnifiedComponentRegistry` in `trading_bot/core/unified_registry.py`. Added AST architectural enforcement tests.

### INT-001: Delusion Loops
- **Severity:** Critical
- **Root Cause:** Adaptive and RL algorithms trained and promoted policies based on ungrounded/simulated or random rewards.
- **Fix:** Enforced strict `EvaluationState` validation. The system fails closed and refuses to calculate rewards, update parameters, or promote strategies unless real, grounded execution outcomes or historical backtests exist.

### ML-001: Lookahead Data Leakage
- **Severity:** High
- **Root Cause:** Feature engineering of technical indicators was vulnerable to future leakage via negative shifts.
- **Fix:** Performed lookahead audit. Established and verified that negative shifts are exclusively restricted to offline label construction and sliced off during inference.
