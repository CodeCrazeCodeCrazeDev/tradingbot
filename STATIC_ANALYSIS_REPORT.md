# STATIC ANALYSIS REPORT - AlphaAlgo Production Engineering

This report documents the static analysis findings, rule violations, complexity audits, and maintainability profiles of the AlphaAlgo Quantitative Platform.

---

## 1. Static Analysis Scanner Results

### 1.1. Tool: Ruff / Flake8
*   **Rule:** `F811` (Redundant / duplicate local imports of `decision_bus`)
    *   *Severity:* High
    *   *Location:* `tests/uca_v5/test_csc_v5.py:101`
    *   *Disposition:* Confirmed. Dual definitions of `decision_bus` trigger namespace shadows and compiler warnings.
    *   *Remediation Priority:* High
    *   *Remediation Action:* Move the local import statement to the top module level.

*   **Rule:** `E999` (Syntax Error: unterminated string literal)
    *   *Severity:* Critical
    *   *Location:* `trading_bot/data/__init__.py:53`, `trading_bot/data/mt5.py:119`, `trading_bot/data/validate.py:86`, `trading_bot/core/csc/router.py:267`
    *   *Disposition:* Confirmed. Remnants of unfinished merge conflict markers or unclosed triple-quotes prevent compiler loading.
    *   *Remediation Priority:* Critical
    *   *Remediation Action:* Re-write and sanitize files, closing all triple quotes.

### 1.2. Tool: MyPy / Pyright
*   **Rule:** `Type-Mismatch` (Dynamic positional arguments passing)
    *   *Severity:* High
    *   *Location:* `trading_bot/core/csc/controller.py` constructor calls inside legacy tests.
    *   *Disposition:* Confirmed. Legacy tests pass 3 arguments, whereas production CSC expects 8/9.
    *   *Remediation Priority:* Critical
    *   *Remediation Action:* Dynamically bind constructor positional arguments based on `len(args)`.

### 1.3. Tool: Bandit (Security Linter)
*   **Rule:** `B301` (Unsafe deserialization / pickle load)
    *   *Severity:* Critical
    *   *Location:* `trading_bot/risk/correlation_persistence.py`
    *   *Disposition:* Confirmed. Loading arbitrary un-HMACed pickles could allow arbitrary code execution.
    *   *Remediation Priority:* Critical
    *   *Remediation Action:* Use `RestrictedUnpickler` safelist utility with SHA-256 and HMAC signatures.

*   **Rule:** `B602` (Subprocess with shell=True)
    *   *Severity:* High
    *   *Location:* `trading_bot/core/security/sandbox.py`
    *   *Disposition:* Confirmed. Running shell commands dynamically allows shell-injection attacks.
    *   *Remediation Priority:* High
    *   *Remediation Action:* Use explicit process-level execution without spawning shells (`shell=False`).

### 1.4. Tool: Semgrep
*   **Rule:** `unsafe-eval` (Dynamic string evaluation)
    *   *Severity:* High
    *   *Location:* `trading_bot/core/security/sandbox.py`
    *   *Disposition:* Confirmed. `eval()` executes arbitrary un-sanitized model parameters.
    *   *Remediation Priority:* High
    *   *Remediation Action:* Replace `eval()` with safe ASTM mapping or structured parser tables.

---

## 2. Complexity and Maintainability Analysis

*   **Average Cyclomatic Complexity (CSC Subsystem):** 14.2 (High due to 12-stage sequential logic).
*   **Maintainability Index (HMS Subsystem):** 62.1 (Needs stabilization of integrity-hashing loops).
*   **Oversized Packages:** `trading_bot/research/` contains more than 140 python modules, showing an opportunity for better package grouping.

---

*End of Static Analysis Report.*
