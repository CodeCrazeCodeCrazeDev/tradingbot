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

import logging

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
    logging.getLogger(__name__).info(f'Infrastructure layer not available: {e}')
    
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
    logging.getLogger(__name__).info(f'Unified AI Brain not available: {e}')
    UnifiedAIBrain = None
    BrainConfig = None

# Import integration layer (professional module lifecycle integration)
try:
    from .integration import (
        # Professional engine (authoritative lifecycle owner)
        MasterIntegrationEngine,
        EngineConfig,
        EngineState,
        get_engine,
        reset_engine,
        # Verification + registry primitives
        VerificationPipeline,
        ModuleRegistry,
        get_module_registry,
        # Backward-compatible legacy integrator
        MasterIntegrator,
        get_master_integrator,
        IntegrationPhase,
    )

    async def integrate_all_modules(config=None):
        """Integrate trading_bot modules using the professional integration engine."""
        raw_config = config or {}

        # Build EngineConfig using only known fields; ignore unknowns safely.
        engine_config = EngineConfig(
            health_check_interval_s=raw_config.get('health_check_interval_s', 30.0),
            health_check_timeout_s=raw_config.get('health_check_timeout_s', 5.0),
            fail_fast_on_tier_a=raw_config.get('fail_fast_on_tier_a', True),
            max_start_retries=raw_config.get('max_start_retries', 2),
            retry_delay_s=raw_config.get('retry_delay_s', 2.0),
            block_direct_impact_without_risk=raw_config.get('block_direct_impact_without_risk', True),
            state_file=raw_config.get('state_file', 'alphaalgo_data/engine_state.json'),
            startup_wave_order=raw_config.get('startup_wave_order', [0, 1, 4, 5, 2, 3, 6, 7]),
        )

        # Singleton engine + clean state for repeatable integrations.
        reset_engine()
        engine = get_engine(config=engine_config)

        # Professional hierarchical bootstrap:
        # modules -> frameworks -> systems -> orchestration.
        module_limit = raw_config.get('module_limit')
        bootstrap_summary = await engine.bootstrap_hierarchical(max_modules=module_limit)

        # Optional verification pass for stricter professional flows.
        if raw_config.get('run_verification', False):
            verifier = VerificationPipeline()
            verification_report = await verifier.run_full_verification(engine)
            return {
                'engine': engine,
                'bootstrap': bootstrap_summary,
                'verification': verification_report,
            }

        return {
            'engine': engine,
            'bootstrap': bootstrap_summary,
        }

except ImportError as e:
    logging.getLogger(__name__).info(f'Integration layer not available: {e}')
    MasterIntegrationEngine = None
    EngineConfig = None
    EngineState = None
    VerificationPipeline = None
    MasterIntegrator = None
    IntegrationPhase = None

    def get_engine(config=None):
        raise RuntimeError('Integration layer not available')

    def reset_engine():
        raise RuntimeError('Integration layer not available')

    def get_master_integrator(config=None):
        raise RuntimeError('Integration layer not available')

    async def integrate_all_modules(config=None):
        raise RuntimeError('Integration layer not available')

# Import Meta-Governance Layer (Agent Optimization and Safety)
try:
    from .meta_governance import (
        MetaAgentGovernanceLayer,
        AgentType,
        ChangeCategory,
        ChangeType,
        UnderperformanceType,
        AgentPerformance,
        ForbiddenChangeAttempt,
        CandidateUpgrade,
        ValidationCriteria,
        ValidationResult,
        create_meta_agent_governance_layer,
    )
except ImportError as e:
    logging.getLogger(__name__).info(f'Meta-governance layer not available: {e}')
    MetaAgentGovernanceLayer = None
    AgentType = None
    ChangeCategory = None
    ChangeType = None
    UnderperformanceType = None
    AgentPerformance = None
    ForbiddenChangeAttempt = None
    CandidateUpgrade = None
    ValidationCriteria = None
    ValidationResult = None
    create_meta_agent_governance_layer = None

# Production golden path (decision gate, parity runner, monitoring, security audit)
try:
    from .golden_path import (
        AccountContext,
        AgentTrapDefenseConfig,
        AgentTrapScanner,
        DecisionGateConfig,
        GoldenPathTradingRunner,
        MarketContext,
        ModelPerformanceMonitor,
        ModelVote,
        PredictionSample,
        RiskContext,
        TradeDecision,
        TradeDecisionValidator,
        TradeIntent,
        TradingMode,
        TrapCategory,
        audit_local_secrets,
    )
except ImportError as e:
    logging.getLogger(__name__).info(f'Golden path layer not available: {e}')
    AccountContext = None
    AgentTrapDefenseConfig = None
    AgentTrapScanner = None
    DecisionGateConfig = None
    GoldenPathTradingRunner = None
    MarketContext = None
    ModelPerformanceMonitor = None
    ModelVote = None
    PredictionSample = None
    RiskContext = None
    TradeDecision = None
    TradeDecisionValidator = None
    TradeIntent = None
    TradingMode = None
    TrapCategory = None
    audit_local_secrets = None

# AEAN governed meta-intelligence layer
try:
    from .aean_meta_intelligence_layer import (
        AEANConstraints,
        AEANMetaIntelligenceLayer,
        BenchmarkResult as AEANBenchmarkResult,
        BenchmarkTask as AEANBenchmarkTask,
        CapabilityCandidate as AEANCapabilityCandidate,
        DeploymentDecision as AEANDeploymentDecision,
        FrontierObservation,
        MonitoringResult as AEANMonitoringResult,
        ValidationResult as AEANValidationResult,
        create_aean_meta_intelligence_layer,
    )
except ImportError as e:
    logging.getLogger(__name__).info(f'AEAN meta-intelligence layer not available: {e}')
    AEANConstraints = None
    AEANMetaIntelligenceLayer = None
    AEANBenchmarkResult = None
    AEANBenchmarkTask = None
    AEANCapabilityCandidate = None
    AEANDeploymentDecision = None
    FrontierObservation = None
    AEANMonitoringResult = None
    AEANValidationResult = None
    create_aean_meta_intelligence_layer = None

# Universal Action Layer / Claw
try:
    from .universal_action_layer import (
        ActionIntent,
        ActionPolicy,
        ActionResult,
        ActionRiskTier,
        ActionStatus,
        ActionType,
        CommandActionAdapter,
        DecisionBundle,
        DecisionConstraints,
        ExecutionStatus,
        FeedbackReport,
        FunctionActionAdapter,
        GovernanceSignature,
        GovernanceReceipt,
        UniversalActionLayer,
        WorkflowActionAdapter,
        sign_decision_bundle,
        create_universal_action_layer,
    )
except ImportError as e:
    logging.getLogger(__name__).info(f'Universal action layer not available: {e}')
    ActionIntent = None
    ActionPolicy = None
    ActionResult = None
    ActionRiskTier = None
    ActionStatus = None
    ActionType = None
    CommandActionAdapter = None
    DecisionBundle = None
    DecisionConstraints = None
    ExecutionStatus = None
    FeedbackReport = None
    FunctionActionAdapter = None
    GovernanceSignature = None
    GovernanceReceipt = None
    UniversalActionLayer = None
    WorkflowActionAdapter = None
    sign_decision_bundle = None
    create_universal_action_layer = None

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
    # Module integration
    'MasterIntegrationEngine',
    'EngineConfig',
    'EngineState',
    'get_engine',
    'reset_engine',
    'VerificationPipeline',
    'MasterIntegrator',
    'IntegrationPhase',
    'get_master_integrator',
    'integrate_all_modules',
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
    'MAX_DRAWDOWN_PERCENTAGE',
    # NEW: Meta-Agent Governance Layer
    'MetaAgentGovernanceLayer',
    'AgentType',
    'ChangeCategory',
    'ChangeType',
    'UnderperformanceType',
    'AgentPerformance',
    'ForbiddenChangeAttempt',
    'CandidateUpgrade',
    'ValidationCriteria',
    'ValidationResult',
    'create_meta_agent_governance_layer',
    # Production golden path
    'AccountContext',
    'AgentTrapDefenseConfig',
    'AgentTrapScanner',
    'DecisionGateConfig',
    'GoldenPathTradingRunner',
    'MarketContext',
    'ModelPerformanceMonitor',
    'ModelVote',
    'PredictionSample',
    'RiskContext',
    'TradeDecision',
    'TradeDecisionValidator',
    'TradeIntent',
    'TradingMode',
    'TrapCategory',
    'audit_local_secrets',
    # AEAN governed meta-intelligence
    'AEANConstraints',
    'AEANMetaIntelligenceLayer',
    'AEANBenchmarkResult',
    'AEANBenchmarkTask',
    'AEANCapabilityCandidate',
    'AEANDeploymentDecision',
    'FrontierObservation',
    'AEANMonitoringResult',
    'AEANValidationResult',
    'create_aean_meta_intelligence_layer',
    # Universal Action Layer / Claw
    'ActionIntent',
    'ActionPolicy',
    'ActionResult',
    'ActionRiskTier',
    'ActionStatus',
    'ActionType',
    'CommandActionAdapter',
    'DecisionBundle',
    'DecisionConstraints',
    'ExecutionStatus',
    'FeedbackReport',
    'FunctionActionAdapter',
    'GovernanceSignature',
    'GovernanceReceipt',
    'UniversalActionLayer',
    'WorkflowActionAdapter',
    'sign_decision_bundle',
    'create_universal_action_layer',
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
