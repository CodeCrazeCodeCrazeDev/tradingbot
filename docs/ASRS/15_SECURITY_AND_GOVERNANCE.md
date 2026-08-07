# 15. SECURITY AND GOVERNANCE
## Security Verification, Sandboxing Boundaries & Governance Framework

### 1. Document Overview
This document specifies the security controls, governance policies, and operational guardrails of the **Institutional AI-for-AI Research System (ASRS)**.

Because ASRS operates as a self-improving platform with programmatic access to code modification, robust boundaries must be strictly enforced. **Under no circumstances is code allowed to modify live, production trading environments without passing through isolated validation sandboxes and independent reviews.**

---

### 2. Physical Sandboxing & Code Isolation

#### Sandboxing Architecture
The system isolates execution and development through three discrete boundaries (Level 1, Level 2, and Level 3):

```text
  +---------------------------------------------------------------------------------+
  |                             ASRS ISOLATION WRAPPERS                             |
  +---------------------------------------------------------------------------------+
  |                                                                                 |
  |  [L1 Isolation (Prompt/Config)]                                                 |
  |  - Change loaded exclusively in localized RAM.                                  |
  |  - No permission to access file writing APIs.                                   |
  |                                                                                 |
  |  [L2 Isolation (Local File Workspace)]                                          |
  |  - Code is written inside temporary directories (e.g., /tmp/asrs-L2/).          |
  |  - Read-only symlinks to AlphaAlgo core packages.                               |
  |  - Subprocess execution wrapped in restricted OS profiles (e.g., AppArmor,     |
  |    systemd-nspawn, or chroot) with network access completely disabled.          |
  |                                                                                 |
  |  [L3 Isolation (Version Control & Containers)]                                  |
  |  - Programmatic git checkout inside a dedicated worktree folder.                |
  |  - Tests executed inside isolated Docker container sandboxes.                   |
  |  - Resource limits (CPU cores, maximum memory, disk space) strictly capped.      |
  |                                                                                 |
  +---------------------------------------------------------------------------------+
```

#### Network Access Controls
* **Level 2 & Level 3 sandboxes** operate with **zero network access** (`--network none` in container configs). This prevents untrusted, evolved code or compromised dependencies from exfiltrating data, accessing database instances, or communicating with external networks.
* **Research Discovery** operates on a dedicated proxy-controlled internet channel restricted solely to paper feeds (e.g., arXiv API, Semantic Scholar). It cannot interact with any trading execution APIs.

---

### 3. Automated Dependency Scanning & Code Verification
Before any evolved code can be merged or executed inside a Level 3 sandbox:
* **AST Parsing & Static Analysis**: The code is parsed into an Abstract Syntax Tree (AST) to look for malicious patterns. Any presence of functions like `os.system`, `subprocess.Popen` (unless whitelisted for local test environments), `socket`, `eval`, or `exec` in mutated code blocks instantly triggers a high-severity alert, terminates the experiment, and quarantines the branch.
* **Dependency Audits**: If a paper suggests adding an external Python package, the SBL scans the package using `pip-audit` or `safety` databases. No package is allowed if it contains critical or high-severity vulnerabilities.

---

### 4. Human-In-The-Loop (HITL) Governance Matrix
While ASRS is designed for continuous, autonomous exploration, the final promotion step requires human authorization to maintain oversight.

| Action | Autonomy Level | Automated Verification Required | Governance Approval Authority |
| :--- | :--- | :--- | :--- |
| **Research Ingest** | Full Autonomy | Parse schema validation, EROI filter | Automated (RDD/RUD) |
| **Sandbox Execution** | Full Autonomy | Compute Resource Scheduler limits | Automated (EG) |
| **Harness Promotion** | Hybrid | Statistical verification, ARA audit | Human-in-the-loop (1-click approval) |
| **Strategy Promotion** | Low Autonomy | Backtests, Walk-Forward, Monte Carlo | Board of Directors / Risk Committee |
| **World Model Merge** | Hybrid | VFE optimization bounds, Replay tests | Lead Architect Review |

---

### 5. Automated Rollback Protocol
In the event that a promoted improvement displays unexpected behavior, high resource utilization, or capital drawdown in production:

1. **Anomaly Detection**: The System Supervisor continuously monitors live metrics (error rates, processing time, Sharpe ratio, drawdowns).
2. **Threshold Violation**: If error rate $> 0.01$ or drawdown $> 5\%$ on the promoted branch, the Supervisor halts live trading, disables the self-improved module, and activates the rollback script.
3. **Rollback Revert**:
   * **Level 1 Revert**: Memory configurations are immediately reloaded to the baseline JSON parameters.
   * **Level 2/3 Revert**: Executes the rollback vector, reverting the production branch to the stable base commit SHA (`git reset --hard <base_sha>`).
4. **Quarantine**: The failed experiment is marked as `ROLLED_BACK` inside the Research Ledger, and its parameter family is flagged as "High Risk / Do Not Evolve" to prevent future similar mutations.
