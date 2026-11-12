"""Governed self-update seam — composes the existing gates into one
declared loop. Nothing here creates new authority; it calls the same
primitives a human operator would, in the same order.

Pipeline (each stage is already implemented elsewhere):
    DISCOVER   discovery.scan_packages / discover_advisory_callables
               -> candidate manifests (source-scanned, never imported)
    PROPOSE    csc.propose_model(spec) -> sealed candidate
    VALIDATE   csc.validate_model(candidate) -> OOS verdict
    APPROVE    requires the durable operator flag — NO bypass exists;
               if absent, the plan reports "awaiting_human" honestly
    ATTACH     csc.attach_engineered_model -> SHADOW, measured only
    LIFECYCLE  self_wiring promotes/demotes on measured emits alone

What "self-update" honestly means here: the system rewrites the set
of things it *consults* (advisory electorate + engineered models)
under measured evidence. It can never rewrite its authority chain,
its risk sizing, or its approval requirement — those are invariant
by INVARIANT_IDS and ProtectedPathGuard.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from .discovery import Manifest, WiringPlan, scan_packages

logger = logging.getLogger(__name__)


@dataclass
class SelfUpdatePlan:
    """What the next self-update cycle *would* do — reported before
    anything runs so an operator can audit intent, not just outcome."""
    discovered: List[Manifest] = field(default_factory=list)
    blocked: List[str] = field(default_factory=list)
    cycles: List[List[str]] = field(default_factory=list)
    dynamic: List[str] = field(default_factory=list)
    wire_order: List[str] = field(default_factory=list)

    def to_report(self) -> Dict[str, Any]:
        return {
            "discovered": [m.id for m in self.discovered],
            "wire_order": self.wire_order,
            "blocked": self.blocked,
            "cycles": self.cycles,
            "dynamic_deferred": self.dynamic,
            "authority_boundary": "advisory-only — INVARIANT_IDS and "
                                  "protected paths unreachable",
        }


def plan_self_update(roots=None, csc=None) -> SelfUpdatePlan:
    """Build the next-cycle plan from live module manifests."""
    if roots is None:
        roots = [Path(__file__).resolve().parents[2]]
    plan: WiringPlan = scan_packages(roots)
    p = SelfUpdatePlan(
        discovered=plan.ordered,
        blocked=[f"{n.manifest.id}:{n.reason}" for n in plan.blocked],
        cycles=plan.cycles,
        dynamic=plan.dynamic,
        wire_order=[m.id for m in plan.ordered])
    logger.info("self-update plan: %d discovered, %d blocked, "
                "%d dynamic deferred", len(p.discovered),
                len(p.blocked), len(p.dynamic))
    return p


async def run_self_update(csc: Any, plan: WiringPlan = None,
                          roots=None) -> Dict[str, Any]:
    """Execute the plan through the REAL gates — never around them.

    1. Wire discovered advisory factories in dep order (they land in
       the electorate at SHADOW — measured, uninfluential).
    2. Report the model-promotion queue: propose/validate/approve/
       attach stays with csc's own methods and their human flag.
    """
    if plan is None:
        plan = scan_packages(roots or
                             [Path(__file__).resolve().parents[2]])
    wired = plan.execute(csc)
    approval = getattr(csc, "operator_approved", None)
    report = {
        "wired": wired,
        "blocked": [f"{n.manifest.id}:{n.reason}"
                    for n in plan.blocked],
        "cycles": plan.cycles,
        "model_promotion": ("awaiting_human — durable operator flag "
                            "absent" if not approval else
                            "operator flag present — approval channel "
                            "available via csc.attach_engineered_model"),
    }
    logger.info("self-update run: %s", report["wired"])
    return report
