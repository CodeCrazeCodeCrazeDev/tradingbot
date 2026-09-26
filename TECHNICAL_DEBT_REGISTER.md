# TECHNICAL DEBT REGISTER - AlphaAlgo Production Engineering

This register documents the technical debt inventory, print statement metrics, magic numbers, and legacy modules of the AlphaAlgo Quantitative Platform.

---

## 1. Technical Debt Inventory

The following items are tracked as active technical debt across the codebase:

| Tech Debt ID | Module / File Path | Debt Description | Estimated Rem. Effort | Priority |
| :--- | :--- | :--- | :---: | :---: |
| **TD-01** | `trading_bot/research/` | Massive package size with over 140 python modules; needs refactoring into consolidated sub-folders. | 24 person-hours | Medium |
| **TD-02** | `trading_bot/core/csc/controller.py` | Highly complex 12-stage sequential loop (high cyclomatic complexity). | 16 person-hours | High |
| **TD-03** | `trading_bot/risk/MASTER_risk_manager.py` | Contains hardcoded volatility and leverage magic numbers. | 4 person-hours | Medium |
| **TD-04** | `tests/known_broken_merge.txt` | Residual generated-test manifest — 41 files referencing modules that were permanently deleted or never existed (fabricated `deepseek_*`/`classa` names, archived modules with internally-missing deps, dead `trading_bot.tests` package). Entries are permanent quarantine unless the modules are deliberately restored. Reduced from 1,677 via: canonical module restoration (`alphaalgo_v2`, `agents2`, `perplexity_trading`, 8 orchestrator/service modules), missing class/package re-exports, archived-module test aliasing (`trading_bot._archive` resolution in `tests/conftest.py`), and test-dir `__init__.py` packages fixing import-file mismatches. | Resolved (maintenance list) | Low |

---

## 2. Print Statement & Logging Audit

*   **Metric:** Count of raw, un-logged `print()` statements in production folders.
*   **Audit Result:** 0 print statements found in core active paths. All production paths utilize the standardized `logging` or `loguru` wrappers.
*   **Legacy Code Percentages:** $12\%$ of total repository files are categorized as legacy/deprecated (residing in `_archive/` or `trading_bot/agents2/`). These are explicitly excluded from production import scopes.

---

## 3. RSI Subsystem Debt (2026-09-26)

| Tech Debt ID | Module / File Path | Debt Description | Priority |
| :--- | :--- | :--- | :---: |
| **TD-05** | `trading_bot/evaluation/` + `market_data.db` | Only 1,000 EURUSD bars exist (10 days). No multi-instrument, multi-regime, or sealed-holdout evaluation is possible. Real-data path exists only as `SqliteSource` adapter stub. | High |
| **TD-06** | `recursive_self_improvement/engine_v2.py::SandboxManager` | Thread-deadline sandbox inside the process; not container/process isolation. A hostile candidate could in principle not be preempted mid-run. | Medium |
| **TD-07** | `recursive_self_improvement/engine_v2.py::IndependentVerifier` | Verifier key is in-process memory. Production requires an operator-controlled external verifier/HSM custody. | High |
| **TD-08** | `trading_bot/evaluation/walk_forward.py` | Brain-based single-split diagnostic, not paired and not cost-aware. Retained for compat; not promotion evidence. | Medium |
| **TD-09** | `trading_bot/governance/evolution_gate.py` | Advisory gate still invents optimistic defaults for missing metrics; must never be the sole RSI authority. | High |
| **TD-10** | `trading_bot/recursive_improvement.py`, `auto_optimizer.py`, `self_learning.py`, `optimization.py` | Dead files shadowed by same-named packages; unreachable code kept for archaeology. | Low |
| **TD-11** | `recursive_self_improvement/` (whole) | ~9,800 repo files audited only by import-reachability; line-level audit of the legacy tree incomplete. | Medium |

---

*End of Technical Debt Register.*
