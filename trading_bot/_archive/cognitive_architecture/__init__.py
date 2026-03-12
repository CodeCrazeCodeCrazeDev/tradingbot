"""
cognitive_architecture package
"""

try:
    from .cognitive_core import AlphaAlgoCognitiveCore, CognitiveState, TradingDecision
    from .layer10_evolution import (
        ArchitectureRebalancer,
        ContinuousEvolutionEngine,
        EvolutionCycle,
        Strategy,
        StrategyEvolver
    )
    from .layer1_market_state_detection import (
        MarketRegime,
        MarketStateEngine,
        RegimeClassifier,
        RegimeSignal,
        TransitionDetector,
        TrendRegimeAnalyzer,
        VolatilityScanner
    )
    from .layer2_adaptive_integration import AdaptiveIntegrationCore, IntegrationMode, MetaAgent
    from .layer3_cognitive_economy import (
        AgentDecision,
        BaseAgent,
        CognitiveEconomy,
        DataAgent,
        LearningAgent,
        RiskAgent,
        StrategyAgent,
        SupervisorAgent
    )
    from .layer4_neuro_symbolic import (
        NeuralLayer,
        NeuroSymbolicSystem,
        Pattern,
        ReasoningEngine,
        ReasoningResult,
        Rule,
        SymbolicLayer
    )
    from .layer5_advanced_rl import (
        AdvancedRLHub,
        DistributionalRL,
        HierarchicalRL,
        MetaRL,
        RLAction,
        RLState
    )
    from .layer6_multimodal_fusion import (
        DataSource,
        DataType,
        DataTypeProcessor,
        FusedSignal,
        MultiModalFusion,
        TransformerFusion
    )
    from .layer7_self_healing import (
        AutoRepairEngine,
        DiagnosticResult,
        DiagnosticsMonitor,
        HealthStatus,
        OptimizationManager,
        OptimizationMode,
        PerformanceEvaluator,
        RepairAction,
        SafetyManager,
        SelfHealingSupervisor
    )
    from .layer8_quantum_simulation import (
        ForecastResult,
        MonteCarloSimulator,
        QuantumForecaster,
        QuantumSimulationLayer,
        SimulationResult,
        WorldModelSimulation
    )
    from .layer9_explainability import (
        ExplainabilityInterface,
        Explanation,
        NaturalLanguageGenerator,
        TrustMetrics,
        TrustScore
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in cognitive_architecture: {e}')

__all__ = [
    'AdaptiveIntegrationCore',
    'AdvancedRLHub',
    'AgentDecision',
    'AlphaAlgoCognitiveCore',
    'ArchitectureRebalancer',
    'AutoRepairEngine',
    'BaseAgent',
    'CognitiveEconomy',
    'CognitiveState',
    'ContinuousEvolutionEngine',
    'DataAgent',
    'DataSource',
    'DataType',
    'DataTypeProcessor',
    'DiagnosticResult',
    'DiagnosticsMonitor',
    'DistributionalRL',
    'EvolutionCycle',
    'ExplainabilityInterface',
    'Explanation',
    'ForecastResult',
    'FusedSignal',
    'HealthStatus',
    'HierarchicalRL',
    'IntegrationMode',
    'LearningAgent',
    'MarketRegime',
    'MarketStateEngine',
    'MetaAgent',
    'MetaRL',
    'MonteCarloSimulator',
    'MultiModalFusion',
    'NaturalLanguageGenerator',
    'NeuralLayer',
    'NeuroSymbolicSystem',
    'OptimizationManager',
    'OptimizationMode',
    'Pattern',
    'PerformanceEvaluator',
    'QuantumForecaster',
    'QuantumSimulationLayer',
    'RLAction',
    'RLState',
    'ReasoningEngine',
    'ReasoningResult',
    'RegimeClassifier',
    'RegimeSignal',
    'RepairAction',
    'RiskAgent',
    'Rule',
    'SafetyManager',
    'SelfHealingSupervisor',
    'SimulationResult',
    'Strategy',
    'StrategyAgent',
    'StrategyEvolver',
    'SupervisorAgent',
    'SymbolicLayer',
    'TradingDecision',
    'TransformerFusion',
    'TransitionDetector',
    'TrendRegimeAnalyzer',
    'TrustMetrics',
    'TrustScore',
    'VolatilityScanner',
    'WorldModelSimulation',
]