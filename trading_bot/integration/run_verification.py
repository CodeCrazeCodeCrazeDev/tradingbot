"""
Integration Verification Runner
================================
Phase 5 of the world-class integration plan.

Runs:
  1. Module discovery & classification (canonical registry scan)
  2. Static import health checks
  3. Dependency graph build & validation
  4. Static verification on highest-impact modules (Tier A, direct capital)
  5. Produces a JSON + human-readable integration status report

Usage:
    python -m trading_bot.integration.run_verification
    python -m trading_bot.integration.run_verification --save-report
    python -m trading_bot.integration.run_verification --tier A --layer 4
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure project root is on sys.path
_HERE = Path(__file__).parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("integration.verify")


# ---------------------------------------------------------------------------
# Verification steps
# ---------------------------------------------------------------------------

def step_scan_and_classify() -> dict:
    """Step 1 & 2: Scan modules, classify, analyse static properties."""
    from trading_bot.integration.module_registry import get_module_registry

    logger.info("[STEP 1/5] Scanning and classifying modules...")
    t0 = time.monotonic()

    reg = get_module_registry()
    discovered = reg.scan()
    reg.classify()
    reg.analyze_static()

    elapsed = time.monotonic() - t0
    report = reg.status_report()
    report["scan_duration_s"] = round(elapsed, 2)
    report["newly_discovered"] = discovered

    logger.info(
        f"  Discovered: {report['total_modules']}  "
        f"Unclassified: {report['by_layer'].get('UNCLASSIFIED', 0)}  "
        f"({elapsed:.1f}s)"
    )
    return report


def step_import_health(max_checks: int = 200) -> dict:
    """Step 3: Test importability of modules (capped to avoid long runtime)."""
    from trading_bot.integration.module_registry import get_module_registry

    logger.info(f"[STEP 2/5] Import health checks (max={max_checks})...")
    t0 = time.monotonic()

    reg = get_module_registry()
    counts = reg.check_imports(quick=True, max_per_tier=max_checks)

    elapsed = time.monotonic() - t0
    counts["duration_s"] = round(elapsed, 2)
    logger.info(
        f"  Healthy: {counts['healthy']}  Broken: {counts['broken']}  "
        f"Skipped: {counts['skipped']}  ({elapsed:.1f}s)"
    )
    return counts


def step_dependency_graph() -> dict:
    """Step 4: Build default dependency graph and validate."""
    from trading_bot.integration.dependency_graph import build_default_graph, DependencyCycle

    logger.info("[STEP 3/5] Building and validating dependency graph...")
    t0 = time.monotonic()

    graph = build_default_graph()
    warnings = graph.validate(strict=False)
    summary = graph.summary()

    try:
        startup_order = graph.startup_order()
        order_ok = True
        cycle_error = None
    except DependencyCycle as exc:
        startup_order = []
        order_ok = False
        cycle_error = str(exc)

    elapsed = time.monotonic() - t0
    result = {
        "services_in_graph": summary["total_services"],
        "dependency_edges": summary["edges"],
        "layers_covered": summary["layers"],
        "tiers_covered": summary["tiers"],
        "startup_order_valid": order_ok,
        "cycle_error": cycle_error,
        "warnings": warnings,
        "startup_order": [n.name for n in startup_order],
        "duration_s": round(elapsed, 2),
    }
    logger.info(
        f"  Services: {result['services_in_graph']}  "
        f"Edges: {result['dependency_edges']}  "
        f"Order valid: {order_ok}  "
        f"Warnings: {len(warnings)}  ({elapsed:.1f}s)"
    )
    if warnings:
        for w in warnings[:5]:
            logger.warning(f"    GRAPH WARNING: {w}")
    return result


def step_static_verify(tier_filter: str = "A", layer_filter: int = 4) -> dict:
    """Step 5: Static verification on highest-impact modules."""
    from trading_bot.integration.module_registry import (
        get_module_registry, ModuleTier, ModuleLayer, PromotionState
    )
    from trading_bot.integration.verification import StaticVerifier, VerificationResult

    logger.info(
        f"[STEP 4/5] Static verification (tier={tier_filter} layer={layer_filter})..."
    )
    t0 = time.monotonic()

    reg = get_module_registry()
    verifier = StaticVerifier()

    # Target: Tier A + direct capital impact modules first, then all Tier A
    targets = [
        r for r in reg.records.values()
        if (
            r.tier == tier_filter
            and r.layer == layer_filter
            and r.promotion_state != PromotionState.QUARANTINED.value
        )
    ]
    # Also include all direct-impact modules regardless of layer
    direct_targets = [
        r for r in reg.records.values()
        if (
            r.capital_impact == "direct"
            and r.promotion_state != PromotionState.QUARANTINED.value
            and r not in targets
        )
    ]
    all_targets = targets + direct_targets[:50]  # cap at 50 for runtime

    passed = 0
    failed = 0
    warned = 0
    reports = []

    for record in all_targets:
        report = verifier.verify(
            module_path=record.module_path,
            file_path=record.file_path,
            service_name=record.domain or record.module_path.split(".")[-1],
            tier=record.tier,
            capital_impact=record.capital_impact,
            layer=record.layer,
        )
        if report.overall == VerificationResult.PASS:
            passed += 1
            # Advance promotion state for those that pass
            if record.promotion_state == PromotionState.REGISTERED.value:
                record.promotion_state = PromotionState.VERIFIED.value
        elif report.overall == VerificationResult.FAIL:
            failed += 1
        else:
            warned += 1

        reports.append({
            "module": record.module_path,
            "overall": report.overall.value,
            "passed": report.passed,
            "failed": report.failed,
            "warnings": report.warnings,
            "failed_checks": [
                c.name for c in report.checks
                if c.result == VerificationResult.FAIL
            ],
        })

    elapsed = time.monotonic() - t0
    result = {
        "modules_verified": len(all_targets),
        "passed": passed,
        "failed": failed,
        "warned": warned,
        "pass_rate": round(passed / max(len(all_targets), 1) * 100, 1),
        "duration_s": round(elapsed, 2),
        "reports": reports,
    }
    logger.info(
        f"  Verified: {len(all_targets)}  Pass: {passed}  Fail: {failed}  "
        f"Warn: {warned}  Pass rate: {result['pass_rate']}%  ({elapsed:.1f}s)"
    )
    return result


def step_promotion_summary() -> dict:
    """Step 6: Produce final promotion state summary and save registry."""
    from trading_bot.integration.module_registry import get_module_registry, PromotionState

    logger.info("[STEP 5/5] Generating final promotion summary...")
    reg = get_module_registry()

    # Auto-promote all registered+healthy modules to REGISTERED state
    for record in reg.records.values():
        if (
            record.import_healthy is True
            and record.promotion_state == "discovered"
            and not record.has_forbidden_patterns
        ):
            record.promotion_state = PromotionState.REGISTERED.value

    reg.save()
    return reg.status_report()


# ---------------------------------------------------------------------------
# Full report assembly
# ---------------------------------------------------------------------------

async def run_all(save_report: bool = True, tier: str = "A", layer: int = 4) -> dict:
    t_total = time.monotonic()
    logger.info("")
    logger.info("=" * 70)
    logger.info("  ALPHAALGO WORLD-CLASS INTEGRATION VERIFICATION")
    logger.info(f"  {datetime.utcnow().isoformat()} UTC")
    logger.info("=" * 70)

    scan_result  = step_scan_and_classify()
    import_result = step_import_health(max_checks=300)
    graph_result  = step_dependency_graph()
    static_result = step_static_verify(tier_filter=tier, layer_filter=layer)
    promo_result  = step_promotion_summary()

    total_elapsed = time.monotonic() - t_total

    full_report = {
        "meta": {
            "generated": datetime.utcnow().isoformat(),
            "total_duration_s": round(total_elapsed, 2),
            "plan_file": "C:/Users/peterson/.windsurf/plans/world-class-module-integration-99af5b.md",
        },
        "scan": scan_result,
        "import_health": import_result,
        "dependency_graph": graph_result,
        "static_verification": static_result,
        "promotion_summary": promo_result,
        "integration_score": _compute_score(scan_result, import_result, graph_result, static_result),
    }

    _print_final_report(full_report)

    if save_report:
        report_dir = _ROOT / "alphaalgo_data"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"integration_verification_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.write_text(json.dumps(full_report, indent=2, default=str), encoding="utf-8")
        logger.info(f"\nReport saved → {report_path}")

    return full_report


def _compute_score(scan: dict, imports: dict, graph: dict, static: dict) -> dict:
    """Compute an integration health score out of 100."""
    scores = {}

    # 1. Coverage: % of modules classified (not UNCLASSIFIED)
    total = max(scan.get("total_modules", 1), 1)
    unclassified = scan.get("by_layer", {}).get("UNCLASSIFIED", 0)
    classified_pct = round((total - unclassified) / total * 100, 1)
    scores["classification_coverage"] = classified_pct

    # 2. Import health: % healthy out of checked
    checked = imports.get("healthy", 0) + imports.get("broken", 0)
    import_pct = round(imports.get("healthy", 0) / max(checked, 1) * 100, 1)
    scores["import_health"] = import_pct

    # 3. Dependency graph: valid = 100, cycle = 0
    scores["dependency_graph"] = 100 if graph.get("startup_order_valid") else 0

    # 4. Static verification pass rate
    scores["static_verification"] = static.get("pass_rate", 0)

    # Weighted overall
    overall = round(
        classified_pct * 0.25
        + import_pct * 0.25
        + scores["dependency_graph"] * 0.25
        + scores["static_verification"] * 0.25,
        1,
    )
    scores["overall_score"] = overall
    return scores


def _print_final_report(report: dict) -> None:
    score = report["integration_score"]
    promo = report["promotion_summary"]
    graph = report["dependency_graph"]
    static = report["static_verification"]

    lines = [
        "",
        "=" * 70,
        "  INTEGRATION VERIFICATION COMPLETE",
        "=" * 70,
        f"  Overall Integration Score : {score['overall_score']}/100",
        f"  Classification Coverage   : {score['classification_coverage']}%",
        f"  Import Health             : {score['import_health']}%",
        f"  Dependency Graph Valid    : {'YES' if graph['startup_order_valid'] else 'NO - CYCLE DETECTED'}",
        f"  Static Verification Pass  : {score['static_verification']}%",
        "",
        "  Module Inventory:",
        f"    Total discovered        : {promo['total_modules']}",
        f"    Registered              : {promo['by_promotion_state'].get('registered', 0)}",
        f"    Verified                : {promo['by_promotion_state'].get('verified', 0)}",
        f"    Promoted                : {promo['by_promotion_state'].get('promoted', 0)}",
        f"    Quarantined             : {promo['quarantined']}",
        "",
        "  By Architecture Layer:",
    ]
    for layer_name, count in sorted(promo["by_layer"].items()):
        lines.append(f"    {layer_name:<28} {count:>5}")
    lines += [
        "",
        "  By Tier:",
    ]
    for tier, count in sorted(promo["by_tier"].items()):
        lines.append(f"    Tier {tier:<24} {count:>5}")
    lines += [
        "",
        "  By Capital Impact:",
    ]
    for impact, count in sorted(promo["by_capital_impact"].items()):
        lines.append(f"    {impact:<28} {count:>5}")
    lines += [
        "",
        f"  Dependency Graph: {graph['services_in_graph']} services, {graph['dependency_edges']} edges",
        f"  Startup Order: {graph['startup_order'][:8]}... ({len(graph['startup_order'])} total)",
        "",
        f"  Duration: {report['meta']['total_duration_s']}s",
        "=" * 70,
    ]
    print("\n".join(lines))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    p = argparse.ArgumentParser(description="AlphaAlgo Integration Verification")
    p.add_argument("--save-report", action="store_true", default=True)
    p.add_argument("--no-save-report", dest="save_report", action="store_false")
    p.add_argument("--tier", default="A", help="Tier filter for static verification")
    p.add_argument("--layer", type=int, default=4, help="Layer filter for static verification")
    return p.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_all(save_report=args.save_report, tier=args.tier, layer=args.layer))
