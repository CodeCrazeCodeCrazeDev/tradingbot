"""
Trading Bot Skills Module
========================

100 Advanced Trading Skills organized by category:

MARKET ANALYSIS (1-15):
- Fractal analysis, Hurst exponent, Elliott waves
- Harmonic patterns, Market profile, Delta divergence
- Auction market theory, Footprint charts, Cumulative delta
- Large trader detection, Iceberg detection, Spoofing detection

AI/ML ENHANCEMENTS (16-30):
- Transformer models, GNN, Temporal fusion
- Diffusion models, Contrastive learning, NAS
- Uncertainty quantification, Causal discovery
- Concept drift detection, Ensemble stacking

EXECUTION OPTIMIZATION (31-45):
- Optimal execution, Adaptive algos
- Queue position estimation, Fill probability
- Venue selection, Maker/taker decisions

RISK MANAGEMENT (46-60):
- Extreme value theory, Copula models
- Dynamic hedging, Greeks calculation
- Liquidity-adjusted VaR, Stress testing

STRATEGY GENERATION (61-75):
- Genetic evolution, Strategy cloning
- Alpha decay forecasting, Crowding detection
- Walk-forward optimization

ALTERNATIVE DATA (76-85):
- Earnings call NLP, SEC filings
- Options flow, Dark pool analysis
- Crypto on-chain analytics

INFRASTRUCTURE (86-92):
- Hot-cold swapping, Distributed state
- Chaos engineering, Canary deployment

USER EXPERIENCE (93-100):
- Voice commands, Natural language queries
- Mobile notifications, Trade journaling
"""

# Market Analysis Skills (1-15)
from trading_bot.skills.market_analysis import (
    FractalAnalyzer,
    HurstExponentCalculator,
    ElliottWaveDetector,
    HarmonicPatternScanner,
    MarketProfileAnalyzer,
    DeltaDivergenceDetector,
    AuctionMarketTheoryEngine,
    FootprintChartAnalyzer,
    CumulativeDeltaTracker,
    SpeedOfTapeAnalyzer,
    LargeTraderDetector,
    IcebergOrderDetector,
    SpoofingPatternDetector,
    StopHuntPredictor,
    SweepDetectionSystem,
)

# AI/ML Enhancement Skills (16-30)
from trading_bot.skills.ai_ml_enhancements import (
    TransformerPricePredictor,
    GraphNeuralNetwork,
    TemporalFusionTransformer,
    DiffusionModelGenerator,
    ContrastiveLearningEmbeddings,
    NeuralArchitectureSearch,
    FederatedLearningClient,
    ActiveLearningSampler,
    UncertaintyQuantifier,
    CausalDiscoveryEngine,
    CounterfactualAnalyzer,
    ConceptDriftDetector,
    ModelEnsembleStacker,
    ReinforcementLearningGym,
    InverseRLPolicyExtractor,
)

# Execution Optimization Skills (31-45)
from trading_bot.skills.execution_optimization import (
    OptimalExecutionScheduler,
    AdaptiveTWAPVWAP,
    ImplementationShortfallMinimizer,
    ParticipationRateController,
    SpreadCaptureStrategy,
    QueuePositionEstimator,
    FillProbabilityPredictor,
    LatencyArbitrageDefense,
    SmartOrderFragmenter,
    VenueSelectionOptimizer,
    MakerTakerDecisionEngine,
    OrderAnticipationDetector,
    ExecutionQualityScorer,
    SlippagePredictor,
    UrgencyClassifier,
)

# Risk Management Skills (46-60)
from trading_bot.skills.risk_management import (
    ExtremeValueTheory,
    CopulaBasedDependency,
    DynamicHedgingEngine,
    GreeksCalculator,
    ScenarioGenerator,
    LiquidityAdjustedVaR,
    IncrementalVaRCalculator,
    ComponentVaRDecomposer,
    ExpectedShortfall,
    DrawdownDurationTracker,
    RecoveryTimeEstimator,
    CorrelationRegimeDetector,
    ContagionRiskMonitor,
    MarginCallPredictor,
    PortfolioStressTester,
)

# Strategy Generation Skills (61-75)
from trading_bot.skills.strategy_generation import (
    GeneticStrategyEvolver,
    StrategyCloner,
    CrossAssetStrategyAdapter,
    RegimeSpecificStrategySelector,
    StrategyDecayDetector,
    AlphaDecayForecaster,
    StrategyCapacityEstimator,
    CrowdingDetector,
    StrategyCorrelationMatrix,
    DynamicStrategyWeighting,
    StrategyTournamentSystem,
    PaperTradingValidator,
    WalkForwardOptimizer,
    CombinatorialPurgedCV,
    StrategyFingerprinting,
)

# Alternative Data Skills (76-85)
from trading_bot.skills.alternative_data import (
    EarningsCallNLPAnalyzer,
    SECFilingParser,
    PatentFilingTracker,
    SupplyChainMapper,
    ESGScoreIntegrator,
    InsiderTradingTracker,
    OptionsFlowAnalyzer,
    DarkPoolPrintAnalyzer,
    CryptoOnChainAnalyzer,
    SocialSentimentVelocity,
)

# Infrastructure Skills (86-92)
from trading_bot.skills.infrastructure import (
    HotColdStrategySwapper,
    DistributedStateManager,
    TimeTravelDebugger,
    ChaosEngineeringModule,
    CanaryDeploymentSystem,
    FeatureFlagManager,
    ABTestingFramework,
)

# User Experience Skills (93-100)
from trading_bot.skills.user_experience import (
    NaturalLanguageInterface,
    VoiceAssistant,
    IntelligentAlertSystem,
    AutomatedReportGenerator,
    DashboardBuilder,
    TradeJournalAnalyzer,
    NotificationRouter,
    ExplainabilityEngine,
)

__all__ = [
    # Market Analysis
    'FractalAnalyzer',
    'HurstExponentCalculator',
    'ElliottWaveDetector',
    'HarmonicPatternScanner',
    'MarketProfileAnalyzer',
    'DeltaDivergenceDetector',
    'AuctionMarketTheoryEngine',
    'FootprintChartAnalyzer',
    'CumulativeDeltaTracker',
    'SpeedOfTapeAnalyzer',
    'LargeTraderDetector',
    'IcebergOrderDetector',
    'SpoofingPatternDetector',
    'StopHuntPredictor',
    'SweepDetectionSystem',
    # AI/ML
    'TransformerPricePredictor',
    'GraphNeuralNetwork',
    'TemporalFusionTransformer',
    'DiffusionModelGenerator',
    'ContrastiveLearningEmbeddings',
    'NeuralArchitectureSearch',
    'FederatedLearningClient',
    'ActiveLearningSampler',
    'UncertaintyQuantifier',
    'CausalDiscoveryEngine',
    'CounterfactualAnalyzer',
    'ConceptDriftDetector',
    'ModelEnsembleStacker',
    'ReinforcementLearningGym',
    'InverseRLPolicyExtractor',
    # Execution
    'OptimalExecutionScheduler',
    'AdaptiveTWAPVWAP',
    'ImplementationShortfallMinimizer',
    'ParticipationRateController',
    'SpreadCaptureStrategy',
    'QueuePositionEstimator',
    'FillProbabilityPredictor',
    'LatencyArbitrageDefense',
    'SmartOrderFragmenter',
    'VenueSelectionOptimizer',
    'MakerTakerDecisionEngine',
    'OrderAnticipationDetector',
    'ExecutionQualityScorer',
    'SlippagePredictor',
    'UrgencyClassifier',
    # Risk Management
    'ExtremeValueTheory',
    'CopulaBasedDependency',
    'DynamicHedgingEngine',
    'GreeksCalculator',
    'ScenarioGenerator',
    'LiquidityAdjustedVaR',
    'IncrementalVaRCalculator',
    'ComponentVaRDecomposer',
    'ExpectedShortfall',
    'DrawdownDurationTracker',
    'RecoveryTimeEstimator',
    'CorrelationRegimeDetector',
    'ContagionRiskMonitor',
    'MarginCallPredictor',
    'PortfolioStressTester',
    # Strategy Generation
    'GeneticStrategyEvolver',
    'StrategyCloner',
    'CrossAssetStrategyAdapter',
    'RegimeSpecificStrategySelector',
    'StrategyDecayDetector',
    'AlphaDecayForecaster',
    'StrategyCapacityEstimator',
    'CrowdingDetector',
    'StrategyCorrelationMatrix',
    'DynamicStrategyWeighting',
    'StrategyTournamentSystem',
    'PaperTradingValidator',
    'WalkForwardOptimizer',
    'CombinatorialPurgedCV',
    'StrategyFingerprinting',
    # Alternative Data
    'EarningsCallNLPAnalyzer',
    'SECFilingParser',
    'PatentFilingTracker',
    'SupplyChainMapper',
    'ESGScoreIntegrator',
    'InsiderTradingTracker',
    'OptionsFlowAnalyzer',
    'DarkPoolPrintAnalyzer',
    'CryptoOnChainAnalyzer',
    'SocialSentimentVelocity',
    # Infrastructure
    'HotColdStrategySwapper',
    'DistributedStateManager',
    'TimeTravelDebugger',
    'ChaosEngineeringModule',
    'CanaryDeploymentSystem',
    'FeatureFlagManager',
    'ABTestingFramework',
    # User Experience
    'NaturalLanguageInterface',
    'VoiceAssistant',
    'IntelligentAlertSystem',
    'AutomatedReportGenerator',
    'DashboardBuilder',
    'TradeJournalAnalyzer',
    'NotificationRouter',
    'ExplainabilityEngine',
]
