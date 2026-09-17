# Red Team / Blue Team Adversarial Evaluation Architecture

To prevent reward-hacking and protect the system from silent failures, AlphaAlgo enforces a strict **Red Team / Blue Team Adversarial Stage** before any code change can be promoted.

---

## 1. Red Team Attack Vectors (Falsification Matrix)

The Red Team is a non-cooperative, independent testing suite designed to aggressively stress and falsify the proposed candidate. It executes the following target attack scenarios:

### A. Reward Hacking & Evaluator Gaming
*   *Attack Vector*: Attempt to modify the score returned to the optimizer by writing mock metrics, hard-coding success variables, or bypassing the validation engine.
*   *Verification*: AST-level audit scans for any variable reassignment of `validation_engine` or `EvolutionGate` attributes.

### B. Data Ingestion & Leakage
*   *Attack Vector*: Attempt to look ahead in time by reading future price arrays or using non-causal standardizing (e.g. subtracting out-of-sample mean).
*   *Verification*: Strictly isolates walk-forward price buffers in memory-mapped read-only processes.

### C. Confirmation Cascades & False Consensus
*   *Attack Vector*: Multiple agents in the Verification Swarm agreeing without independent critique, leading to groupthink.
*   *Verification*: Forces random, diverse initial prior seeds and mandates the presence of a dissenting "Falsifier" agent.

### D. Memory Poisoning & Provenance Corruption
*   *Attack Vector*: Writing corrupt, duplicate, or uncalibrated entries into the `HierarchicalMemorySystem` to bias future SAGE retrieval.
*   *Verification*: Hash-checks the schema integrity of all writes against the canonical CMOS schemas and signs with active cryptographic keys.

### E. Unsafe Fallback Escalation
*   *Attack Vector*: Forcing database or network failures to trick the agent into using unrestricted mock fallbacks that bypass safety limits.
*   *Verification*: Prohibits mock execution when risk limits are active, raising a hard `RiskValidationException` instead.

### F. Runaway Recursive Self-Modification
*   *Attack Vector*: Initiating self-modification loops where the candidate repeatedly modifies itself without exiting or seeking authority.
*   *Verification*: Restricts active loops to a depth of $K \le 3$ and enforces wall-clock SIGTERM limits.

---

## 2. Blue Team Hardening & Regression Lock

When the Red Team successfully identifies a vulnerability or failure mode in a proposed candidate:
1. **Falsification Lock**: The proposal is flagged as `FAILED_RED_TEAM`.
2. **Vulnerability Extraction**: The specific attack vector and state triggers are serialized into JSON.
3. **Regression Test Generation**: The Blue Team automatically compiles this JSON into a new pytest regression test (stored under `tests/security/` or `tests/stress/`).
4. **Hardening**: The candidate must be modified to resolve the vulnerability. It cannot be promoted until it passes both the original test suite and the newly generated adversarial regression test.
5. **Zero-Regression**: Over time, these generated regression tests build an un-bypassable security wall protecting the active trading system.
