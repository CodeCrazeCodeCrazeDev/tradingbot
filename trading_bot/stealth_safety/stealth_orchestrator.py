"""
Stealth Safety Orchestrator
============================================================

Coordinates the stealth_safety subsystem's containment and
monitoring components behind a single entry point. Missing
components degrade gracefully — a partially loaded safety net
still vetoes what it can see.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _try_import(module: str, names: List[str]) -> Dict[str, Any]:
    try:
        mod = __import__(f"trading_bot.stealth_safety.{module}", fromlist=names)
        return {n: getattr(mod, n) for n in names if hasattr(mod, n)}
    except Exception as e:
        logger.warning(f"stealth_safety.{module} unavailable: {e}")
        return {}


class StealthSafetyOrchestrator:
    """Aggregates containment, risk-monitoring, and protection components."""

    def __init__(self):
        self.components: Dict[str, Any] = {}
        for module, names in (
            ("ai_containment", ["PurposeLock", "MetaAlignmentRules",
                                "HumanApprovalAbsolute", "NeverOutgrowControl",
                                "AIBoundaryEnforcer"]),
            ("complexity_control", ["ModuleIsolationFirewall", "NoBlackBoxDecisions",
                                    "HiddenBugDetector", "BehaviorTracker",
                                    "ExplainableEverything"]),
            ("psychological_protection", ["CalmTradingPolicy", "HumanStressMonitor"]),
            ("systemic_safety", ["CascadingFailurePrevention",
                                 "MultiDimensionalRiskMonitor",
                                 "SafeModeRuleset", "ExtremeRiskContainment"]),
        ):
            for name, cls in _try_import(module, names).items():
                try:
                    self.components[name] = cls()
                except Exception as e:
                    logger.warning(f"stealth_safety component {name} failed init: {e}")
        logger.info(f"StealthSafetyOrchestrator: {len(self.components)} components active")

    def status(self) -> Dict[str, Any]:
        return {"components": sorted(self.components.keys()),
                "active": len(self.components)}

    def check(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run every component that exposes a check/verify/validate method."""
        context = context or {}
        results: Dict[str, Any] = {}
        ok = True
        for name, comp in self.components.items():
            for meth in ("check", "verify", "validate", "evaluate"):
                fn = getattr(comp, meth, None)
                if callable(fn):
                    try:
                        res = fn(context)
                        results[name] = res
                        if res is False or (isinstance(res, dict) and res.get("status") in ("failed", "violated", "breach")):
                            ok = False
                    except Exception as e:
                        results[name] = {"status": "error", "error": str(e)}
                        ok = False
                    break
        return {"status": "ok" if ok else "violated", "results": results}
