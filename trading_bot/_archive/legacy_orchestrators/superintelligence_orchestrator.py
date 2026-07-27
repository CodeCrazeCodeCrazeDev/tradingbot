"""Autonomous multi-agent orchestration layer for the trading research ecosystem."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .self_optimizing_core import SelfOptimizingCore

logger = logging.getLogger(__name__)


@dataclass
class Opportunity:
    """A machine-discovered market/company/research opportunity."""

    domain: str
    thesis: str
    score: float
    suggested_agents: List[str] = field(default_factory=list)


class SuperintelligenceOrchestrator:
    """Coordinates agents, discovers opportunities, and drives continuous experiments."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.initialized = False
        self.self_optimizer = SelfOptimizingCore(self.config.get("optimizer", {}))
        self.agent_registry: Dict[str, Dict[str, Any]] = {
            "market-scout": {"kind": "discovery", "status": "idle"},
            "model-lab": {"kind": "research", "status": "idle"},
            "capital-allocator": {"kind": "deployment", "status": "idle"},
        }
        self.research_domains: List[str] = ["market_microstructure", "alt_data"]
        logger.info("%s initialized", self.__class__.__name__)

    def initialize(self) -> bool:
        self.initialized = self.self_optimizer.initialize()
        return self.initialized

    def process(self, data: Any) -> Dict[str, Any]:
        if not self.initialized:
            self.initialize()

        payload = data if isinstance(data, dict) else {"input": data}
        opportunities = self.discover_opportunities(payload)
        coordination = self.coordinate_agents(opportunities)
        infra_plan = self.self_optimizer.allocate_infrastructure(
            [o.__dict__ for o in opportunities],
            total_compute_budget=float(payload.get("compute_budget", 100.0)),
        )
        optimization = self.self_optimizer.optimize_system(payload)

        return {
            "timestamp": datetime.now().isoformat(),
            "opportunities": [o.__dict__ for o in opportunities],
            "coordination": coordination,
            "infrastructure": infra_plan,
            "optimization": optimization,
        }

    def discover_opportunities(self, signals: Dict[str, Any]) -> List[Opportunity]:
        """Detect emerging opportunities from structured signals."""
        opportunities: List[Opportunity] = []
        for item in signals.get("opportunity_signals", []):
            score = float(item.get("score", 0.0))
            if score < self.config.get("opportunity_threshold", 0.55):
                continue
            opportunities.append(
                Opportunity(
                    domain=item.get("domain", "unknown"),
                    thesis=item.get("thesis", "Unspecified opportunity"),
                    score=score,
                    suggested_agents=item.get(
                        "suggested_agents", ["market-scout", "model-lab"]
                    ),
                )
            )

        # Autonomous domain expansion if novel domains appear repeatedly.
        for opp in opportunities:
            if opp.domain not in self.research_domains:
                self.research_domains.append(opp.domain)

        return opportunities

    def coordinate_agents(self, opportunities: List[Opportunity]) -> Dict[str, Any]:
        tasks = []
        for opp in opportunities:
            for agent_name in opp.suggested_agents:
                if agent_name not in self.agent_registry:
                    self.agent_registry[agent_name] = {
                        "kind": "spawned",
                        "status": "active",
                        "origin": "autonomous-domain-expansion",
                    }
                else:
                    self.agent_registry[agent_name]["status"] = "active"
                tasks.append(
                    {
                        "agent": agent_name,
                        "domain": opp.domain,
                        "task": f"Investigate: {opp.thesis}",
                    }
                )

        return {
            "active_agents": [name for name, meta in self.agent_registry.items() if meta.get("status") == "active"],
            "tasks": tasks,
            "research_domains": list(self.research_domains),
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "initialized": self.initialized,
            "timestamp": datetime.now().isoformat(),
            "agents": self.agent_registry,
            "domains": self.research_domains,
            "optimizer": self.self_optimizer.get_status(),
        }


def create_superintelligence_orchestrator(
    config: Optional[Dict[str, Any]] = None,
) -> SuperintelligenceOrchestrator:
    return SuperintelligenceOrchestrator(config)
