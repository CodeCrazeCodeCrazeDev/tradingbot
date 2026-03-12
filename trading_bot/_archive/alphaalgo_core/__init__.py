"""
alphaalgo_core package
"""

try:
    # Original AlphaAlgo Core components
    from .alphaalgo_orchestrator import (
        AlphaAlgoConfig,
        AlphaAlgoOrchestrator,
        create_alphaalgo,
        quick_start
    )
    from .broker_hub import (
        BrokerAdapter,
        BrokerConnection,
        BrokerCredentials,
        BrokerHub,
        BrokerType,
        ConnectionStatus,
        CredentialVault,
        SimulationBrokerAdapter
    )
    from .central_controller import (
        ActionType,
        ApprovalRequest,
        ApprovalStatus,
        CentralController,
        G0_HumanAuthority,
        G1_Controller,
        G2_MiniAI,
        GovernanceLevel,
        create_alphaalgo_controller,
        retry
    )
    from .data_pipeline import (
        DataPoint,
        DataQuality,
        DataSource,
        DataSourceConfig,
        DataSourceStatus,
        DataType,
        FreeDataSource,
        Level2DataSource,
        MacroDataSource,
        SentimentDataSource,
        UnifiedDataPipeline,
        retry
    )
    from .fail_safe import (
        FailSafeSystem,
        SafetyCheck,
        SafetyCheckResult,
        SystemHealth,
        SystemStatus,
        TradingMode,
        create_fail_safe
    )
    from .governance_system import (
        ChangeCategory,
        GovernanceLevel,
        GovernanceSystem,
        ProposedChange
    )
    from .mini_ai_factory import (
        ArchitectureAnalyzerAI,
        BaseMiniAI,
        BrokerConnectorAI,
        DataCleanerAI,
        FeatureEngineerAI,
        L2InterpreterAI,
        MiniAIFactory,
        MiniAIRole,
        MiniAITask,
        RiskValidatorAI,
        SecurityGuardianAI,
        SentimentParserAI,
        StrategyTesterAI,
        retry
    )
    from .security_core import (
        SecretVault,
        SecurityCore,
        SecurityEvent,
        ThreatDetector,
        ThreatLevel,
        ThreatType
    )
    from .self_repair import (
        ArchitectureAnalyzer,
        ArchitectureIssue,
        IssueSeverity,
        IssueType,
        ProposalType,
        RepairProposal,
        SelfRepairEngine
    )
    
    # Capital Governance System components
    from .capital_governance import (
        CapitalGovernanceSystem,
        CapitalGovernanceResult,
        GovernanceLayer,
        MarketPhysicsResult,
        StrategyZooResult,
        AssumptionDecompilerResult,
        RegimeHostilityResult,
        ExposureControllerResult,
        AntiLearningResult,
        ValidationMonitorResult,
        MarketStructureState,
        StrategyState,
        RegimeState,
        ExposureState,
        ValidationState,
        StrategyAssumption,
        HostileCondition
    )
    from .market_physics_filter import MarketPhysicsFilter
    from .strategy_zoo import StrategyZoo
    from .assumption_decompiler import AssumptionDecompiler
    from .regime_hostility_engine import RegimeHostilityEngine
    from .exposure_controller import ExposureController
    from .anti_learning_firewall import AntiLearningFirewall, ExtremeEventType
    from .continuous_validity_monitor import ContinuousValidityMonitor, DeviationType
    from .alphaalgo_core import AlphaAlgoCore, create_alphaalgo_core
    from .integration import (
        AlphaAlgoCoreIntegration,
        MasterOrchestratorIntegration,
        PortfolioRiskManagerIntegration,
        TradingEngineIntegration,
        create_integration
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in alphaalgo_core: {e}')

__all__ = [
    # Original AlphaAlgo Core components
    'ActionType',
    'AlphaAlgoConfig',
    'AlphaAlgoOrchestrator',
    'ApprovalRequest',
    'ApprovalStatus',
    'ArchitectureAnalyzer',
    'ArchitectureAnalyzerAI',
    'ArchitectureIssue',
    'BaseMiniAI',
    'BrokerAdapter',
    'BrokerConnection',
    'BrokerConnectorAI',
    'BrokerCredentials',
    'BrokerHub',
    'BrokerType',
    'CentralController',
    'ChangeCategory',
    'ConnectionStatus',
    'CredentialVault',
    'DataCleanerAI',
    'DataPoint',
    'DataQuality',
    'DataSource',
    'DataSourceConfig',
    'DataSourceStatus',
    'DataType',
    'FailSafeSystem',
    'FeatureEngineerAI',
    'FreeDataSource',
    'G0_HumanAuthority',
    'G1_Controller',
    'G2_MiniAI',
    'GovernanceLevel',
    'GovernanceSystem',
    'IssueSeverity',
    'IssueType',
    'L2InterpreterAI',
    'Level2DataSource',
    'MacroDataSource',
    'MiniAIFactory',
    'MiniAIRole',
    'MiniAITask',
    'ProposalType',
    'ProposedChange',
    'RepairProposal',
    'RiskValidatorAI',
    'SafetyCheck',
    'SafetyCheckResult',
    'SecretVault',
    'SecurityCore',
    'SecurityEvent',
    'SecurityGuardianAI',
    'SelfRepairEngine',
    'SentimentDataSource',
    'SentimentParserAI',
    'SimulationBrokerAdapter',
    'StrategyTesterAI',
    'SystemHealth',
    'SystemStatus',
    'ThreatDetector',
    'ThreatLevel',
    'ThreatType',
    'TradingMode',
    'UnifiedDataPipeline',
    'create_alphaalgo',
    'create_alphaalgo_controller',
    'create_fail_safe',
    'quick_start',
    'retry',
    
    # Capital Governance System components
    'AlphaAlgoCore',
    'AlphaAlgoCoreIntegration',
    'AntiLearningFirewall',
    'AntiLearningResult',
    'AssumptionDecompiler',
    'AssumptionDecompilerResult',
    'CapitalGovernanceResult',
    'CapitalGovernanceSystem',
    'ContinuousValidityMonitor',
    'DeviationType',
    'ExposureController',
    'ExposureControllerResult',
    'ExposureState',
    'ExtremeEventType',
    'GovernanceLayer',
    'HostileCondition',
    'MarketPhysicsFilter',
    'MarketPhysicsResult',
    'MarketStructureState',
    'MasterOrchestratorIntegration',
    'PortfolioRiskManagerIntegration',
    'RegimeHostilityEngine',
    'RegimeHostilityResult',
    'RegimeState',
    'StrategyAssumption',
    'StrategyState',
    'StrategyZoo',
    'StrategyZooResult',
    'TradingEngineIntegration',
    'ValidationMonitorResult',
    'ValidationState',
    'create_alphaalgo_core',
    'create_integration',
]