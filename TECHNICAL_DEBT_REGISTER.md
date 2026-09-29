# TECHNICAL DEBT REGISTER - AlphaAlgo Production Engineering

This register documents the technical debt inventory, print statement metrics, magic numbers, and legacy modules of the AlphaAlgo Quantitative Platform.

---

## 1. Technical Debt Inventory

The following items are tracked as active technical debt across the codebase:

| Tech Debt ID | Module / File Path | Debt Description | Estimated Rem. Effort | Priority |
| :--- | :--- | :--- | :---: | :---: |
| **TD-01** | `trading_bot/research/` | ~~Massive package size with over 140 python modules; needs refactoring into consolidated sub-folders.~~ **Resolved** — subdomains already existed; the remaining 19 flat modules were consolidated into `governance/`, `discovery/`, `alpha/`, `experimentation/`, `orchestration/`, `core/`, `data/`. A `meta_path` compat finder keeps `trading_bot.research.<name>` resolving for all importers. | 0 | Low |
| **TD-02** | `trading_bot/core/csc/controller.py` | ~~Highly complex 12-stage sequential loop (high cyclomatic complexity).~~ **Resolved** — each pipeline stage extracted into an independently testable `_stage_*` method (`_Terminal` marker distinguishes "stage produced a terminal result" from continue); `process_market_observation` is now a numbered sequence. Behavior-identical (15 CSC tests green). | 0 | Low |
| **TD-03** | `trading_bot/risk/MASTER_risk_manager.py` | ~~Contains hardcoded volatility and leverage magic numbers.~~ **Resolved** — magic numbers hoisted to named module constants (`BASE_RISK_PERCENT`, fallback symbol spec, stub ML features); `RiskLimits` built via field-filtered config passthrough. | 0 | Low |
| **TD-04** | `tests/known_broken_merge.txt` + `tests/_quarantine/` | Generated-test repair — **complete**. Manifest emptied; 2 files remain permanently quarantined (structurally unfixable). Detail in §1a. | Resolved | Low |

### 1a. TD-04 resolution detail

The 1,677-entry `known_broken_merge.txt` manifest is now empty. `tests/_quarantine/` holds only 2 files whose generated code is structurally unfixable:

- `test_multi_symbol.py` — needs a 1,600-line class coupled to `legacy_main/main_v1`
- `test_mutation_quality.py` — bare instance refs with no binding context

Resolutions applied:

- canonical module restoration (`alphaalgo_v2`, `agents2`, `perplexity_trading`, orchestrator/service modules)
- missing class/package re-exports (`brain`, `brokers`, `risk`, `execution`, `advanced_features`, `elite_system`, `integrations`, `infrastructure.health_endpoints`)
- archived-module test aliasing (`trading_bot._archive` resolution in `tests/conftest.py`)
- test-dir `__init__.py` packages fixing import-file mismatches
- deleted-stub restoration into `_archive/`
- merge-splice syntax repair of all 46 quarantined files

---

## 2. Print Statement & Logging Audit

*   **Metric:** Count of raw, un-logged `print()` statements in production folders.
*   **Audit Result:** 0 print statements found in core active paths. All production paths utilize the standardized `logging` or `loguru` wrappers.
*   **Legacy Code Percentages:** $12\%$ of total repository files are categorized as legacy/deprecated (residing in `_archive/` or `trading_bot/agents2/`). These are explicitly excluded from production import scopes.

---

## 3. RSI Subsystem Debt (2026-09-26)

| Tech Debt ID | Module / File Path | Debt Description | Priority |
| :--- | :--- | :--- | :---: |
| **TD-05** | `trading_bot/evaluation/` + `market_data.db` | Only 1,000 EURUSD bars exist (10 days). No multi-instrument, multi-regime, or sealed-holdout evaluation is possible. Real-data path exists only as `SqliteSource` adapter stub. **Partially resolved** — `CsvDirSource` (governed multi-instrument CSV path with per-file SHA-256 provenance and timestamp/price validation) added; acquiring actual multi-instrument/regime datasets remains a data-governance task. | Medium |
| **TD-06** | `recursive_self_improvement/engine_v2.py::SandboxManager` | ~~Thread-deadline sandbox inside the process; not container/process isolation.~~ **Resolved** — `backend="subprocess"` (cycle default) runs candidate work in a spawned child killed on deadline; bounded startup grace via "ready" handshake; child self-times work so the semantic budget excludes process mechanics. | 0 | Low |
| **TD-07** | `recursive_self_improvement/engine_v2.py::IndependentVerifier` | ~~Verifier key is in-process memory.~~ **Mostly resolved** — key custody now via injected key / `key_path` / `RSI_VERIFIER_KEY_FILE` (PEM/DER/raw32); subprocess replay is keyless (parent signs); `ExternalVerifierClient` defines the operator-service contract and fails closed until provisioned. A real HSM/remote service remains an ops task. | Medium |
| **TD-08** | `trading_bot/evaluation/walk_forward.py` | Brain-based single-split diagnostic, not paired and not cost-aware. Retained for compat; not promotion evidence. **Resolved** — machine-visible `EVIDENCE_CLASS = "diagnostic"` on module + `EvaluationReport`; promotion consumers must require `"promotion"`. | 0 | Low |
| **TD-09** | `trading_bot/governance/evolution_gate.py` | ~~Advisory gate still invents optimistic defaults for missing metrics.~~ **Resolved** — gate compares only supplied evidence: missing perf rejects, one-sided metrics reject as insufficient evidence, both-missing dimensions are skipped. | 0 | Low |
| **TD-10** | `trading_bot/recursive_improvement.py`, `auto_optimizer.py`, `self_learning.py`, `optimization.py` | ~~Dead files shadowed by same-named packages.~~ **Resolved** — deleted; verified each name resolves to the package `__init__.py` which already warns. | 0 | Low |
| **TD-11** | `recursive_self_improvement/` (whole) | ~~line-level audit of the legacy tree incomplete.~~ **Resolved** — `rsi_reachability_inventory.py` refresh landed (canonical RSI authority confirmed; deleted shadowed files report DISCONNECTED not MISSING); weakness scanner + context classifier cover the whole tree at line level — 0 open findings. | 0 | Low |

---

*End of Technical Debt Register.*
