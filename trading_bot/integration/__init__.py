"""
AlphaAlgo World-Class Integration Layer
========================================
Single authoritative integration package for the trading bot.

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

import logging

logger = logging.getLogger(__name__)

# Core integration engine
from .master_engine import (
    MasterIntegrationEngine,
    EngineConfig,
    EngineState,
    get_engine,
    reset_engine,
)

# Module registry
from .module_registry import (
    ModuleRegistry,
    ModuleRecord,
    ModuleLayer,
    ModuleTier,
    PromotionState,
    CapitalImpact,
    RollbackClass,
    get_module_registry,
)

# Service contract
from .service_contract import (
    IntegratedService,
    LegacyModuleAdapter,
    StubService,
    ServiceLifecycle,
    HealthStatus,
    HealthReport,
    ServiceEvent,
)

# Dependency graph
from .dependency_graph import (
    DependencyGraph,
    ServiceNode,
    build_default_graph,
    DependencyCycle,
    MissingDependency,
)

# Verification
from .verification import (
    VerificationPipeline,
    VerificationReport,
    VerificationResult,
    StaticVerifier,
    ContractVerifier,
    RuntimeVerifier,
)

# Master Integrator - new unified integration system
try:
    from .master_integrator import (
        MasterIntegrator,
        EventBus,
        Event,
        EventType,
        ServiceWrapper,
        IntegrationPhase,
        get_master_integrator,
        quick_start,
    )
except ImportError:
    MasterIntegrator = None  # type: ignore
    EventBus = None  # type: ignore
    Event = None  # type: ignore
    EventType = None  # type: ignore
    ServiceWrapper = None  # type: ignore
    IntegrationPhase = None  # type: ignore
    get_master_integrator = None  # type: ignore
    quick_start = None  # type: ignore

# Legacy shims — preserve existing imports from rest of codebase
try:
    from .internet_integration import InternetIntegration, create_internet_integration
except ImportError:
    InternetIntegration = None           # type: ignore
    create_internet_integration = None   # type: ignore

try:
    from .market_analysis_dashboard import (
        DashboardConfig,
        MarketAnalysisDashboard,
        create_market_analysis_dashboard,
    )
except ImportError:
    DashboardConfig = None                  # type: ignore
    MarketAnalysisDashboard = None          # type: ignore
    create_market_analysis_dashboard = None # type: ignore


class IntegrationOrchestrator:
    """
    Backward-compatible shim.
    New code should use MasterIntegrationEngine directly.
    """
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get("config", {})
        self._engine: MasterIntegrationEngine = get_engine()
        self.running = False

    async def start(self):
        await self._engine.start_all()
        self.running = True

    async def stop(self):
        await self._engine.stop_all()
        self.running = False

    def get_status(self):
        return self._engine.engine_health_report()


__all__ = [
    # Engine
    "MasterIntegrationEngine",
    "EngineConfig",
    "EngineState",
    "get_engine",
    "reset_engine",
    # Registry
    "ModuleRegistry",
    "ModuleRecord",
    "ModuleLayer",
    "ModuleTier",
    "PromotionState",
    "CapitalImpact",
    "RollbackClass",
    "get_module_registry",
    # Contract
    "IntegratedService",
    "LegacyModuleAdapter",
    "StubService",
    "ServiceLifecycle",
    "HealthStatus",
    "HealthReport",
    "ServiceEvent",
    # Graph
    "DependencyGraph",
    "ServiceNode",
    "build_default_graph",
    "DependencyCycle",
    "MissingDependency",
    # Verification
    "VerificationPipeline",
    "VerificationReport",
    "VerificationResult",
    "StaticVerifier",
    "ContractVerifier",
    "RuntimeVerifier",
    # Master Integrator
    "MasterIntegrator",
    "EventBus",
    "Event",
    "EventType",
    "ServiceWrapper",
    "IntegrationPhase",
    "get_master_integrator",
    "quick_start",
    # Legacy shims
    "IntegrationOrchestrator",
    "InternetIntegration",
    "create_internet_integration",
    "DashboardConfig",
    "MarketAnalysisDashboard",
    "create_market_analysis_dashboard",
]
