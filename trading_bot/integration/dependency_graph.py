"""
Dependency Graph & Startup Policy
==================================
Authoritative DAG for service startup, shutdown, degradation, and recovery.

Startup order is always determined by:
  1. Layer order   (Layer 0 → Layer 7)
  2. Within a layer: dependency topological sort
  3. Tier within a layer group (Tier A before B before C before D)

The graph guarantees:
  - no circular dependencies (raises DependencyCycle)
  - dependency-ready check before each service starts
  - reverse-topological order for shutdown
  - degradation cascade: if a Tier-A dependency degrades, dependents are notified
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Set

logger = logging.getLogger(__name__)


class DependencyCycle(Exception):
    """Raised when a circular dependency is detected."""


class MissingDependency(Exception):
    """Raised when a required dependency is not registered."""


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

@dataclass
class ServiceNode:
    name: str
    layer: int
    tier: str
    capital_impact: str
    rollback_class: str
    dependencies: List[str] = field(default_factory=list)
    optional_dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def sort_key(self) -> tuple:
        tier_order = {"A": 0, "B": 1, "C": 2, "D": 3, "?": 4}
        return (self.layer, tier_order.get(self.tier, 4), self.name)


# ---------------------------------------------------------------------------
# DependencyGraph
# ---------------------------------------------------------------------------

class DependencyGraph:
    """
    Directed Acyclic Graph of service dependencies.

    Usage:
        graph = DependencyGraph()
        graph.add_node(ServiceNode(name="risk", layer=4, tier="A", ...))
        graph.add_node(ServiceNode(name="execution", layer=5, tier="A",
                                   dependencies=["risk"]))
        start_order = graph.startup_order()
        stop_order  = graph.shutdown_order()
    """

    def __init__(self):
        self._nodes: Dict[str, ServiceNode] = {}
        self._adj: Dict[str, Set[str]] = defaultdict(set)   # name → set of names it depends on
        self._rev: Dict[str, Set[str]] = defaultdict(set)   # name → set of names that depend on it

    # -----------------------------------------------------------------------
    # Graph construction
    # -----------------------------------------------------------------------

    def add_node(self, node: ServiceNode) -> None:
        """Register a service node."""
        self._nodes[node.name] = node
        for dep in node.dependencies:
            self._adj[node.name].add(dep)
            self._rev[dep].add(node.name)

    def remove_node(self, name: str) -> None:
        """Remove a service from the graph."""
        if name not in self._nodes:
            return
        node = self._nodes.pop(name)
        for dep in node.dependencies:
            self._adj[name].discard(dep)
            self._rev[dep].discard(name)
        for dependent in list(self._rev.get(name, set())):
            self._adj[dependent].discard(name)
        self._rev.pop(name, None)
        self._adj.pop(name, None)

    def has_node(self, name: str) -> bool:
        return name in self._nodes

    def get_node(self, name: str) -> Optional[ServiceNode]:
        return self._nodes.get(name)

    def dependents_of(self, name: str) -> Set[str]:
        """Return names of services that depend on this service."""
        return set(self._rev.get(name, set()))

    def dependencies_of(self, name: str) -> Set[str]:
        """Return direct required dependencies of this service."""
        return set(self._adj.get(name, set()))

    # -----------------------------------------------------------------------
    # Topological ordering
    # -----------------------------------------------------------------------

    def startup_order(self) -> List[ServiceNode]:
        """
        Return services in startup order:
          dependencies first, then dependents.
          Within equal dependency level: sorted by (layer, tier, name).
        Raises DependencyCycle if a cycle exists.
        """
        return self._topo_sort(reverse=False)

    def shutdown_order(self) -> List[ServiceNode]:
        """
        Return services in shutdown order (reverse of startup).
        Raises DependencyCycle if a cycle exists.
        """
        return self._topo_sort(reverse=True)

    def _topo_sort(self, reverse: bool = False) -> List[ServiceNode]:
        """Kahn's algorithm with deterministic tie-breaking."""
        # in_degree[n] = number of predecessors n must wait for
        in_degree: Dict[str, int] = {name: 0 for name in self._nodes}
        for name, deps in self._adj.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[name] = in_degree.get(name, 0)   # already exists
                # dep → name means name depends on dep
                # so name's in-degree increases by 1 per dep
        # Recalculate properly
        in_degree = {name: 0 for name in self._nodes}
        for name, deps in self._adj.items():
            for dep in deps:
                if dep in self._nodes:
                    in_degree[name] += 1

        # Seeds: nodes with no (registered) dependencies
        ready: List[ServiceNode] = sorted(
            [self._nodes[n] for n in self._nodes if in_degree[n] == 0],
            key=lambda nd: nd.sort_key,
        )
        queue: deque = deque(ready)
        result: List[ServiceNode] = []
        visited: Set[str] = set()

        while queue:
            node = queue.popleft()
            if node.name in visited:
                continue
            visited.add(node.name)
            result.append(node)

            # Unlock dependents (rev edges)
            next_batch: List[ServiceNode] = []
            for dependent_name in sorted(self._rev.get(node.name, set())):
                if dependent_name not in self._nodes:
                    continue
                in_degree[dependent_name] -= 1
                if in_degree[dependent_name] == 0:
                    next_batch.append(self._nodes[dependent_name])

            next_batch.sort(key=lambda nd: nd.sort_key)
            queue.extend(next_batch)

        if len(result) != len(self._nodes):
            cyclic = [n for n in self._nodes if n not in visited]
            raise DependencyCycle(f"Circular dependencies detected: {cyclic}")

        return list(reversed(result)) if reverse else result

    # -----------------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------------

    def validate(self, strict: bool = False) -> List[str]:
        """
        Validate the graph.
        Returns list of warning strings.
        Raises MissingDependency / DependencyCycle if strict=True.
        """
        warnings: List[str] = []

        # Check for unregistered hard dependencies
        for name, deps in self._adj.items():
            for dep in deps:
                if dep not in self._nodes:
                    msg = f"Service '{name}' depends on unregistered '{dep}'"
                    warnings.append(msg)
                    if strict:
                        raise MissingDependency(msg)

        # Check for cycles
        try:
            self._topo_sort()
        except DependencyCycle as exc:
            msg = str(exc)
            warnings.append(msg)
            if strict:
                raise

        return warnings

    # -----------------------------------------------------------------------
    # Degradation propagation
    # -----------------------------------------------------------------------

    def cascade_impact(self, degraded_service: str) -> Dict[str, str]:
        """
        Given a service that has degraded, return all downstream services
        and their recommended action.

        Returns:
            {service_name: "degrade" | "warn" | "emergency"}
        """
        impact: Dict[str, str] = {}
        source = self._nodes.get(degraded_service)
        if not source:
            return impact

        # BFS over dependents
        queue: deque = deque([(degraded_service, source.tier, source.capital_impact)])
        visited: Set[str] = set()

        while queue:
            svc_name, parent_tier, parent_impact = queue.popleft()
            if svc_name in visited:
                continue
            visited.add(svc_name)

            for dep_name in self._rev.get(svc_name, set()):
                if dep_name not in self._nodes:
                    continue
                dep = self._nodes[dep_name]
                # Determine recommended action
                if dep.rollback_class == "emergency" or parent_impact == "direct":
                    action = "emergency"
                elif dep.tier == "A":
                    action = "degrade"
                else:
                    action = "warn"
                impact[dep_name] = action
                queue.append((dep_name, dep.tier, dep.capital_impact))

        return impact

    # -----------------------------------------------------------------------
    # Reporting
    # -----------------------------------------------------------------------

    def summary(self) -> Dict:
        """Return a summary dict of the graph."""
        return {
            "total_services": len(self._nodes),
            "edges": sum(len(v) for v in self._adj.values()),
            "layers": sorted(set(n.layer for n in self._nodes.values())),
            "tiers": sorted(set(n.tier for n in self._nodes.values())),
            "services": [
                {
                    "name": n.name,
                    "layer": n.layer,
                    "tier": n.tier,
                    "dependencies": list(self._adj.get(n.name, set())),
                }
                for n in sorted(self._nodes.values(), key=lambda nd: nd.sort_key)
            ],
        }

    def __iter__(self) -> Iterator[ServiceNode]:
        return iter(self._nodes.values())

    def __len__(self) -> int:
        return len(self._nodes)


# ---------------------------------------------------------------------------
# Default graph builder — pre-wires known hard dependencies
# ---------------------------------------------------------------------------

def build_default_graph(registered_names: Optional[List[str]] = None) -> DependencyGraph:
    """
    Build and return the default dependency graph from known architectural
    constraints. Only includes nodes present in registered_names if provided.

    Hard dependencies encoded here come from:
      - service_factory.py TIER definitions
      - background_services.py dependency dict
      - architectural layer rules (Risk must precede Execution, etc.)
    """
    graph = DependencyGraph()

    # Explicit dependency declarations.
    # Format: (service_name, layer, tier, capital_impact, rollback_class, [dependencies])
    KNOWN_SERVICES = [
        # ---- Layer 0 – Infrastructure ----
        ("config_manager",         0, "A", "none",     "safe_disable", []),
        ("logging_manager",        0, "A", "none",     "safe_disable", []),
        ("telemetry_collector",    0, "A", "none",     "safe_disable", []),
        ("health_monitor",         0, "A", "none",     "safe_disable", []),
        ("error_handler",          0, "A", "none",     "safe_disable", []),
        ("system_health",          0, "B", "none",     "safe_disable", ["health_monitor"]),
        ("self_diagnostic",        0, "B", "none",     "degrade",      ["health_monitor"]),
        ("alert_manager",          0, "C", "none",     "safe_disable", ["logging_manager"]),
        ("notification_manager",   0, "C", "none",     "safe_disable", ["logging_manager"]),

        # ---- Layer 1 – Data Foundation ----
        ("database_manager",       1, "A", "none",     "isolate",      ["config_manager"]),
        ("ingestion_pipeline",     1, "A", "indirect", "degrade",      ["database_manager"]),
        ("data_stream",            1, "A", "indirect", "degrade",      ["ingestion_pipeline"]),
        ("schema_validator",       1, "B", "none",     "safe_disable", ["database_manager"]),
        ("staleness_detector",     1, "B", "indirect", "safe_disable", ["data_stream"]),
        ("connectivity_manager",   1, "A", "indirect", "degrade",      ["config_manager"]),
        ("realtime_processor",     1, "A", "indirect", "degrade",      ["data_stream"]),
        ("cache_manager",          1, "B", "none",     "safe_disable", ["database_manager"]),
        ("trading_calendar",       1, "B", "indirect", "safe_disable", ["config_manager"]),
        ("alternative_data",       1, "C", "indirect", "safe_disable", ["connectivity_manager"]),
        ("sentiment_engine",       1, "C", "indirect", "safe_disable", ["connectivity_manager"]),
        ("macro_data",             1, "C", "indirect", "safe_disable", ["connectivity_manager"]),

        # ---- Layer 2 – Intelligence Core ----
        ("ml_pipeline",            2, "A", "indirect", "degrade",      ["database_manager", "ingestion_pipeline"]),
        ("ai_core",                2, "A", "indirect", "degrade",      ["ml_pipeline"]),
        ("brain_core",             2, "B", "indirect", "degrade",      ["ai_core"]),
        ("cognitive_core",         2, "B", "indirect", "degrade",      ["brain_core"]),
        ("reasoning_engine",       2, "B", "indirect", "degrade",      ["cognitive_core"]),
        ("world_model",            2, "B", "indirect", "degrade",      ["ai_core", "data_stream"]),
        ("meta_learner",           2, "C", "indirect", "degrade",      ["ml_pipeline"]),
        ("rl_engine",              2, "C", "indirect", "degrade",      ["ml_pipeline"]),
        ("adaptive_systems",       2, "B", "indirect", "degrade",      ["ml_pipeline"]),
        ("sentiment_processor",    2, "B", "indirect", "safe_disable", ["sentiment_engine"]),
        ("aamis_v3",               2, "B", "indirect", "degrade",      ["ai_core", "brain_core"]),
        ("intelligence_core",      2, "B", "indirect", "degrade",      ["ai_core"]),
        ("tamic",                  2, "B", "indirect", "degrade",      ["ai_core"]),
        ("hivemind",               2, "D", "indirect", "degrade",      ["ai_core"]),
        ("sentient_core",          2, "D", "indirect", "degrade",      ["ai_core", "connectivity_manager"]),

        # ---- Layer 3 – Signal Generation ----
        ("alpha_engine",           3, "A", "indirect", "degrade",      ["ai_core", "data_stream"]),
        ("strategy_engine",        3, "A", "indirect", "degrade",      ["alpha_engine", "indicators"]),
        ("analysis_engine",        3, "A", "indirect", "degrade",      ["data_stream", "indicators"]),
        ("indicators",             3, "A", "indirect", "safe_disable", ["data_stream"]),
        ("signal_generator",       3, "A", "indirect", "degrade",      ["strategy_engine", "analysis_engine"]),
        ("deepchart",              3, "B", "indirect", "degrade",      ["data_stream", "indicators"]),
        ("market_intelligence",    3, "A", "indirect", "degrade",      ["alpha_engine", "deepchart"]),
        ("opportunity_scanner",    3, "B", "indirect", "safe_disable", ["signal_generator"]),
        ("elite_ai_system",        3, "B", "indirect", "degrade",      ["alpha_engine", "brain_core"]),
        ("systems_ai",             3, "B", "indirect", "degrade",      ["signal_generator"]),
        ("decision_layer",         3, "A", "direct",   "isolate",      ["signal_generator", "market_intelligence"]),
        ("alpha_research",         3, "B", "indirect", "degrade",      ["alpha_engine"]),

        # ---- Layer 4 – Risk & Safety  (VETO LAYER) ----
        ("msos",                   4, "A", "direct",   "emergency",    ["config_manager", "database_manager"]),
        ("risk_manager",           4, "A", "direct",   "emergency",    ["msos"]),
        ("safety_manager",         4, "A", "direct",   "emergency",    ["msos"]),
        ("reality_gates",          4, "A", "direct",   "emergency",    ["risk_manager", "safety_manager"]),
        ("hedge_fund_safety",      4, "A", "direct",   "emergency",    ["risk_manager"]),
        ("stealth_safety",         4, "B", "direct",   "isolate",      ["safety_manager"]),
        ("risk_unified",           4, "A", "direct",   "emergency",    ["risk_manager", "msos"]),

        # ---- Layer 5 – Execution ----
        ("broker_adapter",         5, "A", "direct",   "emergency",    ["risk_manager", "reality_gates", "config_manager"]),
        ("order_manager",          5, "A", "direct",   "emergency",    ["broker_adapter", "risk_manager"]),
        ("fill_tracker",           5, "A", "direct",   "isolate",      ["order_manager"]),
        ("portfolio_manager",      5, "A", "direct",   "isolate",      ["database_manager", "risk_manager"]),
        ("position_manager",       5, "A", "direct",   "isolate",      ["portfolio_manager", "fill_tracker"]),
        ("execution_engine",       5, "A", "direct",   "emergency",    ["order_manager", "fill_tracker", "risk_manager"]),
        ("smart_order_router",     5, "A", "direct",   "emergency",    ["broker_adapter", "execution_engine"]),
        ("market_making",          5, "B", "direct",   "isolate",      ["execution_engine"]),
        ("institutional_entry",    5, "B", "direct",   "isolate",      ["execution_engine", "market_intelligence"]),
        ("hedge_fund",             5, "B", "direct",   "isolate",      ["execution_engine", "risk_manager"]),
        ("wealth_manager",         5, "C", "direct",   "isolate",      ["portfolio_manager"]),
        ("profit_maximizer",       5, "B", "direct",   "isolate",      ["portfolio_manager", "risk_manager"]),

        # ---- Layer 6 – Governance ----
        ("audit_logger",           6, "A", "none",     "safe_disable", ["database_manager", "logging_manager"]),
        ("compliance_monitor",     6, "A", "none",     "safe_disable", ["audit_logger"]),
        ("approval_engine",        6, "A", "direct",   "isolate",      ["audit_logger", "risk_manager"]),
        ("governance_manager",     6, "A", "none",     "safe_disable", ["audit_logger", "compliance_monitor"]),
        ("explainability",         6, "B", "none",     "safe_disable", ["audit_logger"]),
        ("validation_manager",     6, "A", "indirect", "degrade",      ["schema_validator"]),
        ("security_manager",       6, "A", "none",     "degrade",      ["config_manager"]),
        ("anti_rogue_ai",          6, "A", "none",     "safe_disable", ["governance_manager"]),
        ("human_layer",            6, "A", "direct",   "isolate",      ["approval_engine", "audit_logger"]),
        ("surveillance_monitor",   6, "B", "none",     "safe_disable", ["audit_logger"]),

        # ---- Layer 7 – Orchestration ----
        ("event_bus",              7, "A", "indirect", "degrade",      ["config_manager", "logging_manager"]),
        ("background_services",    7, "A", "indirect", "degrade",      ["event_bus"]),
        ("scheduled_runner",       7, "B", "indirect", "degrade",      ["event_bus"]),
        ("reporting_engine",       7, "C", "none",     "safe_disable", ["database_manager", "audit_logger"]),
        ("performance_tracker",    7, "B", "none",     "safe_disable", ["database_manager"]),
        ("analytics_manager",      7, "C", "none",     "safe_disable", ["database_manager"]),
        ("dashboard_server",       7, "C", "none",     "safe_disable", ["reporting_engine"]),
        ("trade_journal",          7, "B", "none",     "safe_disable", ["database_manager", "audit_logger"]),
        ("system_supervisor",      7, "A", "indirect", "degrade",      ["health_monitor", "event_bus"]),
        ("master_orchestrator",    7, "A", "indirect", "degrade",      [
            "system_supervisor", "event_bus", "risk_manager", "execution_engine",
            "signal_generator", "market_intelligence",
        ]),
    ]

    for entry in KNOWN_SERVICES:
        name, layer, tier, impact, rollback, deps = entry
        # Only include if in registered_names (or no filter set)
        if registered_names is not None and name not in registered_names:
            continue
        node = ServiceNode(
            name=name,
            layer=layer,
            tier=tier,
            capital_impact=impact,
            rollback_class=rollback,
            dependencies=deps,
        )
        graph.add_node(node)

    return graph
