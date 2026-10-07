"""Canonical cognitive assembly — the ONE AI.

Everything cognitive in this repository exists exactly once, wired
through this single builder:

- ``CognitiveSystemController`` is the sole decision authority — the
  only component that may propose, gate, or record a trade decision.
- ``trading_bot.cognition`` (perception, memory, simulation, reasoning,
  verification, learning) runs as a *subordinate advisory service* via
  ``AdvisoryCognitiveBrain`` — its authority fields are stripped and its
  output lands in the evidence channel as ``advisory_only`` artifacts.
- The research engine accumulates durable, replayable knowledge — the
  KG, uncertainty map, policy, and falsification ledger.

Nothing else may hold decision authority: the dozens of legacy/parallel
"brain" entry points (``alphaalgo_cognitive_brain``'s own
``process_market_update``, per-module orchestrators, the deprecated
self-improvement systems) are outside this assembly and carry no
authority by construction.

``build_cognitive_system(csc)`` is the single place "the AI" comes
into being — call it once from the runtime entry point.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger("alphaalgo.csc.assembly")


def build_cognitive_system(
    csc: Any,
    *,
    research_interval: Optional[int] = None,
    advisory_brain: bool = True,
) -> Any:
    """Wire the complete cognitive system onto the CSC.

    - ``advisory_brain``: register ``AdvisoryCognitiveBrain`` (the whole
      ``cognition/`` stack, authority-stripped) as a subordinate advisory
      service — its analysis joins the observation's evidence channel.
    - ``research_interval``: enable the research OS in operation; 0 means
      evidence ingestion only (no auto-cycles); None leaves the CSC's
      configured interval unchanged.

    Returns the CSC — the one brain — with every subordinate service
    attached. Idempotent: re-calling re-registers the advisory brain and
    reconfigures research, both of which are safe to repeat.
    """
    if advisory_brain:
        from trading_bot.cognition.advisory_adapter import (
            AdvisoryCognitiveBrain)
        csc.configure_cognition(AdvisoryCognitiveBrain())
        logger.info("cognitive assembly: advisory brain attached "
                    "(authority-stripped)")

        # Every other wireable AI module joins the same advisory channel
        # — the manifest in advisory.py is the total audit map: attached
        # services emit advisory_only evidence; UNWIRED_ORPHAN_MODULES
        # records why everything else is inert.
        from .advisory import attach_advisory_modules
        attached, skipped = attach_advisory_modules(csc)
        logger.info("cognitive assembly: advisory modules attached=%s "
                    "skipped=%s", attached, skipped)

    eng = csc.configure_research()
    if research_interval is not None:
        csc._research_interval = max(0, int(research_interval))
    logger.info(
        "cognitive assembly: research engine attached (interval=%s) — "
        "one AI, CSC sole authority", csc._research_interval)
    return csc
