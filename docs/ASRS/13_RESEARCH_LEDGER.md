# 13. RESEARCH LEDGER
## The Research Ledger & Immutable Scientific Provenance

### 1. Architectural Mission
The **Research Ledger (RL)** is the historical repository of scientific record for AlphaAlgo. In quantitative trading, auditing is critical. Every change deployed to production must have absolute, unambiguous traceability back to its originating paper, hypothesis, simulation results, and review records.

The RL ensures that no change is deployed without complete provenance, making self-improvement transparent, auditable, and scientifically sound.

---

### 2. Ledger Record Schema
Each experiment entry in the Research Ledger is written as an immutable JSON-LD record stored under `trading_bot/research/asrs/ledger/records/` and indexed in a master database.

#### Schema Fields
* `record_uuid` (str): Unique UUIDv4 identifier.
* `timestamp` (str): ISO-8601 UTC timestamp.
* `originating_paper` (str): Node link in Scientific Knowledge Graph (e.g. `paper:eksft_2026`).
* `hypothesis_id` (str): ID of the hypothesis proposed by the ODD.
* `git_context` (Dict[str, str]):
  * `base_sha`: Parent commit SHA of the main branch before change.
  * `experiment_sha`: Commits made during Level 3 isolation branch development.
  * `promotion_sha`: Final merge commit SHA on main.
* `configuration_hash` (str): SHA-256 checksum of the configuration payload.
* `evaluation_datasets` (List[str]): List of datasets, backtest cache keys, and historical periods used.
* `verification_report` (Dict[str, Any]): Summary of unit, integration, deterministic replay, stress, and chaos tests passed.
* `benchmark_metrics` (Dict[str, Any]): Latency percentiles, ECE, prediction accuracy, Sharpe, Calmar, CVaR.
* `statistical_tests` (Dict[str, Any]): Paired t-test p-value, FDR parameters, Bootstrap confidence intervals.
* `adversarial_audit_log` (str): Audit summary written by the Autonomous Reviewer Agent.
* `decision_rationale` (str): Summary of why the candidate was approved or rejected.
* `promotion_outcome` (str): `APPROVED` or `REJECTED`.
* `rollback_instructions` (Dict[str, str]): Revert command / config toggle specifications.

---

### 3. Structural Provenance Chain
The RL connects every phase of the research cycle together:

```text
[Paper Node in SKG] -> [Hypothesis ID (ODD)] -> [Experiment Workspace (EG)]
                                                        |
                                                        v
[Ledger Immutable Hash] <- [Promotion Approval (PG)] <- [Verification Metrics (VL)]
```

---

### 4. Sample Ledger Record (JSON Format)
```json
{
  "$context": "https://alphaalgo.org/contexts/research_ledger.jsonld",
  "record_uuid": "rl-rec-8240f92b-81ea",
  "timestamp": "2026-07-14T06:50:00Z",
  "originating_paper": "paper:eksft_2026",
  "hypothesis_id": "hyp-odd-2026-0082",
  "git_context": {
    "base_sha": "a1b2c3d4e5f6g7h8i9j0a1b2c3d4e5f6g7h8i9j0",
    "experiment_sha": "b2c3d4e5f6g7h8i9j0a1b2c3d4e5f6g7h8i9j0a1",
    "promotion_sha": "c3d4e5f6g7h8i9j0a1b2c3d4e5f6g7h8i9j0a1b2"
  },
  "configuration_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "evaluation_datasets": [
    "dataset:mt5_eurusd_m15_ticks_2020_2025",
    "dataset:stress_high_vol_flash_crash"
  ],
  "verification_report": {
    "unit_tests_passed": true,
    "integration_tests_passed": true,
    "replay_reproducible": true,
    "chaos_resilience_verified": true,
    "peak_memory_leak_slope": 0.001
  },
  "benchmark_metrics": {
    "p99_latency_ms": 142.0,
    "expected_calibration_error": 0.034,
    "annualized_sharpe": 2.38
  },
  "statistical_tests": {
    "bootstrap_sharpe_ci": [0.15, 0.42],
    "paired_t_test_p_value": 0.002,
    "fdr_adjusted_p_value": 0.012
  },
  "adversarial_audit_log": "ARA Audit: Confirmed no lookahead leakage in features. Sensitivity test shows stability under parameter perturbations (+/- 2%). Latency is within institutional limits. Recommending approval.",
  "decision_rationale": "The candidate EKSFT implementation significantly reduced Expected Calibration Error without introducing processing latency or memory leaks, meeting all institutional standards of proof.",
  "promotion_outcome": "APPROVED",
  "rollback_instructions": {
    "command": "git revert -m 1 c3d4e5f6g7h8i9j0a1b2c3d4e5f6g7h8i9j0a1b2",
    "config_toggle": "config.use_eksft = false"
  }
}
```

---

### 5. Ledger Integrity Scans
To ensure the ledger cannot be tampered with or modified retrospectively:
* **Chain-of-Trust Checksums**: Each ledger record includes a hash of the *preceding* ledger record, creating a cryptographic chain-of-trust (Merkle path).
* **Integrity Audit Agent**: A daily job computes the SHA-256 hashes of all ledger files, checking them against the master SQLite index. Any discrepancy triggers a high-severity alert, halting the ASRS and requesting immediate security audit.
