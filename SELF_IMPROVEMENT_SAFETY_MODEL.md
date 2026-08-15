# Self-Improvement Safety Model (RSI-SAFETY-2026)

## 1. The Immutable Safety Kernel

The **Safety Kernel** represents the absolute non-modifiable core of the AlphaAlgo operating environment. No autonomous self-improvement loop, meta-optimizer, or model-generated code candidate can alter, delete, or bypass the rules and classes inside this boundary.

### Protected Configurations and Classes
The following systems are protected by read-only filesystem locks, strict checksum validation, and execution hooks:
1.  **ImmutableShield (`ImmutableShield`):** The final governance and transaction validation gateway.
2.  **RiskAuthority & Limits:** System-wide maximum daily loss, leverage caps, broker order confirmations, and maximum position size parameters.
3.  **Audit Logging System:** Logging to the SQLite `audit_log.db` and the totally ordered `LogAct` shared transaction log.
4.  **Human Approval and Protocol Hooks:** The verification gate code and deployment authentication keys.

### Security Escalation Policy
Any attempt by an autonomous improvement loop to modify these protected files or configurations results in:
```
[Self-Improvement Modification Attempt]
               │
               ▼
   [Safety Kernel Auditer] (Intercepts AST write)
               │
      ┌────────┴────────┐
      ▼                 ▼
[BLOCKED]       [SECURITY EVENT]
                        │
                        ▼
            [Emergency Engine Freeze]
                        │
                        ▼
            [Human Alarm / Email / SMS]
```

---

## 2. Experimental Isolation via `StrategySandbox`

To allow AlphaAlgo to safely innovate and evaluate candidate strategies, models, and features (under Tier 2 and Tier 3), we implement the **StrategySandbox** (`trading_bot/core/security/sandbox.py`). This sandbox provides robust process-level isolation:

### Sandbox Isolation Invariants
*   **Subprocess Spawning:** Code candidates are executed strictly inside disposable `multiprocessing.Process` instances.
*   **Zero Thread Leakage:** Threads cannot escape the sandbox process. Once execution concludes, the sandbox process is forcefully garbage-collected.
*   **SIGTERM Timeout Enforcement:** An AST-level check runs alongside a strict wall-clock timeout. If a candidate runs longer than **30 seconds** (or hogs CPU above limits), it is terminated via process-level SIGTERM signals.
*   **AST Security Filtering:** Prior to execution, the candidate's Abstract Syntax Tree (AST) is scanned recursively. The sandbox aggressively blocks any code containing:
    *   System command calls (`os.system`, `subprocess.Popen`, `shutil`).
    *   Dynamic code execution (`eval`, `exec`).
    *   Direct filesystem modifications outside the designated tmp directory.
    *   Raw serialization/unpickling (`pickle.load`, `shelve`).
    *   Network sockets or socket creation libraries (`socket.socket`, `urllib`, `requests` unless explicitly safe-listed).
