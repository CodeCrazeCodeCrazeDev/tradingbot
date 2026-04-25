"""
Decision Governance System (DGS)
==================================

A self-auditing epistemic governance system for autonomous trading.

Core Components:
- 7 Governance Layers (claim construction through final arbitration)
- 3 Memory Systems (decision, outcome, failure)
- 3 Operational Planes (real-time, offline research, controlled evolution)
- NEW: Signal Validator, Risk Gatekeeper, Execution Engine
- NEW: Meta-Learning Judge, Audit Logger
- NEW: Multi-Hypothesis Generator, Causal Attribution
- NEW: Statistical Validation, Cost-Adjusted Expectancy
- NEW: Multi-Agent Validation, Safety Enforcer, Diagnostic Engine
- Capability Discovery Engine (continuous self-improvement)

Usage:
    from trading_bot.decision_governance import DecisionGovernanceSystem
    
    dgs = DecisionGovernanceSystem()
    await dgs.start()
    
    # Evaluate trade signal
    decision, record, metadata = await dgs.evaluate_trade_signal(
        signal={'confidence': 0.8, 'direction': 'buy'},
        symbol='AAPL',
        current_regime=market_regime,
        market_data={...}
    )
    
    if decision == GovernanceDecision.APPROVE:
        # Execute trade
        pass
    
    # Record outcome
    result = await dgs.record_trade_outcome(
        decision_id=record.id,
        pnl=0.05,
        market_context={...}
    )
"""

# Core types
from .core_types import (
    # Enums
    GovernanceDecision,
    ClaimType,
    EvidenceStatus,
    UncertaintyType,
    RegimeDimension,
    
    # Data classes
    Claim,
    Evidence,
    AdversarialChallenge,
    MarketRegime,
    UncertaintyProfile,
    ExecutionFeasibility,
    DecisionRecord,
    OutcomeRecord,
    FailurePattern,
    CapabilityHypothesis,
    
    # NEW: Advanced engines
    OpportunityCost,
    OpportunityCostEngine,
    CapitalSurvivalMetrics,
    CapitalSurvivalPriorityEngine,
    
    # Exceptions
    DGSException,
    ValidationError,
    GovernanceRejection
)

# Layer 1: Claim Graph Constructor
from .layer1_claim_graph import ClaimGraphConstructor

# Layer 2: Evidence Sufficiency Auditor
from .layer2_evidence_auditor import EvidenceSufficiencyAuditor

# Layer 3: Adversarial Counter-Analyst
from .layer3_adversarial_analyst import AdversarialCounterAnalyst

# Layer 4: Regime Applicability Engine
from .layer4_regime_engine import RegimeApplicabilityEngine

# Layer 5: Counterfactual Simulator
from .layer5_counterfactual import CounterfactualSimulator

# Layer 6: Uncertainty and Calibration Layer
from .layer6_uncertainty import (
    UncertaintyCalibrationLayer,
    ConfidenceCalibrationEngine,
    MetaUncertaintyController
)

# Layer 7: Governance Arbiter
from .layer7_arbiter import GovernanceArbiter, GovernanceCriteria

# NEW: Core Components
from .signal_validator import SignalValidator, SignalValidationResult, SignalValidationError
from .risk_gatekeeper import RiskGatekeeper, RiskLimits, RiskCheckResult, RiskViolationType
from .execution_engine import ExecutionFeasibilityEngine, ExecutionEstimate
from .meta_learning_judge import MetaLearningJudge, OptimizationLevel, OptimizationProposal
from .audit_logger import AuditLogger, AuditEventType, AuditEntry

# NEW: Advanced Analysis
from .multi_hypothesis import (
    MultiHypothesisGenerator, 
    CrossStrategyArbitrator, 
    TradingHypothesis, 
    EnsembleConsensus,
    HypothesisSource
)
from .causal_attribution import CausalAttributionEngine, CausalAttribution, CausalFactor
from .statistical_validator import PreTradeStatisticalValidator, StatisticalValidation, StatisticalTestResult
from .cost_expectancy import CostAdjustedExpectancyModel, CostAdjustedExpectancy, TradingCosts
from .multi_agent_validation import MultiAgentValidationSystem, AgentValidation, EnsembleConsensus as AgentEnsembleConsensus

# NEW: Safety & Diagnostics
from .safety_enforcer import SafetyEnforcer, SafetyEnforcementConfig, SafetyViolation, SafetyViolationType
from .diagnostic_engine import DiagnosticIntrospectionEngine, FailureDiagnosis, DiagnosticInsight

# Three-Memory System
from .memory_system import (
    DecisionMemory,
    OutcomeMemory,
    FailureMemory
)

# Three Planes
from .plane_realtime import RealtimeDecisionGovernancePlane
from .plane_offline import OfflineResearchPlane
from .plane_evolution import ControlledEvolutionPlane, PromotionGate

# Capability Discovery Engine
from .capability_discovery import CapabilityDiscoveryEngine, CapabilityDiscoveryAndIntegrationEngine

# Continuous Capability Discovery Engine
from .continuous_capability_discovery import (
    ContinuousCapabilityDiscoveryEngine,
    CapabilityStatus,
    InnovationStage,
    CapabilityNode,
    CapabilityGap,
    InnovationProposal,
    ConstraintProfile,
    PerformanceBaseline,
    create_continuous_discovery_engine,
)

# Introspection-Driven Evolution Engine
from .introspection_evolution import (
    IntrospectionDrivenEvolutionEngine,
    RootCauseCategory,
    FixComplexity,
    CausalFactor,
    Explanation,
    PrescribedFix,
    IntrospectionResult,
    EvolutionLoopRecord,
    create_introspection_evolution_engine,
)

# Self-Inspection and Meta-Learning Engine
from .self_inspection import (
    SelfInspectionEngine,
    InspectionCategory,
    FindingSeverity,
    InspectionFinding,
    DecisionQualityMetrics,
    CalibrationProfile,
    ImprovementOpportunity,
    create_self_inspection_engine,
)

# Unified Financial Intelligence System
from .unified_intelligence import (
    UnifiedFinancialIntelligenceSystem,
    SystemPhase,
    IntelligenceMetrics,
    BottleneckAnalysis,
    CompoundingEvent,
    create_financial_intelligence_system,
)

# Trading Simulator for Safe Self-Testing
from .trading_simulator import (
    MarketSimulator,
    MarketRegime,
    SimulatedTrade,
    SimulationState,
    ScenarioConfig,
    TradingSimulatorIntegration,
    create_trading_simulator_integration,
)

# EXPANDED: Multi-Agent Debate System
from .multi_agent_debate import (
    MultiAgentDebateSystem,
    DebateRole,
    DebateStatus,
    ArgumentType,
    Argument,
    DebateRound,
    AgentBelief,
    DebateResult,
    DebatingAgent,
    create_debate_system,
)

# EXPANDED: Experiment Management
from .experiment_management import (
    ExperimentManager,
    Experiment,
    ExperimentStage,
    ExperimentType,
    ResourceLimits,
    StageResult,
    ABTestConfig,
    ABTestResult,
    BanditArm,
    create_experiment_manager,
)

# EXPANDED: Cognition Store
from .cognition_store import (
    CognitionStore,
    KnowledgeType,
    KnowledgeSource,
    KnowledgeEmbedding,
    KnowledgeMetadata,
    KnowledgeEntry,
    KnowledgeGraph,
    create_cognition_store,
)

# EXPANDED: Cross-Domain Knowledge Transfer
from .cross_domain_transfer import (
    CrossDomainTransferSystem,
    SourceDomain,
    TransferType,
    TransferStatus,
    DomainMapping,
    TransferredKnowledge,
    TransferProposal,
    DomainAdapter,
    create_cross_domain_transfer_system,
)

# Main Integration
from .integration import DecisionGovernanceSystem

__version__ = "2.0.0"

__all__ = [
    # Main integration
    'DecisionGovernanceSystem',
    
    # Core types
    'GovernanceDecision',
    'ClaimType',
    'EvidenceStatus',
    'UncertaintyType',
    'Claim',
    'Evidence',
    'AdversarialChallenge',
    'MarketRegime',
    'UncertaintyProfile',
    'ExecutionFeasibility',
    'DecisionRecord',
    'OutcomeRecord',
    'FailurePattern',
    'CapabilityHypothesis',
    'OpportunityCost',
    'OpportunityCostEngine',
    'CapitalSurvivalMetrics',
    'CapitalSurvivalPriorityEngine',
    'DGSException',
    'ValidationError',
    'GovernanceRejection',
    
    # Layers
    'ClaimGraphConstructor',
    'EvidenceSufficiencyAuditor',
    'AdversarialCounterAnalyst',
    'RegimeApplicabilityEngine',
    'CounterfactualSimulator',
    'UncertaintyCalibrationLayer',
    'ConfidenceCalibrationEngine',
    'MetaUncertaintyController',
    'GovernanceArbiter',
    'GovernanceCriteria',
    
    # NEW: Core Components
    'SignalValidator',
    'SignalValidationResult',
    'SignalValidationError',
    'RiskGatekeeper',
    'RiskLimits',
    'RiskCheckResult',
    'RiskViolationType',
    'ExecutionFeasibilityEngine',
    'ExecutionEstimate',
    'MetaLearningJudge',
    'OptimizationLevel',
    'OptimizationProposal',
    'AuditLogger',
    'AuditEventType',
    'AuditEntry',
    
    # NEW: Advanced Analysis
    'MultiHypothesisGenerator',
    'CrossStrategyArbitrator',
    'TradingHypothesis',
    'EnsembleConsensus',
    'HypothesisSource',
    'CausalAttributionEngine',
    'CausalAttribution',
    'CausalFactor',
    'PreTradeStatisticalValidator',
    'StatisticalValidation',
    'StatisticalTestResult',
    'CostAdjustedExpectancyModel',
    'CostAdjustedExpectancy',
    'TradingCosts',
    'MultiAgentValidationSystem',
    'AgentValidation',
    
    # NEW: Safety & Diagnostics
    'SafetyEnforcer',
    'SafetyEnforcementConfig',
    'SafetyViolation',
    'SafetyViolationType',
    'DiagnosticIntrospectionEngine',
    'FailureDiagnosis',
    'DiagnosticInsight',
    
    # Memory
    'DecisionMemory',
    'OutcomeMemory',
    'FailureMemory',
    
    # Planes
    'RealtimeDecisionGovernancePlane',
    'OfflineResearchPlane',
    'ControlledEvolutionPlane',
    'PromotionGate',
    
    # Capability Discovery (Legacy and New)
    'CapabilityDiscoveryEngine',
    'CapabilityDiscoveryAndIntegrationEngine',
    'ContinuousCapabilityDiscoveryEngine',
    'CapabilityStatus',
    'InnovationStage',
    'CapabilityNode',
    'CapabilityGap',
    'InnovationProposal',
    'ConstraintProfile',
    'PerformanceBaseline',
    'create_continuous_discovery_engine',
    
    # Introspection-Driven Evolution
    'IntrospectionDrivenEvolutionEngine',
    'RootCauseCategory',
    'FixComplexity',
    'CausalFactor',
    'Explanation',
    'PrescribedFix',
    'IntrospectionResult',
    'EvolutionLoopRecord',
    'create_introspection_evolution_engine',
    
    # Self-Inspection and Meta-Learning
    'SelfInspectionEngine',
    'InspectionCategory',
    'FindingSeverity',
    'InspectionFinding',
    'DecisionQualityMetrics',
    'CalibrationProfile',
    'ImprovementOpportunity',
    'create_self_inspection_engine',
    
    # Unified Financial Intelligence System
    'UnifiedFinancialIntelligenceSystem',
    'SystemPhase',
    'IntelligenceMetrics',
    'BottleneckAnalysis',
    'CompoundingEvent',
    'create_financial_intelligence_system',
    
    # Trading Simulator
    'MarketSimulator',
    'MarketRegime',
    'SimulatedTrade',
    'SimulationState',
    'ScenarioConfig',
    'TradingSimulatorIntegration',
    'create_trading_simulator_integration',
    
    # EXPANDED: Multi-Agent Debate
    'MultiAgentDebateSystem',
    'DebateRole',
    'DebateStatus',
    'ArgumentType',
    'Argument',
    'DebateRound',
    'AgentBelief',
    'DebateResult',
    'DebatingAgent',
    'create_debate_system',
    
    # EXPANDED: Experiment Management
    'ExperimentManager',
    'Experiment',
    'ExperimentStage',
    'ExperimentType',
    'ResourceLimits',
    'StageResult',
    'ABTestConfig',
    'ABTestResult',
    'BanditArm',
    'create_experiment_manager',
    
    # EXPANDED: Cognition Store
    'CognitionStore',
    'KnowledgeType',
    'KnowledgeSource',
    'KnowledgeEmbedding',
    'KnowledgeMetadata',
    'KnowledgeEntry',
    'KnowledgeGraph',
    'create_cognition_store',
    
    # EXPANDED: Cross-Domain Transfer
    'CrossDomainTransferSystem',
    'SourceDomain',
    'TransferType',
    'TransferStatus',
    'DomainMapping',
    'TransferredKnowledge',
    'TransferProposal',
    'DomainAdapter',
    'create_cross_domain_transfer_system',
]
