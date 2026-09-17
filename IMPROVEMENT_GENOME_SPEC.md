# AlphaAlgo Improvement Genome Specification

This document defines the schema, structure, and constraints of the AlphaAlgo-native **Improvement Genome**. Every candidate code or parameter change proposed by the system must carry this immutable genome blocks.

---

## 1. Genome Schema (JSON-Schema Core)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AlphaAlgoImprovementGenome",
  "type": "object",
  "required": [
    "genome_id",
    "parent_version",
    "target_capability",
    "hypothesis",
    "proposed_change",
    "expected_benefit",
    "affected_components",
    "dependencies",
    "experiment_definition",
    "evaluation_protocol",
    "baseline",
    "safety_constraints",
    "threat_model",
    "provenance",
    "approval_state",
    "deployment_state",
    "rollback_target"
  ],
  "properties": {
    "genome_id": {
      "type": "string",
      "description": "Unique UUIDv4 for the improvement candidate."
    },
    "parent_version": {
      "type": "string",
      "description": "The exact Git commit SHA of the parent system."
    },
    "target_capability": {
      "type": "string",
      "enum": ["world_model_learning", "strategy_discovery", "execution_intelligence", "portfolio_intelligence", "market_analysis"],
      "description": "The specific capability targeted for improvement."
    },
    "hypothesis": {
      "type": "string",
      "description": "The scientific hypothesis explaining why this change improves the target capability."
    },
    "proposed_change": {
      "type": "object",
      "properties": {
        "files_modified": { "type": "array", "items": { "type": "string" } },
        "parameters": { "type": "object" },
        "code_diff": { "type": "string" }
      }
    },
    "expected_benefit": {
      "type": "object",
      "properties": {
        "metric": { "type": "string" },
        "target_value_gain": { "type": "number" }
      }
    },
    "affected_components": {
      "type": "array",
      "items": { "type": "string" }
    },
    "dependencies": {
      "type": "array",
      "items": { "type": "string" }
    },
    "experiment_definition": {
      "type": "object",
      "properties": {
        "sandbox_type": { "type": "string", "enum": ["multiprocessing", "isolated_docker"] },
        "timeout_seconds": { "type": "number" },
        "memory_limit_mb": { "type": "number" }
      }
    },
    "evaluation_protocol": {
      "type": "object",
      "properties": {
        "dataset_split_id": { "type": "string" },
        "out_of_sample_period_days": { "type": "number" },
        "slippage_bps": { "type": "number" },
        "commission_bps": { "type": "number" }
      }
    },
    "baseline": {
      "type": "object",
      "properties": {
        "metric_values": { "type": "object" },
        "reference_version": { "type": "string" }
      }
    },
    "safety_constraints": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "metric": { "type": "string" },
          "threshold": { "type": "number" },
          "operator": { "type": "string", "enum": ["gte", "lte"] }
        }
      }
    },
    "threat_model": {
      "type": "object",
      "properties": {
        "possible_vulnerabilities": { "type": "array", "items": { "type": "string" } },
        "exploit_vectors": { "type": "array", "items": { "type": "string" } }
      }
    },
    "red_team_results": {
      "type": "object",
      "properties": {
        "falsification_score": { "type": "number" },
        "failures_encountered": { "type": "array", "items": { "type": "string" } },
        "reproducible_bugs": { "type": "array", "items": { "type": "string" } }
      }
    },
    "independent_evaluation": {
      "type": "object",
      "properties": {
        "evaluator_signature": { "type": "string" },
        "oos_gain": { "type": "number" },
        "drawdown_impact": { "type": "number" },
        "latency_impact_ms": { "type": "number" },
        "is_approved": { "type": "boolean" }
      }
    },
    "provenance": {
      "type": "object",
      "properties": {
        "author_agent_id": { "type": "string" },
        "timestamp": { "type": "string", "format": "date-time" },
        "integrity_hash": { "type": "string" }
      }
    },
    "resource_cost": {
      "type": "object",
      "properties": {
        "vram_gb": { "type": "number" },
        "cpu_seconds": { "type": "number" }
      }
    },
    "complexity_impact": {
      "type": "object",
      "properties": {
        "loc_delta": { "type": "number" },
        "cyclomatic_complexity_delta": { "type": "number" }
      }
    },
    "deployment_risk": {
      "type": "string",
      "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    },
    "approval_state": {
      "type": "string",
      "enum": ["PROPOSED", "SANDBOXED", "CRITIQUED", "RED_TEAMED", "EVALUATED", "APPROVED", "REJECTED"]
    },
    "deployment_state": {
      "type": "string",
      "enum": ["UNDEPLOYED", "CANARY_STAGED", "ACTIVE_PROD", "ROLLED_BACK"]
    },
    "rollback_target": {
      "type": "string",
      "description": "Commit SHA or genome ID to revert to upon failure."
    }
  }
}
```

---

## 2. Unalterable Genome Laws (Hard-Coded Invariants)

1. **Evaluator Invariance**: The candidate code contains absolutely zero access to change `validate_evolution`, `EvolutionGate`, or any evaluation harness.
2. **Deterministic Replayability**: Any candidate genome must reproduce the exact same out-of-sample metrics when re-evaluated on the exact same dataset splits and seed.
3. **No Self-Rewrite of Genome Rules**: The rules governing the genome schema, safety constraints, and promotion operators are kept inside the **Immutable Shield** (`trading_bot/core/immutable_shield.py`), which is protected by un-bypassable hardware/process-level read-only locks. AlphaAlgo cannot rewrite or propose changes to its own evaluation and promotion logic.
