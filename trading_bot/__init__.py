"""
AlphaAlgo Trading System - Unified AI Brain Architecture

This package integrates ALL 2900+ files into ONE coherent AI system.

"Many modules, ONE mind. Many features, ONE purpose. Many files, ONE AI."

ARCHITECTURE:
┌─────────────────────────────────────────────────────────────────────────────┐
│                         UNIFIED AI BRAIN                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    CONSCIOUSNESS LAYER                               │   │
│  │  • Decision Making  • Learning  • Self-Improvement  • Memory        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                  │                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    COGNITIVE LAYER                                   │   │
│  │  • Pattern Recognition  • Reasoning  • Prediction  • Analysis       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                  │                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    OPERATIONAL LAYER                                 │   │
│  │  • Data Ingestion  • Signal Generation  • Execution  • Risk         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                  │                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    SAFETY LAYER (IMMUTABLE)                          │   │
│  │  • Risk Limits  • Circuit Breakers  • Human Override  • Fail-Safe   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

QUICK START:
    from trading_bot import UnifiedAIBrain, BrainConfig
    
    brain = UnifiedAIBrain(BrainConfig(mode="paper"))
    await brain.awaken()
    thought = await brain.think("BTCUSDT", market_data)
    await brain.run()

IMMUTABLE PRINCIPLES:
1. RISK FIRST: Safety layer has VETO power over all decisions
2. HUMAN CONTROL: Human override ALWAYS works
3. FAIL-SAFE: Default to NO TRADE when uncertain
4. SURVIVAL: "AlphaAlgo does not try to win. AlphaAlgo tries to not die."

"""

# Layer 7: Infrastructure & Orchestration (ONLY layer exposed at package level)
try:
    from .infrastructure.orchestration import SystemOrchestrator
    from .infrastructure.config import InfrastructureConfigManager as ConfigManager
    from .reporting.logger import init_logger as setup_logging
    
    # NEW: Unified Orchestration System
    from .orchestration import (
        MasterOrchestrator,
        OrchestratorConfig,
        get_orchestrator,
        initialize_orchestrator
    )
    from .registry import (
        ModuleRegistry,
        get_registry,
        initialize_registry
    )
    from .events import (
        BaseEvent,
        MarketEvent,
        PriceUpdateEvent,
        SignalEvent,
        OrderEvent,
        EventHandler
    )
    
    # Essential constants only
    from .constants import (
        VERSION_STRING,
        DEFAULT_RISK_PERCENTAGE,
        MAX_DRAWDOWN_PERCENTAGE,
        DEFAULT_STOP_LOSS_PIPS,
        DEFAULT_TAKE_PROFIT_PIPS
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).warning(f'Infrastructure layer not available: {e}')
    
    # Fallback minimal interface
    class SystemOrchestrator:
        """
        SystemOrchestrator class.

    Auto-documented by QwenCodeMender.
        """
        def __init__(self, config=None):
            self.config = config or {}
        async def start(self):
            """
            start function.

    Auto-documented by QwenCodeMender.
            """
            raise RuntimeError("Infrastructure layer not properly configured")
    
    class MasterOrchestrator:
        """Fallback MasterOrchestrator."""
        def __init__(self, config=None):
            self.config = config or {}
        async def initialize(self):
            raise RuntimeError("Orchestration system not available")
    
    class OrchestratorConfig:
        """Fallback OrchestratorConfig."""
        pass
    
    def get_orchestrator():
        raise RuntimeError("Orchestration system not available")
    
    def initialize_orchestrator(config=None):
        raise RuntimeError("Orchestration system not available")
    
    class ModuleRegistry:
        """Fallback ModuleRegistry."""
        pass
    
    def get_registry():
        raise RuntimeError("Registry system not available")
    
    def initialize_registry():
        raise RuntimeError("Registry system not available")
    
    class BaseEvent:
        """Fallback BaseEvent."""
        pass
    
    class ConfigManager:
        """
        ConfigManager class.

    Auto-documented by QwenCodeMender.
        """
        @staticmethod
        def load():
            """
            load function.

    Auto-documented by QwenCodeMender.
            """
            return {}
    
    def setup_logging(level="INFO"):
        """
        setup_logging function.

    Args:
        level: Description

    Returns:
        Result of operation
        """
        logging.basicConfig(level=getattr(logging, level, logging.INFO))

# Import Unified AI Brain (THE ONE SYSTEM)
try:
    from .unified_ai_brain import (
        UnifiedAIBrain,
        BrainConfig,
        BrainState,
        BrainStatus,
        Thought,
        Memory,
        DecisionType,
        ConfidenceLevel,
        SubsystemCategory,
        create_brain,
        quick_start,
        SUBSYSTEM_REGISTRY
    )
except ImportError as e:
    logging.getLogger(__name__).warning(f'Unified AI Brain not available: {e}')
    UnifiedAIBrain = None
    BrainConfig = None

# Clean exports - Unified AI Brain + orchestration layer
__all__ = [
    # Unified AI Brain (PRIMARY)
    'UnifiedAIBrain',
    'BrainConfig',
    'BrainState',
    'BrainStatus',
    'Thought',
    'Memory',
    'DecisionType',
    'ConfidenceLevel',
    'SubsystemCategory',
    'create_brain',
    'quick_start',
    'SUBSYSTEM_REGISTRY',
    # NEW: Unified Orchestration System
    'MasterOrchestrator',
    'OrchestratorConfig',
    'get_orchestrator',
    'initialize_orchestrator',
    'ModuleRegistry',
    'get_registry',
    'initialize_registry',
    'BaseEvent',
    'MarketEvent',
    'PriceUpdateEvent',
    'SignalEvent',
    'OrderEvent',
    'EventHandler',
    # Legacy orchestration
    'SystemOrchestrator',
    'ConfigManager', 
    'setup_logging',
    'VERSION_STRING',
    'DEFAULT_RISK_PERCENTAGE',
    'MAX_DRAWDOWN_PERCENTAGE'
]

# Layer access documentation
__doc__ += """

LAYER ACCESS PATTERNS:
- Layer 1 (Data): from trading_bot.data import DataManager
- Layer 2 (Signals): from trading_bot.signals import SignalEngine  
- Layer 3 (Strategy): from trading_bot.strategy import StrategyController
- Layer 4 (Risk): from trading_bot.risk import RiskManager
- Layer 5 (Execution): from trading_bot.execution import ExecutionEngine
- Layer 6 (Monitoring): from trading_bot.monitoring import MonitoringSystem
- Layer 7 (Orchestration): from trading_bot import SystemOrchestrator

FORBIDDEN PATTERNS:
- Cross-layer imports (e.g., signals importing from execution)
- Circular dependencies between any layers
- Direct instantiation of lower layers from higher layers
"""