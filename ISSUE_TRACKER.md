# ISSUE TRACKER

| ID | Title | Severity | Category | Impact | Status |
|---|---|---|---|---|---|
| SEC-001 | Unsafe `pickle` Deserialization | Critical | Security | RCE Risk | Resolved |
| SEC-002 | `shell=True` in Subprocess Calls | High | Security | Command Injection | Resolved |
| SEC-003 | Hardcoded Credentials | High | Security | Credential Leak | Resolved |
| REL-001 | Naked `except:` Blocks | Medium | Reliability | Silent Failures | Resolved |
| REL-002 | Infinite Loops without Exit Signals | Medium | Reliability | Zombie Processes | Resolved |
| PERF-001 | Blocking I/O in Async Context | High | Performance | Loop Starvation | Resolved |
| ARCH-001 | Competing Orchestrators | High | Architecture | Split-Brain Decisions | Resolved |
| ARCH-002 | Circular Dependency Workarounds | Medium | Architecture | Technical Debt | Resolved |
| INT-001 | "Delusion Loop" (Random Simulation) | Critical | Intelligence | Hallucinated Alpha | Resolved |
| MAINT-001 | "God Class" / Massive Files | Low | Maintainability | Hard to Audit | Resolved |
| MAINT-002 | Excessive Print Statements | Low | Maintainability | Log Pollution | Resolved |
| PROD-001 | Windows-only MT5 Lock-in | High | Production | Deployment Limit | Resolved |
| REL-003 | Missing Cleanup in Async Tasks | Medium | Reliability | Memory Leaks | Resolved |
| SEC-004 | Unsafe `eval()` Usage | High | Security | Code Injection | Resolved |
| ARCH-003 | Redundant Registry Implementations | Medium | Architecture | Confusion | Resolved |
| DATA-001 | Missing Schema Validation | Medium | Data | Corruption Risk | Resolved |
| PERF-002 | O(n^2) Data Processing Loops | Medium | Performance | Latency | Resolved |
| MAINT-003 | Duplicated Logic in `_archive` | High | Maintainability | Confusion | Resolved |
| INT-002 | Simulated Superintelligence Stubs | High | Intelligence | False Capability | Resolved |
| CONC-001 | Race Conditions in Event Bus | High | Concurrency | Data Loss | Resolved |
| SEC-005 | Weak Hashing / Insecure Randomness | Medium | Security | Crypto Risk | Resolved |
| REL-004 | Inconsistent Error Recovery | Medium | Reliability | System Instability | Resolved |
| PERF-003 | Redundant Model Loading | High | Performance | Memory Exhaustion | Resolved |
| ARCH-004 | Excessive Coupling in Core | High | Architecture | Rigidity | Resolved |
| MAINT-004 | Magic Numbers in Risk Models | Medium | Maintainability | Untunable | Resolved |
| DATA-002 | Stale Data in Cache | Medium | Data | Bad Decisions | Resolved |
| PROD-002 | Missing Configuration Validation | Medium | Production | Startup Failure | Resolved |
| REL-005 | Retry Failures in Network Calls | Medium | Reliability | Data Gaps | Resolved |
| ARCH-005 | God Module `trading_bot/core/__init__.py` | Medium | Architecture | Performance | Resolved |
| MAINT-005 | Missing Docstrings in Core APIs | Low | Maintainability | Onboarding | Resolved |

---

## Detailed Resolved Issue Reports

### SEC-001: Unsafe `pickle` Deserialization
* **Severity**: Critical
* **Root cause**: Use of standard `pickle.load` or `pickle.loads` on untrusted binary files which could trigger arbitrary bytecode execution.
* **Files affected**:
  - `trading_bot/analysis/sentiment_core.py`
  - `trading_bot/risk/correlation_persistence.py`
  - `trading_bot/ml/online_learning.py`
  - `trading_bot/ml/automl_pipeline.py`
  - `trading_bot/ai_core/mlops/model_registry.py`
* **Technical explanation**: Python's `pickle` protocol allows dynamic construction of Python object graphs using custom `__reduce__` methods, leading to potential remote code execution (RCE) if an attacker can manipulate files or cache streams.
* **Solution implemented**:
  - Entirely migrated non-model cache paths (sentiment history and correlation matrices) to pure JSON serialization (using dict-representation conversion).
  - Implemented `SafeUnpickler` class in `trading_bot/security/safe_pickle.py` which rejects class reconstruction for any module outside a safe whitelist of analytical primitives.
  - Replaced all other occurrences with `safe_load`.
* **Verification performed**: Validated JSON file structures and successfully executed unit tests to load and save states cleanly.
* **Remaining risks**: Some complex scikit-learn models or deep learning models still depend on safe deserialization whitelists during migration.
* **Future Recommendation**: Fully migrate scikit-learn artifacts to formats like ONNX, `skops.io`, or joblib with absolute file-level checksum verification (SHA-256 validation).

### SEC-002: `shell=True` in Subprocess Calls
* **Severity**: High
* **Root cause**: Use of `shell=True` in command executions which allows shell injection vulnerabilities when command components are parsed as shell metacharacters.
* **Files affected**:
  - `scripts/deploy.py`
  - `scripts/deployment/deploy.py`
  - `scripts/deployment/deploy_production.py`
* **Technical explanation**: Setting `shell=True` spawns an intermediate system shell (`/bin/sh` or `cmd.exe`) which processes the provided command string. If parts of the command are user-provided or externally influenced, attackers can inject arbitrary commands.
* **Solution implemented**: Refactored the `run_command` functions to use `shell=False` and parsed command strings into structured argument lists using `shlex.split`.
* **Verification performed**: Ran deployment scripts, verifying that commands compile and execute cleanly in sub-processes without requiring an intermediate shell.
* **Remaining risks**: Highly complex shell pipelines (using `|` or `>`) cannot be trivially split; they are not currently present in these modules.
* **Future Recommendation**: Construct all subprocess argument lists explicitly (e.g. as arrays of strings) and validate parameters rather than relying on string command inputs.

### REL-001: Naked `except:` Blocks
* **Severity**: Medium
* **Root cause**: Silent catching of standard exceptions, including system-level interrupts (like KeyboardInterrupt, SystemExit, GeneratorExit).
* **Files affected**:
  - `trading_bot/infrastructure/auto_scaling.py`
* **Technical explanation**: A naked `except:` statement catches *any* exception class, including `BaseException` subclasses. This silences Ctrl+C or graceful termination signals, leading to zombie processes and uncontrolled shutdown failures.
* **Solution implemented**: Replaced the naked `except:` block with `except Exception:` to only capture expected recoverable application-level failures while letting system-level signals propagate.
* **Verification performed**: Verified program execution and verified that KeyboardInterrupt safely terminates the scaling loops.
* **Remaining risks**: Other legacy directories might have hidden exceptions that are silent.
* **Future Recommendation**: Establish code quality rules (e.g. Ruff or Flake8) to automatically block any commits containing naked `except:` blocks.
