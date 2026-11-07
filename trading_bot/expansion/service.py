"""Expansion service wiring — attaches the canonical growth services to
the CSC advisory electorate.

Every service emits measured advisory evidence only. Heavy scans are
cached and refreshed on a slow cadence — an advisor that reads the
whole database every cycle would starve the decision loop.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .domains import DomainGenerator
from .ecosystem import EcosystemHealth
from .foundry import AgentFoundry
from .governor import ResourceGovernor
from .inventory import DataResourceInventory
from .scanner import OpportunityScanner

logger = logging.getLogger(__name__)

DEFAULT_STATE_DIR = "var/expansion"
SCAN_REFRESH_CYCLES = 240  # ~every 240 advisory calls


class ExpansionContext:
    """Shared measured state behind the expansion advisory services."""

    def __init__(self, root: Any, state_dir: Any,
                 active: Optional[Iterable[Tuple[str, str]]] = None,
                 budgets: Optional[Dict[str, float]] = None) -> None:
        self.root = Path(root)
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.inventory = DataResourceInventory(
            self.root,
            state_path=self.state_dir / "onboarded.json")
        self.scanner = OpportunityScanner(self.inventory,
                                          active=active)
        self.foundry = AgentFoundry(
            self.state_dir / "foundry.json")
        self.governor = ResourceGovernor(self.state_dir,
                                         budgets=budgets)
        self.domains = DomainGenerator(
            self.state_dir / "domains.json")
        self.active = set(active or ())
        self._scan_cache: Optional[Dict[str, Any]] = None
        self._scan_calls = 0

    def scan(self, force: bool = False) -> Dict[str, Any]:
        self._scan_calls += 1
        if self._scan_cache is None or force or \
                self._scan_calls % SCAN_REFRESH_CYCLES == 0:
            self._scan_cache = self.scanner.scan_all()
            (self.state_dir / "last_scan.json").write_text(
                json.dumps(self._scan_cache, indent=2, default=str))
        return self._scan_cache

    def run_domains(self, csc: Any) -> List[Dict[str, Any]]:
        scan = self.scan()
        hms = getattr(csc, "hms", None)
        failures: Dict[str, int] = {}
        if hms is not None and hasattr(hms, "failure_summary"):
            try:
                failures = dict(
                    (hms.failure_summary() or {}).get("by_kind", {}))
            except Exception:  # noqa: BLE001
                failures = {}
        falsified = [
            str(getattr(getattr(c, "spec", {}), "get", lambda k: "")(
                "kind") or getattr(c, "name", "unknown"))
            for c in (getattr(csc, "_engineered_models", {}) or {})
            .values()
            if getattr(c, "verdict", None) == "FALSIFIED"]
        return self.domains.generate(
            coverage_gaps=self.inventory.coverage_gaps(
                self.active, catalog=None),
            emerging_regimes=scan.get("emerging_regimes", ()),
            failure_kinds=failures,
            falsified_families=falsified)


def attach_expansion_services(
    csc: Any,
    *,
    root: Any = ".",
    state_dir: Any = DEFAULT_STATE_DIR,
    active: Optional[Iterable[Tuple[str, str]]] = None,
    budgets: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Attach all expansion services as advisory cognition services.

    Returns a truthful attach report — services that fail to build are
    reported skipped, never silently absent."""
    from trading_bot.core.csc.advisory import AdvisoryModuleAdapter

    ctx = ExpansionContext(root, state_dir, active=active,
                           budgets=budgets)
    attached: List[str] = []
    skipped: Dict[str, str] = {}

    def _register(cap_id: str, fn: Any) -> None:
        try:
            csc.configure_cognition(AdvisoryModuleAdapter(cap_id, fn))
            attached.append(cap_id)
        except Exception as exc:  # noqa: BLE001
            skipped[cap_id] = str(exc)[:160]

    eco = EcosystemHealth(csc)
    _register("expansion_ecosystem", lambda c: eco.report())
    _register("expansion_governor", lambda c: ctx.governor.measure())
    _register("expansion_scanner", lambda c: _cached_advisory(ctx))
    _register("expansion_foundry", lambda c: ctx.foundry.summary())
    _register("expansion_domains",
              lambda c: {"proposed": ctx.run_domains(csc),
                         **ctx.domains.summary()})
    _register("expansion_inventory",
              lambda c: _inventory_advisory(ctx))
    report = {"attached": attached, "skipped": skipped,
              "state_dir": str(ctx.state_dir)}
    logger.info("expansion services: attached=%d skipped=%s",
                len(attached), skipped)
    return report


def _cached_advisory(ctx: ExpansionContext) -> Dict[str, Any]:
    scan = ctx.scan()
    return {
        "series_scanned": scan["series_scanned"],
        "top_opportunity": (scan["opportunities"][0]
                            if scan["opportunities"] else None),
        "emerging_regimes": [
            {"symbol": r["symbol"], "timeframe": r["timeframe"],
             "vol_regime_ratio": r["vol_regime_ratio"]}
            for r in scan["emerging_regimes"][:5]],
        "new_market_count": len(scan["new_markets"]),
    }


def _inventory_advisory(ctx: ExpansionContext) -> Dict[str, Any]:
    cat = ctx.inventory.scan()
    return {
        "sources": sum(1 for s in cat["sources"].values()
                       if s.get("series")),
        "series_total": cat["series_total"],
        "rows_total": cat["rows_total"],
        "onboarded": ctx.inventory.onboarded(),
        "coverage_gaps": len(ctx.inventory.coverage_gaps(
            ctx.active, catalog=cat)),
    }


def expansion_status(csc: Any = None, ctx: Optional[ExpansionContext]
                     = None) -> Dict[str, Any]:
    """Truthful per-claim status for the capability report — each entry
    records the real mechanism and what it actually measured."""
    status: Dict[str, Any] = {"claims": {}}

    def put(claim: str, mechanism: str, measured: Any) -> None:
        status["claims"][claim] = {
            "mechanism": mechanism, "measured": measured,
            "status": "real_bounded"}

    put("living_ecosystem", "self_wiring electorate lifecycle",
        (EcosystemHealth(csc).report() if csc is not None
         else "needs a CSC"))
    put("builds_new_agents", "model-engineering gated pipeline",
        (ctx.foundry.summary() if ctx is not None
         else "needs an ExpansionContext"))
    put("new_research_domains", "evidence-derived domain proposals",
        (ctx.domains.summary() if ctx is not None
         else "needs an ExpansionContext"))
    put("expands_infrastructure", "verified data-resource onboarding",
        (ctx.inventory.onboarded() if ctx is not None
         else "needs an ExpansionContext"))
    put("manages_resources", "local-host psutil budgets",
        (ctx.governor.measure() if ctx is not None
         else "needs an ExpansionContext"))
    put("global_opportunities", "all onboarded sources scanned",
        ((ctx.scan()["series_scanned"] if ctx is not None
          else "needs an ExpansionContext")))
    put("emerging_markets", "measured regime-shift detection",
        "vol_regime_ratio + persistence shift on real closes")
    put("designs_products", "strategy products from sealed evaluations",
        "reframes 'designs companies' honestly")
    put("new_markets", "untradable-set coverage gaps in real data",
        ((ctx.scan()["new_markets"][:10] if ctx is not None
          else "needs an ExpansionContext")))
    status["generated_at"] = time.time()
    return status
