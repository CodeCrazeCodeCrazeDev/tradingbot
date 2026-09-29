# SECURITY AUDIT - AlphaAlgo Production Engineering

This report documents the security audit findings, vulnerabilities, CWE classifications, exploitability metrics, and mitigation plans of the AlphaAlgo Quantitative Platform.

---

## 1. Vulnerability Findings

### 1.1. Unsafe Deserialization via Pickle
*   **CWE Classification:** `CWE-502` (Deserialization of Untrusted Data)
*   **Location:** `trading_bot/risk/correlation_persistence.py`
*   **Exploitability:** High (Attacker who writes to cache files can execute arbitrary code upon reload)
*   **Production Impact:** Critical (Full system takeover)
*   **Remediation:** Implement a centralized and authoritative `ArtifactManager` under `trading_bot/security/artifact_manager.py` that enforces non-executable JSON serialization for general operations, and restricts pickle to legacy scikit-learn models using HMAC signature validation, SHA-256 integrity, manifests, and the `RestrictedUnpickler` safelist utility.
*   **Current Status:** Remediation planned under Phase A.

### 1.2. Command Injection via Subprocess shell=True
*   **CWE Classification:** `CWE-78` (Improper Neutralization of Special Elements used in an OS Command)
*   **Location:** `trading_bot/core/security/sandbox.py`
*   **Exploitability:** High (Injecting shell meta-characters like `; rm -rf /` inside model parameter strings)
*   **Production Impact:** Critical (Data loss and host takeover)
*   **Remediation:** Remove all `shell=True` configurations, passing command lists directly as arguments to `subprocess.run` with `shell=False`.
*   **Current Status:** Remediation planned under Phase A.

### 1.3. Code Injection via Unsafe eval() Usage
*   **CWE Classification:** `CWE-95` (Improper Neutralization of Directive in Dynamically Evaluated Code)
*   **Location:** `trading_bot/core/security/sandbox.py`
*   **Exploitability:** High (Malicious models proposing arbitrary python code inside playbooks)
*   **Production Impact:** Critical (Arbitrary in-memory python execution)
*   **Remediation:** Completely deprecate and excise `eval()`. Use AST-level parsing checkers and static lookup maps for safe evaluations.
*   **Current Status:** Remediation planned under Phase A.

### 1.4. Path Traversal in File Writing
*   **CWE Classification:** `CWE-22` (Improper Limitation of a Pathname to a Restricted Directory)
*   **Location:** `trading_bot/core/hms/memory_os.py`
*   **Exploitability:** Medium (Writing files outside designated data directories using `../` segments)
*   **Production Impact:** High (System file overwrite / credential modification)
*   **Remediation:** Enforce strict, non-bypassable directory boundary validation on all file paths.
*   **Current Status:** Remediation planned under Phase A.

---

## 2. Secrets & Credential Management

*   **Audit Area:** API authentication and credential storage.
*   **Audit Finding:** Legacy files contain hardcoded API keys inside `config/` or `docker-compose.yml`.
*   **Remediation:** Force all secrets to be loaded strictly from system environment variables at runtime via `os.environ` or `.env` files. Enforce a repository-wide CI test blocking any hardcoded credentials.

---

*End of Security Audit.*
