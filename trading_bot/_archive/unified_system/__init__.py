"""
Unified Trading System - Master Integration Package

This package provides the complete unified architecture that integrates all 177+ modules
into a cohesive, production-ready trading system following the 11-layer architecture.

Architecture Layers:
- Layer 0: Infrastructure & Hardware (OS, Network, GPU/TPU)
- Layer 1: Observability & Health (Logging, Metrics, Tracing, Alerting)
- Layer 2: Connectivity & Ingestion (Exchange connectors, Data feeds, Time sync)
- Layer 3: Data Foundation (Normalized data, Feature stores, Event enrichment)
- Layer 4: Intelligence Core (ML/AI, MoE, Meta-learning, RL)
- Layer 5: Signal Generation (Multi-strategy, Regime-conditioned, Opportunity scanning)
- Layer 6: Risk & Safety (Pre-trade checks, VaR/CVaR, Circuit breakers, Kill switches)
- Layer 7: Decision Verification (Multi-agent debate, Adversarial validation)
- Layer 8: Execution (Order routing, Fill tracking, Slippage control)
- Layer 9: Orchestration & Meta-control (Master orchestrator, Mode switching)
- Layer 10: Governance & Human Control (G0/G1/G2 hierarchy, Audit, Kill-switch)

Total Codebase:
- 177 modules
- 3,121 files
- ~1,494,642 lines of code

Usage:
    from trading_bot.unified_system import UnifiedMasterSystem, quick_start
    
    # Quick start
    system = await quick_start(config={'mode': 'paper', 'symbols': ['BTCUSDT']})
    
    # Or manual initialization
    system = UnifiedMasterSystem()
    await system.initialize()
    await system.start()
"""

from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

# Lazy imports to avoid circular dependencies
_master_system = None
_layer_registry = None


def get_master_system():
    """Get or create the master system singleton"""
    global _master_system
    if _master_system is None:
        from .master_system import UnifiedMasterSystem
        _master_system = UnifiedMasterSystem()
    return _master_system


def get_layer_registry():
    """Get or create the layer registry singleton"""
    global _layer_registry
    if _layer_registry is None:
        from .layer_registry import LayerRegistry
        _layer_registry = LayerRegistry()
    return _layer_registry


async def quick_start(config: Optional[Dict[str, Any]] = None) -> 'UnifiedMasterSystem':
    """
    Quick start the unified trading system
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Initialized and running UnifiedMasterSystem
    """
    from .master_system import UnifiedMasterSystem
    
    system = UnifiedMasterSystem(config or {})
    await system.initialize()
    return system


# Export key classes when imported
try:
    from .master_system import UnifiedMasterSystem
    from .layer_registry import LayerRegistry, LayerInfo
    from .layer_interfaces import (
        ILayer,
        IInfrastructureLayer,
        IObservabilityLayer,
        IConnectivityLayer,
        IDataFoundationLayer,
        IIntelligenceLayer,
        ISignalLayer,
        IRiskSafetyLayer,
        IDecisionLayer,
        IExecutionLayer,
        IOrchestrationLayer,
        IGovernanceLayer,
    )
    from .unified_config import UnifiedConfig, LayerConfig
    from .unified_types import (
        SystemStatus,
        LayerStatus,
        TradingMode,
        MarketRegime,
        RiskLevel,
        SignalStrength,
    )
except ImportError as e:
    logger.debug(f"Optional imports not yet available: {e}")


__all__ = [
    # Core classes
    'UnifiedMasterSystem',
    'LayerRegistry',
    'LayerInfo',
    'UnifiedConfig',
    'LayerConfig',
    
    # Interfaces
    'ILayer',
    'IInfrastructureLayer',
    'IObservabilityLayer',
    'IConnectivityLayer',
    'IDataFoundationLayer',
    'IIntelligenceLayer',
    'ISignalLayer',
    'IRiskSafetyLayer',
    'IDecisionLayer',
    'IExecutionLayer',
    'IOrchestrationLayer',
    'IGovernanceLayer',
    
    # Types
    'SystemStatus',
    'LayerStatus',
    'TradingMode',
    'MarketRegime',
    'RiskLevel',
    'SignalStrength',
    
    # Functions
    'quick_start',
    'get_master_system',
    'get_layer_registry',
]
