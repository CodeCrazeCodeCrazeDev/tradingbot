"""
Service Factory - Instantiates and Registers All Services
==========================================================

Central factory for creating and registering all trading bot services.
Follows the 8-layer architecture with proper dependency ordering.

ARCHITECTURE LAYERS (startup order):
- Layer 0: Infrastructure (health, monitoring, logging)
- Layer 1: Data Foundation (database, connectivity, data feeds)
- Layer 2: Risk & Safety (MSOS, risk management) - HIGHEST PRIORITY
- Layer 3: Intelligence (ML, AI, cognitive)
- Layer 4: Signal Generation (alpha, strategy, analysis)
- Layer 5: Execution (brokers, orders, positions)
- Layer 6: Governance (compliance, audit, approval)
- Layer 7: Orchestration (event pipeline, coordination)

IMMUTABLE PRINCIPLES:
1. RISK FIRST: Risk services have VETO power over all trades
2. HUMAN CONTROL: Human override ALWAYS works
3. FAIL-SAFE: Default to NO TRADE when uncertain
"""

import logging
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass, field
from enum import Enum

from trading_bot.core.service_registry import (
    ServiceRegistry, BaseService, ServicePriority
)
from trading_bot.core.event_bus import EventBus

logger = logging.getLogger(__name__)


class ServiceLayer(Enum):
    """Service architecture layers"""
    INFRASTRUCTURE = 0
    DATA_FOUNDATION = 1
    RISK_SAFETY = 2      # CRITICAL - Has veto power
    INTELLIGENCE = 3
    SIGNAL_GENERATION = 4
    EXECUTION = 5
    GOVERNANCE = 6
    ORCHESTRATION = 7


@dataclass
class ServiceDefinition:
    """Definition of a service to be created"""
    name: str
    service_class: str  # Full import path
    layer: ServiceLayer
    priority: ServicePriority
    dependencies: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    critical: bool = False  # If True, system won't start without it


# =============================================================================
# TIER 1: CORE SERVICES (Must have for trading)
# =============================================================================

TIER1_SERVICES: List[ServiceDefinition] = [
    # -------------------------------------------------------------------------
    # LAYER 0: INFRASTRUCTURE
    # -------------------------------------------------------------------------
    ServiceDefinition(
        name="monitoring",
        service_class="trading_bot.services.diagnostics_service.DiagnosticsService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.CRITICAL,
        dependencies=[],
        critical=True,
    ),
    
    # -------------------------------------------------------------------------
    # LAYER 1: DATA FOUNDATION
    # -------------------------------------------------------------------------
    ServiceDefinition(
        name="database",
        service_class="trading_bot.services.database_service.DatabaseService",
        layer=ServiceLayer.DATA_FOUNDATION,
        priority=ServicePriority.CRITICAL,
        dependencies=[],
        critical=True,
    ),
    ServiceDefinition(
        name="connectivity",
        service_class="trading_bot.services.connectivity_service.ConnectivityService",
        layer=ServiceLayer.DATA_FOUNDATION,
        priority=ServicePriority.CRITICAL,
        dependencies=["database"],
        critical=True,
    ),
    ServiceDefinition(
        name="data_feeds",
        service_class="trading_bot.services.data_feeds_service.DataFeedsService",
        layer=ServiceLayer.DATA_FOUNDATION,
        priority=ServicePriority.HIGH,
        dependencies=["connectivity"],
    ),
    ServiceDefinition(
        name="data_sources",
        service_class="trading_bot.services.data_sources_service.DataSourcesService",
        layer=ServiceLayer.DATA_FOUNDATION,
        priority=ServicePriority.HIGH,
        dependencies=["connectivity"],
    ),
    ServiceDefinition(
        name="data",
        service_class="trading_bot.services.data_service.DataService",
        layer=ServiceLayer.DATA_FOUNDATION,
        priority=ServicePriority.HIGH,
        dependencies=["database", "data_feeds"],
    ),
    
    # -------------------------------------------------------------------------
    # LAYER 2: RISK & SAFETY (CRITICAL - Has veto power)
    # -------------------------------------------------------------------------
    ServiceDefinition(
        name="msos",
        service_class="trading_bot.services.msos_service.MSOSService",
        layer=ServiceLayer.RISK_SAFETY,
        priority=ServicePriority.CRITICAL,
        dependencies=["database"],
        critical=True,
    ),
    ServiceDefinition(
        name="risk",
        service_class="trading_bot.services.risk_service.RiskService",
        layer=ServiceLayer.RISK_SAFETY,
        priority=ServicePriority.CRITICAL,
        dependencies=["database", "msos"],
        critical=True,
    ),
    
    # -------------------------------------------------------------------------
    # LAYER 3: INTELLIGENCE
    # -------------------------------------------------------------------------
    ServiceDefinition(
        name="advanced_ml",
        service_class="trading_bot.services.advanced_ml_service.AdvancedMLService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.HIGH,
        dependencies=["data"],
    ),
    ServiceDefinition(
        name="ai_core",
        service_class="trading_bot.services.ai_core_service.AICoreService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.HIGH,
        dependencies=["data"],
    ),
    ServiceDefinition(
        name="cognitive_architecture",
        service_class="trading_bot.services.cognitive_architecture_service.CognitiveArchitectureService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["data"],
    ),
    
    # -------------------------------------------------------------------------
    # LAYER 4: SIGNAL GENERATION
    # -------------------------------------------------------------------------
    ServiceDefinition(
        name="analysis",
        service_class="trading_bot.services.analysis_service.AnalysisService",
        layer=ServiceLayer.SIGNAL_GENERATION,
        priority=ServicePriority.HIGH,
        dependencies=["data"],
    ),
    ServiceDefinition(
        name="alpha_engine",
        service_class="trading_bot.services.alpha_engine_service.AlphaEngineService",
        layer=ServiceLayer.SIGNAL_GENERATION,
        priority=ServicePriority.HIGH,
        dependencies=["analysis"],
    ),
    ServiceDefinition(
        name="signals",
        service_class="trading_bot.services.signals_service.SignalsService",
        layer=ServiceLayer.SIGNAL_GENERATION,
        priority=ServicePriority.HIGH,
        dependencies=["analysis"],
    ),
    
    # -------------------------------------------------------------------------
    # LAYER 5: EXECUTION
    # -------------------------------------------------------------------------
    ServiceDefinition(
        name="broker",
        service_class="trading_bot.services.broker_service.BrokerService",
        layer=ServiceLayer.EXECUTION,
        priority=ServicePriority.CRITICAL,
        dependencies=["connectivity"],
        critical=True,
    ),
    ServiceDefinition(
        name="brokers",
        service_class="trading_bot.services.brokers_service.BrokersService",
        layer=ServiceLayer.EXECUTION,
        priority=ServicePriority.HIGH,
        dependencies=["broker"],
    ),
    ServiceDefinition(
        name="execution",
        service_class="trading_bot.services.execution_service.ExecutionService",
        layer=ServiceLayer.EXECUTION,
        priority=ServicePriority.CRITICAL,
        dependencies=["broker", "risk"],
        critical=True,
    ),
    
    # -------------------------------------------------------------------------
    # LAYER 6: GOVERNANCE
    # -------------------------------------------------------------------------
    ServiceDefinition(
        name="compliance",
        service_class="trading_bot.services.compliance_service.ComplianceService",
        layer=ServiceLayer.GOVERNANCE,
        priority=ServicePriority.HIGH,
        dependencies=["database"],
    ),
    ServiceDefinition(
        name="audit",
        service_class="trading_bot.services.audit_service.AuditService",
        layer=ServiceLayer.GOVERNANCE,
        priority=ServicePriority.NORMAL,
        dependencies=["database"],
    ),
    ServiceDefinition(
        name="approval",
        service_class="trading_bot.services.approval_service.ApprovalService",
        layer=ServiceLayer.GOVERNANCE,
        priority=ServicePriority.HIGH,
        dependencies=["risk"],
    ),
    ServiceDefinition(
        name="intelligence_directorate",
        service_class="trading_bot.services.intelligence_directorate_service.IntelligenceDirectorateService",
        layer=ServiceLayer.GOVERNANCE,
        priority=ServicePriority.NORMAL,
        dependencies=["audit", "approval", "compliance"],
        critical=True,
    ),
    
    # -------------------------------------------------------------------------
    # LAYER 7: ORCHESTRATION
    # -------------------------------------------------------------------------
    ServiceDefinition(
        name="decision_layer",
        service_class="trading_bot.services.decision_layer_service.DecisionLayerService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.CRITICAL,
        dependencies=["analysis", "risk", "msos"],
        critical=True,
    ),
]


# =============================================================================
# TIER 2: ENHANCED SERVICES (Add significant value)
# =============================================================================

TIER2_SERVICES: List[ServiceDefinition] = [
    # AAMIS V3
    ServiceDefinition(
        name="aamis_v3",
        service_class="trading_bot.services.aamis_service.AAMISService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["data"],
    ),
    # Adaptive Systems
    ServiceDefinition(
        name="adaptive_systems",
        service_class="trading_bot.services.adaptive_service.AdaptiveSystemsService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["ml"],
    ),
    # Advanced AI
    ServiceDefinition(
        name="advanced_ai",
        service_class="trading_bot.services.advanced_ai_service.AdvancedAIService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["ai_core"],
    ),
    # Advanced Analysis
    ServiceDefinition(
        name="advanced_analysis",
        service_class="trading_bot.services.advanced_analysis_service.AdvancedAnalysisService",
        layer=ServiceLayer.SIGNAL_GENERATION,
        priority=ServicePriority.NORMAL,
        dependencies=["analysis"],
    ),
    # Advanced Features
    ServiceDefinition(
        name="advanced_features",
        service_class="trading_bot.services.advanced_features_service.AdvancedFeaturesService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["ml"],
    ),
    # AlphaAlgo Core
    ServiceDefinition(
        name="alphaalgo_core",
        service_class="trading_bot.services.alphaalgo_core_service.AlphaAlgoCoreService",
        layer=ServiceLayer.GOVERNANCE,
        priority=ServicePriority.HIGH,
        dependencies=["risk"],
    ),
    # AlphaAlgo V2
    ServiceDefinition(
        name="alphaalgo_v2",
        service_class="trading_bot.services.alphaalgo_v2_service.AlphaAlgoV2Service",
        layer=ServiceLayer.GOVERNANCE,
        priority=ServicePriority.NORMAL,
        dependencies=["alphaalgo_core"],
    ),
    # Alpha Research
    ServiceDefinition(
        name="alpha_research",
        service_class="trading_bot.services.alpha_research_service.AlphaResearchService",
        layer=ServiceLayer.SIGNAL_GENERATION,
        priority=ServicePriority.LOW,
        dependencies=["alpha_engine"],
    ),
    # Backtesting
    ServiceDefinition(
        name="backtesting",
        service_class="trading_bot.services.backtesting_service.BacktestingService",
        layer=ServiceLayer.SIGNAL_GENERATION,
        priority=ServicePriority.LOW,
        dependencies=["data", "analysis"],
    ),
    # DeepChart
    ServiceDefinition(
        name="deepchart",
        service_class="trading_bot.services.deepchart_service.DeepChartService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["data"],
    ),
    # Analytics
    ServiceDefinition(
        name="analytics",
        service_class="trading_bot.services.analytics_service.AnalyticsService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.NORMAL,
        dependencies=["database"],
    ),
    # Quant Analysis
    ServiceDefinition(
        name="quant_analysis",
        service_class="trading_bot.services.quant_analysis_service.QuantAnalysisService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["data"],
    ),
    # Dashboard
    ServiceDefinition(
        name="dashboard",
        service_class="trading_bot.services.dashboard_service.DashboardService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.LOW,
        dependencies=["analytics"],
    ),
    # Autonomous
    ServiceDefinition(
        name="autonomous",
        service_class="trading_bot.services.autonomous_service.AutonomousService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["ml", "risk"],
    ),
    # Autonomous Learner
    ServiceDefinition(
        name="autonomous_learner",
        service_class="trading_bot.services.autonomous_learner_service.AutonomousLearnerService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["autonomous"],
    ),
]


# =============================================================================
# TIER 3: ADDITIONAL SERVICES (More modules)
# =============================================================================

TIER3_SERVICES: List[ServiceDefinition] = [
    # Brain Service
    ServiceDefinition(
        name="brain",
        service_class="trading_bot.services.brain_service.BrainService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["ml"],
    ),
    # Hivemind Service
    ServiceDefinition(
        name="hivemind",
        service_class="trading_bot.services.hivemind_service.HivemindService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["brain"],
    ),
    # Elite AI System
    ServiceDefinition(
        name="elite_ai",
        service_class="trading_bot.services.elite_ai_service.EliteAIService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["ai_core"],
    ),
    # Market Intelligence
    ServiceDefinition(
        name="market_intelligence",
        service_class="trading_bot.services.market_intelligence_service.MarketIntelligenceService",
        layer=ServiceLayer.SIGNAL_GENERATION,
        priority=ServicePriority.NORMAL,
        dependencies=["analysis"],
    ),
    # Portfolio Service
    ServiceDefinition(
        name="portfolio",
        service_class="trading_bot.services.portfolio_service.PortfolioService",
        layer=ServiceLayer.EXECUTION,
        priority=ServicePriority.HIGH,
        dependencies=["execution", "risk"],
    ),
    # Position Service
    ServiceDefinition(
        name="position",
        service_class="trading_bot.services.position_service.PositionService",
        layer=ServiceLayer.EXECUTION,
        priority=ServicePriority.HIGH,
        dependencies=["broker"],
    ),
    # Performance Service
    ServiceDefinition(
        name="performance",
        service_class="trading_bot.services.performance_service.PerformanceService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.NORMAL,
        dependencies=["database"],
    ),
    # Optimization Service
    ServiceDefinition(
        name="optimization",
        service_class="trading_bot.services.optimization_service.OptimizationService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["backtesting"],
    ),
    # Strategy Service
    ServiceDefinition(
        name="strategy",
        service_class="trading_bot.services.strategy_service.StrategyService",
        layer=ServiceLayer.SIGNAL_GENERATION,
        priority=ServicePriority.HIGH,
        dependencies=["signals"],
    ),
    # Indicators Service
    ServiceDefinition(
        name="indicators",
        service_class="trading_bot.services.indicators_service.IndicatorsService",
        layer=ServiceLayer.SIGNAL_GENERATION,
        priority=ServicePriority.NORMAL,
        dependencies=["data"],
    ),
    # Sentiment Service
    ServiceDefinition(
        name="sentiment",
        service_class="trading_bot.services.sentiment_service.SentimentService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["data"],
    ),
    # Notifications Service
    ServiceDefinition(
        name="notifications",
        service_class="trading_bot.services.notifications_service.NotificationsService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.LOW,
        dependencies=[],
    ),
    # Monitoring Service
    ServiceDefinition(
        name="system_monitoring",
        service_class="trading_bot.services.monitoring_service.MonitoringService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.HIGH,
        dependencies=[],
    ),
    # Telemetry Service
    ServiceDefinition(
        name="telemetry",
        service_class="trading_bot.services.telemetry_service.TelemetryService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.NORMAL,
        dependencies=[],
    ),
    # Security Service
    ServiceDefinition(
        name="security",
        service_class="trading_bot.services.security_service.SecurityService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.HIGH,
        dependencies=[],
    ),
]


# =============================================================================
# TIER 4: COMPLETE SYSTEM SERVICES (All remaining modules)
# =============================================================================

TIER4_SERVICES: List[ServiceDefinition] = [
    # Elite AI System
    ServiceDefinition(
        name="elite_ai_system",
        service_class="trading_bot.services.elite_ai_service.EliteAIService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["ai_core"],
    ),
    # Elite System
    ServiceDefinition(
        name="elite_system",
        service_class="trading_bot.services.elite_system_service.EliteSystemService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["brain"],
    ),
    # Error Handling
    ServiceDefinition(
        name="error_handling",
        service_class="trading_bot.services.error_handling_service.ErrorHandlingService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.CRITICAL,
        dependencies=[],
    ),
    # Eternal Evolution
    ServiceDefinition(
        name="eternal_evolution",
        service_class="trading_bot.services.tier4_services.EternalEvolutionService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["ml"],
    ),
    # Event Monitoring
    ServiceDefinition(
        name="event_monitoring",
        service_class="trading_bot.services.tier4_services.EventMonitoringService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.HIGH,
        dependencies=[],
    ),
    # Event Pipeline
    ServiceDefinition(
        name="event_pipeline",
        service_class="trading_bot.services.tier4_services.EventPipelineService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.HIGH,
        dependencies=[],
    ),
    # Evolution Layer
    ServiceDefinition(
        name="evolution_layer",
        service_class="trading_bot.services.tier4_services.EvolutionLayerService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["ml"],
    ),
    # Exit Strategies
    ServiceDefinition(
        name="exit_strategies",
        service_class="trading_bot.services.tier4_services.ExitStrategiesService",
        layer=ServiceLayer.EXECUTION,
        priority=ServicePriority.HIGH,
        dependencies=["execution"],
    ),
    # Explainability
    ServiceDefinition(
        name="explainability",
        service_class="trading_bot.services.tier4_services.ExplainabilityService",
        layer=ServiceLayer.GOVERNANCE,
        priority=ServicePriority.NORMAL,
        dependencies=["ml"],
    ),
    # Features
    ServiceDefinition(
        name="features",
        service_class="trading_bot.services.tier4_services.FeaturesService",
        layer=ServiceLayer.DATA_FOUNDATION,
        priority=ServicePriority.NORMAL,
        dependencies=["data"],
    ),
    # Filters
    ServiceDefinition(
        name="filters",
        service_class="trading_bot.services.tier4_services.FiltersService",
        layer=ServiceLayer.SIGNAL_GENERATION,
        priority=ServicePriority.NORMAL,
        dependencies=["signals"],
    ),
    # Global Expansion
    ServiceDefinition(
        name="global_expansion",
        service_class="trading_bot.services.tier4_services.GlobalExpansionService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.LOW,
        dependencies=["broker"],
    ),
    # Governance
    ServiceDefinition(
        name="governance",
        service_class="trading_bot.services.tier4_services.GovernanceService",
        layer=ServiceLayer.GOVERNANCE,
        priority=ServicePriority.HIGH,
        dependencies=["compliance"],
    ),
    # Hedge Fund
    ServiceDefinition(
        name="hedge_fund",
        service_class="trading_bot.services.tier4_services.HedgeFundService",
        layer=ServiceLayer.EXECUTION,
        priority=ServicePriority.NORMAL,
        dependencies=["portfolio", "risk"],
    ),
    # HFT
    ServiceDefinition(
        name="hft",
        service_class="trading_bot.services.tier4_services.HFTService",
        layer=ServiceLayer.EXECUTION,
        priority=ServicePriority.HIGH,
        dependencies=["execution"],
    ),
    # Human Layer
    ServiceDefinition(
        name="human_layer",
        service_class="trading_bot.services.tier4_services.HumanLayerService",
        layer=ServiceLayer.GOVERNANCE,
        priority=ServicePriority.HIGH,
        dependencies=["approval"],
    ),
    # Improvement Agent
    ServiceDefinition(
        name="improvement_agent",
        service_class="trading_bot.services.tier4_services.ImprovementAgentService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["autonomous"],
    ),
    # Improvements
    ServiceDefinition(
        name="improvements",
        service_class="trading_bot.services.tier4_services.ImprovementsService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["ml"],
    ),
    # Infrastructure
    ServiceDefinition(
        name="infrastructure",
        service_class="trading_bot.services.tier4_services.InfrastructureService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.CRITICAL,
        dependencies=[],
    ),
    # Ingestion
    ServiceDefinition(
        name="ingestion",
        service_class="trading_bot.services.tier4_services.IngestionService",
        layer=ServiceLayer.DATA_FOUNDATION,
        priority=ServicePriority.HIGH,
        dependencies=["database"],
    ),
    # Innovations
    ServiceDefinition(
        name="innovations",
        service_class="trading_bot.services.tier4_services.InnovationsService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["ml"],
    ),
    # Institutional
    ServiceDefinition(
        name="institutional",
        service_class="trading_bot.services.tier4_services.InstitutionalService",
        layer=ServiceLayer.EXECUTION,
        priority=ServicePriority.NORMAL,
        dependencies=["execution"],
    ),
    # Institutional Entry
    ServiceDefinition(
        name="institutional_entry",
        service_class="trading_bot.services.tier4_services.InstitutionalEntryService",
        layer=ServiceLayer.EXECUTION,
        priority=ServicePriority.NORMAL,
        dependencies=["institutional"],
    ),
    # Integration
    ServiceDefinition(
        name="integration",
        service_class="trading_bot.services.tier4_services.IntegrationService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.HIGH,
        dependencies=[],
    ),
    # Integrations
    ServiceDefinition(
        name="integrations",
        service_class="trading_bot.services.tier4_services.IntegrationsService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.NORMAL,
        dependencies=["integration"],
    ),
    # Intel
    ServiceDefinition(
        name="intel",
        service_class="trading_bot.services.tier4_services.IntelService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["analysis"],
    ),
    # Intelligence
    ServiceDefinition(
        name="intelligence",
        service_class="trading_bot.services.tier4_services.IntelligenceService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.HIGH,
        dependencies=["ml"],
    ),
    # Intelligent Delegation
    ServiceDefinition(
        name="intelligent_delegation",
        service_class="trading_bot.services.tier4_services.IntelligentDelegationService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.NORMAL,
        dependencies=["ai_core"],
    ),
    # Internet Access
    ServiceDefinition(
        name="internet_access",
        service_class="trading_bot.services.tier4_services.InternetAccessService",
        layer=ServiceLayer.DATA_FOUNDATION,
        priority=ServicePriority.NORMAL,
        dependencies=["connectivity"],
    ),
    # Learning
    ServiceDefinition(
        name="learning",
        service_class="trading_bot.services.tier4_services.LearningService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["ml"],
    ),
    # Log System
    ServiceDefinition(
        name="log_system",
        service_class="trading_bot.services.tier4_services.LogSystemService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.HIGH,
        dependencies=[],
    ),
    # Macro
    ServiceDefinition(
        name="macro",
        service_class="trading_bot.services.tier4_services.MacroService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["analysis"],
    ),
    # Market Making
    ServiceDefinition(
        name="market_making",
        service_class="trading_bot.services.tier4_services.MarketMakingService",
        layer=ServiceLayer.EXECUTION,
        priority=ServicePriority.NORMAL,
        dependencies=["execution"],
    ),
    # Market Student
    ServiceDefinition(
        name="market_student",
        service_class="trading_bot.services.tier4_services.MarketStudentService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["learning"],
    ),
    # Market Teacher
    ServiceDefinition(
        name="market_teacher",
        service_class="trading_bot.services.tier4_services.MarketTeacherService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["market_student"],
    ),
    # Meta Learning
    ServiceDefinition(
        name="meta_learning",
        service_class="trading_bot.services.tier4_services.MetaLearningService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["ml"],
    ),
    # Mobile
    ServiceDefinition(
        name="mobile",
        service_class="trading_bot.services.tier4_services.MobileService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.LOW,
        dependencies=["api"],
    ),
    # Mobile App
    ServiceDefinition(
        name="mobile_app",
        service_class="trading_bot.services.tier4_services.MobileAppService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.LOW,
        dependencies=["mobile"],
    ),
    # Models
    ServiceDefinition(
        name="models",
        service_class="trading_bot.services.tier4_services.ModelsService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["ml"],
    ),
    # Multimodal
    ServiceDefinition(
        name="multimodal",
        service_class="trading_bot.services.tier4_services.MultimodalService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["ml"],
    ),
    # Observability
    ServiceDefinition(
        name="observability",
        service_class="trading_bot.services.tier4_services.ObservabilityService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.HIGH,
        dependencies=["monitoring"],
    ),
    # Opportunity Scanner
    ServiceDefinition(
        name="opportunity_scanner",
        service_class="trading_bot.services.tier4_services.OpportunityScannerService",
        layer=ServiceLayer.SIGNAL_GENERATION,
        priority=ServicePriority.HIGH,
        dependencies=["analysis"],
    ),
    # Ops
    ServiceDefinition(
        name="ops",
        service_class="trading_bot.services.tier4_services.OpsService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.NORMAL,
        dependencies=[],
    ),
    # Orchestrator
    ServiceDefinition(
        name="orchestrator",
        service_class="trading_bot.services.tier4_services.OrchestratorService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.CRITICAL,
        dependencies=["decision_layer"],
    ),
]


# =============================================================================
# TIER 5: COMPLETE ECOSYSTEM SERVICES (All remaining modules)
# =============================================================================

TIER5_SERVICES: List[ServiceDefinition] = [
    # Perplexity Trading
    ServiceDefinition(
        name="perplexity_trading",
        service_class="trading_bot.services.tier5_services.PerplexityTradingService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["ml"],
    ),
    # Persistence
    ServiceDefinition(
        name="persistence",
        service_class="trading_bot.services.tier5_services.PersistenceService",
        layer=ServiceLayer.DATA_FOUNDATION,
        priority=ServicePriority.HIGH,
        dependencies=["database"],
    ),
    # Profiling
    ServiceDefinition(
        name="profiling",
        service_class="trading_bot.services.tier5_services.ProfilingService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.LOW,
        dependencies=[],
    ),
    # Profit Maximizer
    ServiceDefinition(
        name="profit_maximizer",
        service_class="trading_bot.services.tier5_services.ProfitMaximizerService",
        layer=ServiceLayer.EXECUTION,
        priority=ServicePriority.HIGH,
        dependencies=["execution", "risk"],
    ),
    # Psychology
    ServiceDefinition(
        name="psychology",
        service_class="trading_bot.services.tier5_services.PsychologyService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=[],
    ),
    # Quality
    ServiceDefinition(
        name="quality",
        service_class="trading_bot.services.tier5_services.QualityService",
        layer=ServiceLayer.GOVERNANCE,
        priority=ServicePriority.NORMAL,
        dependencies=[],
    ),
    # Quantum
    ServiceDefinition(
        name="quantum",
        service_class="trading_bot.services.tier5_services.QuantumService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["ml"],
    ),
    # Qwen Codemender
    ServiceDefinition(
        name="qwen_codemender",
        service_class="trading_bot.services.tier5_services.QwenCodemenderService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["ai_core"],
    ),
    # Reality Gates
    ServiceDefinition(
        name="reality_gates",
        service_class="trading_bot.services.tier5_services.RealityGatesService",
        layer=ServiceLayer.GOVERNANCE,
        priority=ServicePriority.HIGH,
        dependencies=["risk"],
    ),
    # Realtime
    ServiceDefinition(
        name="realtime",
        service_class="trading_bot.services.tier5_services.RealtimeService",
        layer=ServiceLayer.DATA_FOUNDATION,
        priority=ServicePriority.CRITICAL,
        dependencies=["data"],
    ),
    # Reasoning
    ServiceDefinition(
        name="reasoning",
        service_class="trading_bot.services.tier5_services.ReasoningService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["ml"],
    ),
    # Recursive Improvement
    ServiceDefinition(
        name="recursive_improvement",
        service_class="trading_bot.services.tier5_services.RecursiveImprovementService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["autonomous"],
    ),
    # Reporting
    ServiceDefinition(
        name="reporting",
        service_class="trading_bot.services.tier5_services.ReportingService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.NORMAL,
        dependencies=["database"],
    ),
    # Research
    ServiceDefinition(
        name="research",
        service_class="trading_bot.services.tier5_services.ResearchService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["analysis"],
    ),
    # Research Ingestion
    ServiceDefinition(
        name="research_ingestion",
        service_class="trading_bot.services.tier5_services.ResearchIngestionService",
        layer=ServiceLayer.DATA_FOUNDATION,
        priority=ServicePriority.NORMAL,
        dependencies=["ingestion"],
    ),
    # Risk Management
    ServiceDefinition(
        name="risk_management",
        service_class="trading_bot.services.tier5_services.RiskManagementService",
        layer=ServiceLayer.RISK_SAFETY,
        priority=ServicePriority.CRITICAL,
        dependencies=["risk"],
    ),
    # Safety
    ServiceDefinition(
        name="safety",
        service_class="trading_bot.services.tier5_services.SafetyService",
        layer=ServiceLayer.RISK_SAFETY,
        priority=ServicePriority.CRITICAL,
        dependencies=[],
    ),
    # Schemas
    ServiceDefinition(
        name="schemas",
        service_class="trading_bot.services.tier5_services.SchemasService",
        layer=ServiceLayer.DATA_FOUNDATION,
        priority=ServicePriority.HIGH,
        dependencies=[],
    ),
    # Self Assembly AI
    ServiceDefinition(
        name="self_assembly_ai",
        service_class="trading_bot.services.tier5_services.SelfAssemblyAIService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["autonomous"],
    ),
    # Self Concepts
    ServiceDefinition(
        name="self_concepts",
        service_class="trading_bot.services.tier5_services.SelfConceptsService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["ml"],
    ),
    # Self Diagnostic
    ServiceDefinition(
        name="self_diagnostic",
        service_class="trading_bot.services.tier5_services.SelfDiagnosticService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.HIGH,
        dependencies=[],
    ),
    # Self Healing AI
    ServiceDefinition(
        name="self_healing_ai",
        service_class="trading_bot.services.tier5_services.SelfHealingAIService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["autonomous"],
    ),
    # Self Improvement
    ServiceDefinition(
        name="self_improvement",
        service_class="trading_bot.services.tier5_services.SelfImprovementService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["ml"],
    ),
    # Self Learning
    ServiceDefinition(
        name="self_learning",
        service_class="trading_bot.services.tier5_services.SelfLearningService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["learning"],
    ),
    # Self Mastery
    ServiceDefinition(
        name="self_mastery",
        service_class="trading_bot.services.tier5_services.SelfMasteryService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["self_learning"],
    ),
    # Sentient Core (already exists as sentiment, adding sentient)
    ServiceDefinition(
        name="sentient_core",
        service_class="trading_bot.services.tier5_services.SentientCoreService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["autonomous"],
    ),
    # Simulation
    ServiceDefinition(
        name="simulation",
        service_class="trading_bot.services.tier5_services.SimulationService",
        layer=ServiceLayer.SIGNAL_GENERATION,
        priority=ServicePriority.NORMAL,
        dependencies=["backtesting"],
    ),
    # Skills
    ServiceDefinition(
        name="skills",
        service_class="trading_bot.services.tier5_services.SkillsService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["ml"],
    ),
    # Social
    ServiceDefinition(
        name="social",
        service_class="trading_bot.services.tier5_services.SocialService",
        layer=ServiceLayer.DATA_FOUNDATION,
        priority=ServicePriority.LOW,
        dependencies=["data"],
    ),
    # Stealth Safety
    ServiceDefinition(
        name="stealth_safety",
        service_class="trading_bot.services.tier5_services.StealthSafetyService",
        layer=ServiceLayer.RISK_SAFETY,
        priority=ServicePriority.HIGH,
        dependencies=["safety"],
    ),
    # Strategies
    ServiceDefinition(
        name="strategies",
        service_class="trading_bot.services.tier5_services.StrategiesService",
        layer=ServiceLayer.SIGNAL_GENERATION,
        priority=ServicePriority.HIGH,
        dependencies=["signals"],
    ),
    # Streaming
    ServiceDefinition(
        name="streaming",
        service_class="trading_bot.services.tier5_services.StreamingService",
        layer=ServiceLayer.DATA_FOUNDATION,
        priority=ServicePriority.HIGH,
        dependencies=["connectivity"],
    ),
    # Superintelligence
    ServiceDefinition(
        name="superintelligence",
        service_class="trading_bot.services.tier5_services.SuperintelligenceService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["ai_core"],
    ),
    # Superpowerful AI
    ServiceDefinition(
        name="superpowerful_ai",
        service_class="trading_bot.services.tier5_services.SuperpowerfulAIService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["superintelligence"],
    ),
    # Surveillance
    ServiceDefinition(
        name="surveillance",
        service_class="trading_bot.services.tier5_services.SurveillanceService",
        layer=ServiceLayer.GOVERNANCE,
        priority=ServicePriority.HIGH,
        dependencies=["compliance"],
    ),
    # System
    ServiceDefinition(
        name="system",
        service_class="trading_bot.services.tier5_services.SystemService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.CRITICAL,
        dependencies=[],
    ),
    # System Health
    ServiceDefinition(
        name="system_health_service",
        service_class="trading_bot.services.tier5_services.SystemHealthServiceWrapper",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.CRITICAL,
        dependencies=[],
    ),
    # System Supervisor
    ServiceDefinition(
        name="system_supervisor",
        service_class="trading_bot.services.tier5_services.SystemSupervisorService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.CRITICAL,
        dependencies=["orchestrator"],
    ),
    # Systems AI
    ServiceDefinition(
        name="systems_ai",
        service_class="trading_bot.services.tier5_services.SystemsAIService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["ai_core"],
    ),
    # TAMIC
    ServiceDefinition(
        name="tamic",
        service_class="trading_bot.services.tier5_services.TAMICService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["analysis"],
    ),
    # Telemetry (already in tier3, skip)
    # Testing
    ServiceDefinition(
        name="testing",
        service_class="trading_bot.services.tier5_services.TestingService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.LOW,
        dependencies=[],
    ),
    # Tools
    ServiceDefinition(
        name="tools",
        service_class="trading_bot.services.tier5_services.ToolsService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.NORMAL,
        dependencies=[],
    ),
    # Trade Journal
    ServiceDefinition(
        name="trade_journal",
        service_class="trading_bot.services.tier5_services.TradeJournalService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.NORMAL,
        dependencies=["audit"],
    ),
    # Trading
    ServiceDefinition(
        name="trading",
        service_class="trading_bot.services.tier5_services.TradingService",
        layer=ServiceLayer.EXECUTION,
        priority=ServicePriority.CRITICAL,
        dependencies=["execution"],
    ),
    # Trading Calendar
    ServiceDefinition(
        name="trading_calendar",
        service_class="trading_bot.services.tier5_services.TradingCalendarService",
        layer=ServiceLayer.DATA_FOUNDATION,
        priority=ServicePriority.NORMAL,
        dependencies=["data"],
    ),
    # Ultimate Approval
    ServiceDefinition(
        name="ultimate_approval",
        service_class="trading_bot.services.tier5_services.UltimateApprovalService",
        layer=ServiceLayer.GOVERNANCE,
        priority=ServicePriority.HIGH,
        dependencies=["approval"],
    ),
    # Ultimate Architecture
    ServiceDefinition(
        name="ultimate_architecture",
        service_class="trading_bot.services.tier5_services.UltimateArchitectureService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.NORMAL,
        dependencies=[],
    ),
    # Ultimate Bot
    ServiceDefinition(
        name="ultimate_bot",
        service_class="trading_bot.services.tier5_services.UltimateBotService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.NORMAL,
        dependencies=["orchestrator"],
    ),
    # Ultimate Production
    ServiceDefinition(
        name="ultimate_production",
        service_class="trading_bot.services.tier5_services.UltimateProductionService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.NORMAL,
        dependencies=["production"],
    ),
    # Ultimate System
    ServiceDefinition(
        name="ultimate_system",
        service_class="trading_bot.services.tier5_services.UltimateSystemService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.NORMAL,
        dependencies=["system"],
    ),
    # Unified Approval
    ServiceDefinition(
        name="unified_approval",
        service_class="trading_bot.services.tier5_services.UnifiedApprovalService",
        layer=ServiceLayer.GOVERNANCE,
        priority=ServicePriority.HIGH,
        dependencies=["ultimate_approval"],
    ),
    # Unified Architecture
    ServiceDefinition(
        name="unified_architecture",
        service_class="trading_bot.services.tier5_services.UnifiedArchitectureService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.NORMAL,
        dependencies=["ultimate_architecture"],
    ),
    # Unified System
    ServiceDefinition(
        name="unified_system",
        service_class="trading_bot.services.tier5_services.UnifiedSystemService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.NORMAL,
        dependencies=["ultimate_system"],
    ),
    # Upgrades
    ServiceDefinition(
        name="upgrades",
        service_class="trading_bot.services.tier5_services.UpgradesService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=["autonomous"],
    ),
    # Utils
    ServiceDefinition(
        name="utils",
        service_class="trading_bot.services.tier5_services.UtilsService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.HIGH,
        dependencies=[],
    ),
    # Validation
    ServiceDefinition(
        name="validation",
        service_class="trading_bot.services.tier5_services.ValidationService",
        layer=ServiceLayer.GOVERNANCE,
        priority=ServicePriority.HIGH,
        dependencies=[],
    ),
    # Verification
    ServiceDefinition(
        name="verification",
        service_class="trading_bot.services.tier5_services.VerificationService",
        layer=ServiceLayer.GOVERNANCE,
        priority=ServicePriority.HIGH,
        dependencies=["validation"],
    ),
    # Visualization
    ServiceDefinition(
        name="visualization",
        service_class="trading_bot.services.tier5_services.VisualizationService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.LOW,
        dependencies=["dashboard"],
    ),
    # Voice Assistant
    ServiceDefinition(
        name="voice_assistant",
        service_class="trading_bot.services.tier5_services.VoiceAssistantService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.LOW,
        dependencies=[],
    ),
    # Wealth
    ServiceDefinition(
        name="wealth",
        service_class="trading_bot.services.tier5_services.WealthService",
        layer=ServiceLayer.EXECUTION,
        priority=ServicePriority.NORMAL,
        dependencies=["portfolio"],
    ),
    # World Model
    ServiceDefinition(
        name="world_model",
        service_class="trading_bot.services.tier5_services.WorldModelService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.NORMAL,
        dependencies=["ml"],
    ),
    # Production
    ServiceDefinition(
        name="production",
        service_class="trading_bot.services.tier5_services.ProductionService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.HIGH,
        dependencies=[],
    ),
    # TIER 6 - Additional Modules
    ServiceDefinition(
        name="adversarial_curriculum",
        service_class="trading_bot.services.tier5_services.AdversarialCurriculumService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=[],
    ),
    ServiceDefinition(
        name="adversarial_decision",
        service_class="trading_bot.services.tier5_services.AdversarialDecisionService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=[],
    ),
    ServiceDefinition(
        name="agents",
        service_class="trading_bot.services.tier5_services.AgentsService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=[],
    ),
    ServiceDefinition(
        name="agents2",
        service_class="trading_bot.services.tier5_services.Agents2Service",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=[],
    ),
    ServiceDefinition(
        name="ai_engineer",
        service_class="trading_bot.services.tier5_services.AIEngineerService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=[],
    ),
    ServiceDefinition(
        name="alerts",
        service_class="trading_bot.services.tier5_services.AlertsService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.NORMAL,
        dependencies=[],
    ),
    ServiceDefinition(
        name="api",
        service_class="trading_bot.services.tier5_services.APIService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.HIGH,
        dependencies=[],
    ),
    ServiceDefinition(
        name="arbitrage",
        service_class="trading_bot.services.tier5_services.ArbitrageService",
        layer=ServiceLayer.EXECUTION,
        priority=ServicePriority.NORMAL,
        dependencies=[],
    ),
    ServiceDefinition(
        name="auto_optimizer",
        service_class="trading_bot.services.tier5_services.AutoOptimizerService",
        layer=ServiceLayer.INTELLIGENCE,
        priority=ServicePriority.LOW,
        dependencies=[],
    ),
    ServiceDefinition(
        name="automation",
        service_class="trading_bot.services.tier5_services.AutomationService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.NORMAL,
        dependencies=[],
    ),
    ServiceDefinition(
        name="blockchain",
        service_class="trading_bot.services.tier5_services.BlockchainService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.LOW,
        dependencies=[],
    ),
    ServiceDefinition(
        name="bridges",
        service_class="trading_bot.services.tier5_services.BridgesService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.NORMAL,
        dependencies=[],
    ),
    ServiceDefinition(
        name="cloud_deployer",
        service_class="trading_bot.services.tier5_services.CloudDeployerService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.LOW,
        dependencies=[],
    ),
    ServiceDefinition(
        name="connectors",
        service_class="trading_bot.services.tier5_services.ConnectorsService",
        layer=ServiceLayer.DATA_FOUNDATION,
        priority=ServicePriority.HIGH,
        dependencies=[],
    ),
    ServiceDefinition(
        name="core_api",
        service_class="trading_bot.services.tier5_services.CoreAPIService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.HIGH,
        dependencies=[],
    ),
    ServiceDefinition(
        name="critical_fixes",
        service_class="trading_bot.services.tier5_services.CriticalFixesService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.HIGH,
        dependencies=[],
    ),
    ServiceDefinition(
        name="crypto",
        service_class="trading_bot.services.tier5_services.CryptoService",
        layer=ServiceLayer.EXECUTION,
        priority=ServicePriority.NORMAL,
        dependencies=[],
    ),
    ServiceDefinition(
        name="ctrader",
        service_class="trading_bot.services.tier5_services.CTraderService",
        layer=ServiceLayer.EXECUTION,
        priority=ServicePriority.NORMAL,
        dependencies=[],
    ),
    ServiceDefinition(
        name="deployment",
        service_class="trading_bot.services.tier5_services.DeploymentService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.LOW,
        dependencies=[],
    ),
    ServiceDefinition(
        name="derivatives",
        service_class="trading_bot.services.tier5_services.DerivativesService",
        layer=ServiceLayer.EXECUTION,
        priority=ServicePriority.NORMAL,
        dependencies=[],
    ),
    ServiceDefinition(
        name="diagnostics_wrapper",
        service_class="trading_bot.services.tier5_services.DiagnosticsServiceWrapper",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.HIGH,
        dependencies=[],
    ),
    ServiceDefinition(
        name="distributed",
        service_class="trading_bot.services.tier5_services.DistributedService",
        layer=ServiceLayer.INFRASTRUCTURE,
        priority=ServicePriority.LOW,
        dependencies=[],
    ),
    ServiceDefinition(
        name="documentation",
        service_class="trading_bot.services.tier5_services.DocumentationService",
        layer=ServiceLayer.ORCHESTRATION,
        priority=ServicePriority.LOW,
        dependencies=[],
    ),
    ServiceDefinition(
        name="exits",
        service_class="trading_bot.services.tier5_services.ExitsService",
        layer=ServiceLayer.EXECUTION,
        priority=ServicePriority.HIGH,
        dependencies=[],
    ),
    ServiceDefinition(
        name="hedging",
        service_class="trading_bot.services.tier5_services.HedgingService",
        layer=ServiceLayer.RISK_SAFETY,
        priority=ServicePriority.HIGH,
        dependencies=[],
    ),
]


class ServiceFactory:
    """
    Factory for creating and registering services.
    
    Handles:
    - Service instantiation with proper configuration
    - Dependency resolution
    - Layer-based startup ordering
    - Graceful degradation for non-critical services
    """
    
    def __init__(
        self,
        registry: ServiceRegistry,
        event_bus: EventBus,
        config: Optional[Dict[str, Any]] = None
    ):
        self.registry = registry
        self.event_bus = event_bus
        self.config = config or {}
        self._created_services: Dict[str, BaseService] = {}
        self._failed_services: Dict[str, str] = {}
        
        # Link registry to event bus
        self.registry.set_event_bus(event_bus)
        
        logger.info("ServiceFactory initialized")
    
    def _import_service_class(self, class_path: str) -> Optional[Type[BaseService]]:
        """Dynamically import a service class"""
        try:
            module_path, class_name = class_path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            logger.warning(f"Failed to import {class_path}: {e}")
            return None
    
    def _create_service(
        self,
        definition: ServiceDefinition
    ) -> Optional[BaseService]:
        """Create a single service instance"""
        # Get service config
        service_config = self.config.get('services', {}).get(
            definition.name, {}
        )
        service_config.update(definition.config)
        
        # Check if disabled
        if not definition.enabled or not service_config.get('enabled', True):
            logger.info(f"Service {definition.name} is disabled")
            return None
        
        # Import service class
        service_class = self._import_service_class(definition.service_class)
        if not service_class:
            if definition.critical:
                raise RuntimeError(
                    f"Critical service {definition.name} could not be loaded"
                )
            self._failed_services[definition.name] = "Import failed"
            return None
        
        # Create instance
        try:
            service = service_class(config=service_config)
            self._created_services[definition.name] = service
            return service
        except Exception as e:
            logger.error(f"Failed to create {definition.name}: {e}")
            if definition.critical:
                raise RuntimeError(
                    f"Critical service {definition.name} failed: {e}"
                )
            self._failed_services[definition.name] = str(e)
            return None
    
    def create_tier1_services(self) -> Dict[str, BaseService]:
        """Create all TIER 1 (core) services"""
        logger.info("Creating TIER 1 services...")
        
        # Sort by layer
        sorted_definitions = sorted(
            TIER1_SERVICES,
            key=lambda d: d.layer.value
        )
        
        for definition in sorted_definitions:
            service = self._create_service(definition)
            if service:
                self.registry.register(service, definition.dependencies)
                logger.info(
                    f"✓ Created {definition.name} "
                    f"(Layer {definition.layer.value}: {definition.layer.name})"
                )
        
        logger.info(
            f"TIER 1 complete: {len(self._created_services)} services created, "
            f"{len(self._failed_services)} failed"
        )
        return self._created_services.copy()
    
    def create_tier2_services(self) -> Dict[str, BaseService]:
        """Create all TIER 2 (enhanced) services"""
        logger.info("Creating TIER 2 services...")
        
        tier2_created = {}
        
        # Sort by layer
        sorted_definitions = sorted(
            TIER2_SERVICES,
            key=lambda d: d.layer.value
        )
        
        for definition in sorted_definitions:
            # Check dependencies are available
            deps_available = all(
                dep in self._created_services
                for dep in definition.dependencies
            )
            
            if not deps_available:
                missing = [
                    d for d in definition.dependencies
                    if d not in self._created_services
                ]
                logger.warning(
                    f"Skipping {definition.name}: missing dependencies {missing}"
                )
                continue
            
            service = self._create_service(definition)
            if service:
                self.registry.register(service, definition.dependencies)
                tier2_created[definition.name] = service
                logger.info(
                    f"✓ Created {definition.name} "
                    f"(Layer {definition.layer.value}: {definition.layer.name})"
                )
        
        logger.info(
            f"TIER 2 complete: {len(tier2_created)} services created"
        )
        return tier2_created
    
    def create_tier3_services(self) -> Dict[str, BaseService]:
        """Create all TIER 3 (additional) services"""
        logger.info("Creating TIER 3 services...")
        
        tier3_created = {}
        
        # Sort by layer
        sorted_definitions = sorted(
            TIER3_SERVICES,
            key=lambda d: d.layer.value
        )
        
        for definition in sorted_definitions:
            # Check dependencies are available
            deps_available = all(
                dep in self._created_services
                for dep in definition.dependencies
            )
            
            if not deps_available:
                missing = [
                    d for d in definition.dependencies
                    if d not in self._created_services
                ]
                logger.warning(
                    f"Skipping {definition.name}: missing dependencies {missing}"
                )
                continue
            
            service = self._create_service(definition)
            if service:
                self.registry.register(service, definition.dependencies)
                tier3_created[definition.name] = service
                logger.info(
                    f"+ Created {definition.name} "
                    f"(Layer {definition.layer.value}: {definition.layer.name})"
                )
        
        logger.info(
            f"TIER 3 complete: {len(tier3_created)} services created"
        )
        return tier3_created
    
    def create_tier4_services(self) -> Dict[str, BaseService]:
        """Create all TIER 4 (complete system) services"""
        logger.info("Creating TIER 4 services (Complete System)...")
        
        tier4_created = {}
        
        # Sort by layer
        sorted_definitions = sorted(
            TIER4_SERVICES,
            key=lambda d: d.layer.value
        )
        
        for definition in sorted_definitions:
            # Check dependencies are available
            deps_available = all(
                dep in self._created_services
                for dep in definition.dependencies
            )
            
            if not deps_available:
                missing = [
                    d for d in definition.dependencies
                    if d not in self._created_services
                ]
                logger.warning(
                    f"Skipping {definition.name}: missing dependencies {missing}"
                )
                continue
            
            service = self._create_service(definition)
            if service:
                self.registry.register(service, definition.dependencies)
                tier4_created[definition.name] = service
                logger.info(
                    f"* Created {definition.name} "
                    f"(Layer {definition.layer.value}: {definition.layer.name})"
                )
        
        logger.info(
            f"TIER 4 complete: {len(tier4_created)} services created"
        )
        return tier4_created
    
    def create_tier5_services(self) -> Dict[str, BaseService]:
        """Create all TIER 5 (complete ecosystem) services"""
        logger.info("Creating TIER 5 services (Complete Ecosystem)...")
        
        tier5_created = {}
        
        # Sort by layer
        sorted_definitions = sorted(
            TIER5_SERVICES,
            key=lambda d: d.layer.value
        )
        
        for definition in sorted_definitions:
            # Check dependencies are available
            deps_available = all(
                dep in self._created_services
                for dep in definition.dependencies
            )
            
            if not deps_available:
                missing = [
                    d for d in definition.dependencies
                    if d not in self._created_services
                ]
                logger.warning(
                    f"Skipping {definition.name}: missing dependencies {missing}"
                )
                continue
            
            service = self._create_service(definition)
            if service:
                self.registry.register(service, definition.dependencies)
                tier5_created[definition.name] = service
                logger.info(
                    f"# Created {definition.name} "
                    f"(Layer {definition.layer.value}: {definition.layer.name})"
                )
        
        logger.info(
            f"TIER 5 complete: {len(tier5_created)} services created"
        )
        return tier5_created
    
    def create_all_services(
        self,
        include_tier2: bool = True,
        include_tier3: bool = False,
        include_tier4: bool = False,
        include_tier5: bool = False
    ) -> Dict[str, BaseService]:
        """Create all services (TIER 1 + optionally TIER 2/3/4/5)"""
        services = self.create_tier1_services()
        
        if include_tier2:
            tier2 = self.create_tier2_services()
            services.update(tier2)
        
        if include_tier3:
            tier3 = self.create_tier3_services()
            services.update(tier3)
        
        if include_tier4:
            tier4 = self.create_tier4_services()
            services.update(tier4)
        
        if include_tier5:
            tier5 = self.create_tier5_services()
            services.update(tier5)
        
        return services
    
    def get_creation_report(self) -> Dict[str, Any]:
        """Get report of service creation results"""
        return {
            'created': list(self._created_services.keys()),
            'failed': self._failed_services.copy(),
            'total_created': len(self._created_services),
            'total_failed': len(self._failed_services),
        }


def create_service_factory(
    registry: ServiceRegistry,
    event_bus: EventBus,
    config: Optional[Dict[str, Any]] = None
) -> ServiceFactory:
    """Factory function to create ServiceFactory"""
    return ServiceFactory(registry, event_bus, config)
