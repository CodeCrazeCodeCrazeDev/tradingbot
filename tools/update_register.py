"""Apply status updates to WEAKNESS_REGISTER.json rows.

Usage: python tools/update_register.py
Edits STATUS_MAP below per wave; keyed on (file, line) or file-prefix.
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REG = REPO / "WEAKNESS_REGISTER.json"


def norm(p: str) -> str:
    return p.replace("\\", "/")


FIXED = {
    "trading_bot/execution/service.py:173":
        "fixed: raise RuntimeError when legacy enums unresolvable (test_weakness_wave1)",
    "trading_bot/governance/evolution_gate.py:303":
        "fixed: baseline benchmark failure returns False instead of fabricated-default comparison",
    "trading_bot/audit/trade_journal.py:356":
        "fixed: update columns whitelisted against schema before interpolation",
    "trading_bot/distributed/parallel_backtester.py:347":
        "fixed: safe_exec_strategy restricted globals",
    "trading_bot/distributed/parallel_backtester.py:565":
        "fixed: safe_exec_strategy restricted globals",
    "trading_bot/distributed/parallel_backtester.py:693":
        "fixed: safe_exec_strategy restricted globals",
    "trading_bot/ingestion/storage.py:248":
        "fixed: ClickHouse identifier charset validation before client init",
    "trading_bot/unified_bot.py:430":
        "fixed: evolution stop failure now logged at warning",
    "trading_bot/core/unified_event_bus.py:230":
        "fixed: queue rebuild failure now logged at debug",
    "trading_bot/decision_governance/self_inspection.py:1773":
        "fixed: capability-gap probe failure logged at debug",
    "trading_bot/recursive_self_improvement/evidence_boundaries.py:73":
        "fixed: signature verify narrowed to expected exception types",
}

CLASSIFIED_PREFIX = {
    "trading_bot/execution/__init__.py":
        "classified: optional-import guards by design",
    "trading_bot/risk/unified_risk_manager.py":
        "classified: deprecated compat stub (warns on import; canonical authority is risk/service.py)",
    "trading_bot/core/unified_event_bus.py":
        "classified: narrow asyncio.CancelledError shutdown pattern",
    "trading_bot/execution/advanced_order_management.py":
        "classified: narrow asyncio.CancelledError shutdown pattern",
    "trading_bot/decision_governance/continuous_capability_discovery.py":
        "classified: optional-import probes / CancelledError shutdown",
    "trading_bot/decision_governance/unified_intelligence.py":
        "classified: narrow asyncio.CancelledError shutdown pattern",
    "trading_bot/decision_governance/self_inspection.py":
        "classified: narrow asyncio.CancelledError shutdown pattern (line 227)",
    "trading_bot/core/governance/determinism.py":
        "classified: optional numpy/torch import guards",
    "trading_bot/core/governance/replay.py":
        "classified: optional torch import guard",
    "trading_bot/risk/correlation_manager.py":
        "classified: documented None-on-missing semantics",
    "trading_bot/risk/correlation_persistence.py":
        "classified: load-failure default by design",
    "trading_bot/evaluation/synthetic_market.py":
        "classified: rng is seeded per instrument (false positive)",
    "trading_bot/recursive_self_improvement/evaluation.py":
        "classified: Random is seeded from contract hash (false positive)",
    "trading_bot/security/safe_eval.py":
        "classified: AST-interpreting evaluator, not builtin eval (false positive)",
    "trading_bot/core/trade_journal.py":
        "classified: column names from internal dataclass, not caller input",
    "trading_bot/database/robust_db.py":
        "classified: hardcoded table list",
    "trading_bot/cos/cognition_store.py":
        "classified: hardcoded column list",
    "trading_bot/core/security/sandbox.py":
        "classified: exec inside isolated worker with restricted builtins by design",
}


def main():
    d = json.loads(REG.read_text())
    n_fix = n_cls = 0
    for r in d["findings"]:
        key = f"{norm(r['file'])}:{r['line']}"
        if key in FIXED:
            r["status"] = FIXED[key]
            n_fix += 1
        elif norm(r["file"]) in CLASSIFIED_PREFIX and r["severity"] in ("S0", "S1", "S2", "S3"):
            r["status"] = CLASSIFIED_PREFIX[norm(r["file"])]
            n_cls += 1
    d["counts"]["fixed_this_round"] = n_fix
    d["counts"]["classified_this_round"] = n_cls
    REG.write_text(json.dumps(d, indent=2))
    print(f"fixed: {n_fix}  classified: {n_cls}")


if __name__ == "__main__":
    main()
