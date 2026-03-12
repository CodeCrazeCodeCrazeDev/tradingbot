"""
ai_ml_enhancements package
"""

try:
    from .active_learning import ActiveLearningResult, ActiveLearningSampler, Sample
    from .causal_discovery import (
        CausalDiscoveryEngine,
        CausalEdge,
        CausalGraph,
        CausalResult
    )
    from .concept_drift import (
        ConceptDriftDetector,
        ConceptDriftResult,
        DriftDetection,
        DriftSeverity,
        DriftType
    )
    from .contrastive_learning import ContrastiveLearningEmbeddings, ContrastiveResult, MarketEmbedding
    from .counterfactual_analyzer import Counterfactual, CounterfactualAnalyzer, CounterfactualResult
    from .diffusion_model import DiffusionModelGenerator, DiffusionResult, GeneratedScenario
    from .ensemble_stacker import EnsembleResult, ModelEnsembleStacker, ModelPrediction
    from .federated_learning import (
        FederatedLearningClient,
        FederatedResult,
        FederatedServer,
        LocalUpdate
    )
    from .graph_neural_network import (
        EdgeType,
        GNNAnalysisResult,
        GraphEdge,
        GraphNeuralNetwork,
        GraphNode,
        GraphPrediction
    )
    from .inverse_rl import (
        ExpertTrajectory,
        InverseRLPolicyExtractor,
        InverseRLResult,
        LearnedReward
    )
    from .neural_architecture_search import Architecture, NASResult, NeuralArchitectureSearch
    from .rl_gym import (
        Action,
        Experience,
        RLResult,
        ReinforcementLearningGym,
        State
    )
    from .temporal_fusion import (
        QuantilePrediction,
        TFTResult,
        TemporalAttention,
        TemporalFusionTransformer
    )
    from .transformer_predictor import (
        AttentionWeights,
        PredictionHorizon,
        PredictionType,
        PricePrediction,
        TransformerPredictionResult,
        TransformerPricePredictor
    )
    from .uncertainty_quantification import UncertaintyEstimate, UncertaintyQuantifier, UncertaintyResult
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in ai_ml_enhancements: {e}')

__all__ = [
    'Action',
    'ActiveLearningResult',
    'ActiveLearningSampler',
    'Architecture',
    'AttentionWeights',
    'CausalDiscoveryEngine',
    'CausalEdge',
    'CausalGraph',
    'CausalResult',
    'ConceptDriftDetector',
    'ConceptDriftResult',
    'ContrastiveLearningEmbeddings',
    'ContrastiveResult',
    'Counterfactual',
    'CounterfactualAnalyzer',
    'CounterfactualResult',
    'DiffusionModelGenerator',
    'DiffusionResult',
    'DriftDetection',
    'DriftSeverity',
    'DriftType',
    'EdgeType',
    'EnsembleResult',
    'Experience',
    'ExpertTrajectory',
    'FederatedLearningClient',
    'FederatedResult',
    'FederatedServer',
    'GNNAnalysisResult',
    'GeneratedScenario',
    'GraphEdge',
    'GraphNeuralNetwork',
    'GraphNode',
    'GraphPrediction',
    'InverseRLPolicyExtractor',
    'InverseRLResult',
    'LearnedReward',
    'LocalUpdate',
    'MarketEmbedding',
    'ModelEnsembleStacker',
    'ModelPrediction',
    'NASResult',
    'NeuralArchitectureSearch',
    'PredictionHorizon',
    'PredictionType',
    'PricePrediction',
    'QuantilePrediction',
    'RLResult',
    'ReinforcementLearningGym',
    'Sample',
    'State',
    'TFTResult',
    'TemporalAttention',
    'TemporalFusionTransformer',
    'TransformerPredictionResult',
    'TransformerPricePredictor',
    'UncertaintyEstimate',
    'UncertaintyQuantifier',
    'UncertaintyResult',
]