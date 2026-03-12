"""
Orchestration Layer - Unified system orchestration and coordination.
"""

from .master_orchestrator import MasterOrchestrator, OrchestratorConfig
from .service_managers import (
    ServiceManager,
    DataServiceManager,
    AnalysisServiceManager,
    TradingServiceManager,
    RiskServiceManager,
    OptimizationServiceManager
)
from .event_bus import EventBus, Event, EventHandler

__all__ = [
    'MasterOrchestrator',
    'OrchestratorConfig',
    'ServiceManager',
    'DataServiceManager',
    'AnalysisServiceManager',
    'TradingServiceManager',
    'RiskServiceManager',
    'OptimizationServiceManager',
    'EventBus',
    'Event',
    'EventHandler'
]

# Global orchestrator instance
_orchestrator = None

def get_orchestrator() -> MasterOrchestrator:
    """Get the global master orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MasterOrchestrator()
    return _orchestrator

async def initialize_orchestrator(config: OrchestratorConfig = None) -> MasterOrchestrator:
    """Initialize the global orchestrator."""
    orchestrator = get_orchestrator()
    await orchestrator.initialize(config)
    return orchestrator
