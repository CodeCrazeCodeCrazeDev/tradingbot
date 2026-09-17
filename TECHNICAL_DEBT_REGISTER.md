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

---

## 2. Print Statement & Logging Audit

*   **Metric:** Count of raw, un-logged `print()` statements in production folders.
*   **Audit Result:** 0 print statements found in core active paths. All production paths utilize the standardized `logging` or `loguru` wrappers.
*   **Legacy Code Percentages:** $12\%$ of total repository files are categorized as legacy/deprecated (residing in `_archive/` or `trading_bot/agents2/`). These are explicitly excluded from production import scopes.

---

*End of Technical Debt Register.*
