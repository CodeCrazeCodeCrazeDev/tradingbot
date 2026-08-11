# AlphaAlgo Improvement Genome Specification (2026)

## 1. Genome Philosophy & Design
The **Improvement Genome** is a schema-enforced, machine-readable object that models every proposed modification to the AlphaAlgo system.

An improvement must never exist as a loose patch or untraceable file change. By wrapping every proposal in a versioned genome, we ensure total auditability, structural transparency, and immediate rollback capability.

---

## 2. Canonical JSON Schema
Every proposed improvement must compile into a structure matching the following canonical specification:

```json
{
  "$schema": "https://alphaalgo.org/schemas/improvement_genome.v1.json",
  "genome_version": "1.0.0",
  "improvement_id": "imp-9f82d1e2-csc",
  "parent_version": "v5.4.1",
  "target_subsystem": "trading_bot.core.csc.controller",
  "current_behavior": "Decision synthesis relies on point-probability estimates, causing overconfidence under volatility.",
  "diagnosed_problem": "Lack of epistemic uncertainty tracking during regime transitions (VFE spikes).",
  "proposed_change": "Introduce Bayesian Credal Bounds [P_lower, P_upper] in step 13 calibration.",
  "hypothesis": "Restricting trade execution when the credal span P_upper - P_lower > 0.40 will reduce drawdown under regime drift.",
  "expected_mechanism": "Step 13 contracts boundaries based on validation score; high ambiguity routes decisions to hold.",
  "scientific_basis": "Variational Active Inference (Friston, 2010); Credal Sets (Walley, 1991)",
  "dependencies": [
    "trading_bot.core.unified_event_bus",
    "trading_bot.core.hms.memory"
  ],
  "assumptions": [
    "Baseline data inputs are clean",
    "SAGE graph has high retrieval quality"
  ],
  "expected_benefits": {
    "sharpe_ratio_improvement": 0.15,
    "max_drawdown_reduction_pct": 20.0
  },
  "expected_cost": {
    "additional_inference_latency_ms": 1.2,
    "compute_hours": 0.5
  },
  "risk_level": "MEDIUM",
  "safety_constraints": [
    "Must not modify risk/capital limits",
    "Must preserve 100% test suite compatibility"
  ],
  "evaluation_protocol": {
    "baseline_id": "base-v5-baseline",
    "experiment_configuration": "OOS walk-forward over 1000 historical scenarios",
    "required_gain": 0.05
  },
  "results": {
    "benchmark_results": {
      "gain": 0.1245,
      "reproducible_seed": 42
    },
    "regression_results": {
      "passed": true,
      "failed_tests_count": 0
    },
    "red_team_results": {
      "passed": true,
      "attacks_resisted_count": 5
    }
  },
  "governance": {
    "decision_state": "SHADOW_DEPLOYED",
    "human_approval_required": true,
    "human_approval_state": "APPROVED_BY_STRATEGIST",
    "rollback_version": "v5.4.1"
  },
  "provenance": {
    "git_sha": "88bdb1ee00aa3838dbfa1948839088",
    "signed_hash": "sha256-a9f82d1e2b839818ca83d289191e7c9f82d1e2"
  }
}
```

---

## 3. Strict Validation & Verification Rules

1. **Schema Monotonicity:** Submitting an Improvement Genome with empty expected mechanisms, missing parent references, or invalid safety constraints will trigger an immediate **structural rejection** at Step 2 (Static analysis).
2. **Deterministic Hashing:** The `signed_hash` must represent a SHA-256 hash computed over all fields of the genome (excluding volatile fields like `results` and `governance`) and signed by the proposing agent's key. This guarantees complete lineage and prevents mid-flight tampering.
