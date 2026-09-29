"""
AlphaAlgo World-Class Integration Layer
========================================
Single authoritative integration package for the trading bot.

Names resolve lazily (PEP 562): the heavy leaves (``internet_integration``
pulls aiohttp+aiodns, ``market_analysis_dashboard`` pulls pandas) only load
when actually accessed. Submodule imports (``trading_bot.integration.X``)
are unaffected.

Public surface:
  - MasterIntegrationEngine   : single authority for service lifecycle
  - EngineConfig              : engine runtime configuration
  - get_engine                : singleton accessor
  - ModuleRegistry            : canonical module inventory
  - get_module_registry       : singleton accessor
  - IntegratedService         : base class for all promoted services
  - LegacyModuleAdapter       : wraps any raw module object
  - StubService               : no-op placeholder
  - DependencyGraph           : service dependency DAG
  - build_default_graph       : pre-wired dependency graph
  - VerificationPipeline      : static + contract + runtime verification
  - PromotionState            : module promotion lifecycle enum
  - ModuleLayer               : 8-layer architecture enum
  - ModuleTier                : A/B/C/D quality tier enum
"""

import importlib as _importlib
import logging

logger = logging.getLogger(__name__)

_LAZY = {
    # Engine
    "MasterIntegrationEngine": ".master_engine",
    "EngineConfig": ".master_engine",
    "EngineState": ".master_engine",
    "get_engine": ".master_engine",
    "reset_engine": ".master_engine",
    # Registry
    "ModuleRegistry": ".module_registry",
    "ModuleRecord": ".module_registry",
    "ModuleLayer": ".module_registry",
    "ModuleTier": ".module_registry",
    "PromotionState": ".module_registry",
    "CapitalImpact": ".module_registry",
    "RollbackClass": ".module_registry",
    "get_module_registry": ".module_registry",
    # Contract
    "IntegratedService": ".service_contract",
    "LegacyModuleAdapter": ".service_contract",
    "StubService": ".service_contract",
    "ServiceLifecycle": ".service_contract",
    "HealthStatus": ".service_contract",
    "HealthReport": ".service_contract",
    "ServiceEvent": ".service_contract",
    # Graph
    "DependencyGraph": ".dependency_graph",
    "ServiceNode": ".dependency_graph",
    "build_default_graph": ".dependency_graph",
    "DependencyCycle": ".dependency_graph",
    "MissingDependency": ".dependency_graph",
    # Verification
    "VerificationPipeline": ".verification",
    "VerificationReport": ".verification",
    "VerificationResult": ".verification",
    "StaticVerifier": ".verification",
    "ContractVerifier": ".verification",
    "RuntimeVerifier": ".verification",
    # Master Integrator
    "MasterIntegrator": ".master_integrator",
    "EventBus": ".master_integrator",
    "Event": ".master_integrator",
    "EventType": ".master_integrator",
    "ServiceWrapper": ".master_integrator",
    "IntegrationPhase": ".master_integrator",
    "get_master_integrator": ".master_integrator",
    "quick_start": ".master_integrator",
    # Legacy shims
    "InternetIntegration": ".internet_integration",
    "create_internet_integration": ".internet_integration",
    "DashboardConfig": ".market_analysis_dashboard",
    "MarketAnalysisDashboard": ".market_analysis_dashboard",
    "create_market_analysis_dashboard": ".market_analysis_dashboard",
}


class IntegrationOrchestrator:
    """
    Backward-compatible shim.
    New code should use MasterIntegrationEngine directly.
    """
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get("config", {})
        import warnings
        warnings.warn(
            "IntegrationOrchestrator is a merge-generated stub and is deprecated. "
            "Route orchestration through CognitiveSystemController "
            "(trading_bot.core.csc.controller).",
            DeprecationWarning, stacklevel=2,
        )
        self._engine = __getattr__("get_engine")()
        self.running = False

    async def start(self):
        await self._engine.start_all()
        self.running = True

    async def stop(self):
        await self._engine.stop_all()
        self.running = False

    def get_status(self):
        return self._engine.engine_health_report()


__all__ = list(_LAZY) + ["IntegrationOrchestrator"]


_OPTIONAL = {".master_integrator", ".internet_integration", ".market_analysis_dashboard"}


def __getattr__(name):
    mod = _LAZY.get(name)
    if mod is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    try:
        return getattr(_importlib.import_module(mod, __name__), name)
    except ImportError:
        if mod in _OPTIONAL:
            return None  # optional dependency absent — mirrors old try/except None-shim
        raise


def __dir__():
    return sorted(__all__)
