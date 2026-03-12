"""
AlphaAlgo Core AI Architecture

Advanced multi-agent system with:
- AgentFlow orchestration (planner-verifier-executor)
- Advanced RL (CQL, BCQ, BEAR, MBOP, MAGIC)
- Forecasting (TFT, Informer, N-BEATS, DeepAR)
- Execution optimization (Almgren-Chriss, RL-based)
- Explainability (SHAP, LIME, DoWhy)
- Meta-learning (MAML, EWC)
- Drift detection (ADWIN, Page-Hinkley)
- MLOps (MLflow, monitoring, versioning)
"""

# Import agents (using try-except for graceful degradation)
try:
    from .agents import (
        PlannerAgent,
        VerifierAgent,
        ExecutorAgent,
        SafetyValidatorAgent,
        AgentOrchestrator
    )
except ImportError:
    pass
try:
    # Agents module incomplete - use placeholders
    PlannerAgent = None
    VerifierAgent = None
    ExecutorAgent = None
    SafetyValidatorAgent = None
    AgentOrchestrator = None

# Import RL agents
    from .rl import (
        CQLAgent,
        BCQAgent,
        BEARAgent,
        MBOPAgent,
        MAGICAgent,
        HierarchicalRLAgent,
        OfflinePolicyEvaluator
    )
except ImportError:
    CQLAgent = None
    BCQAgent = None
    BEARAgent = None
    MBOPAgent = None
    MAGICAgent = None
    HierarchicalRLAgent = None
    OfflinePolicyEvaluator = None
# Import forecasting models
    from .forecasting import (
        TemporalFusionTransformer,
        InformerModel,
        NBEATSModel,
        DeepARModel,
        ForecastEnsemble
    )
except ImportError:
    TemporalFusionTransformer = None
    InformerModel = None
    NBEATSModel = None
    DeepARModel = None
    ForecastEnsemble = None
# Import execution optimization
    from .execution import (
        AlmgrenChrissExecutor,
        RLAdaptiveExecutor,
        MarketImpactModel,
        ExecutionOptimizer
    )
except ImportError:
    AlmgrenChrissExecutor = None
    RLAdaptiveExecutor = None
    MarketImpactModel = None
    ExecutionOptimizer = None
# Import explainability
    from .explainability import (
        SHAPExplainer,
        LIMEExplainer,
        CausalAnalyzer,
        AttentionVisualizer,
        TradeAttributor
    )
except ImportError:
    SHAPExplainer = None
    LIMEExplainer = None
    CausalAnalyzer = None
    AttentionVisualizer = None
    TradeAttributor = None
# Import meta-learning
    from .meta_learning import (
        MAMLTrainer,
        ContinualLearner,
        RegimeDetector,
        AdaptiveRetrainer
    )
except ImportError:
    MAMLTrainer = None
    ContinualLearner = None
    RegimeDetector = None
    AdaptiveRetrainer = None
# Import drift detection
    from .drift_detection import (
        ADWINDetector,
        PageHinkleyDetector,
        ConceptDriftMonitor
    )
except ImportError:
    ADWINDetector = None
    PageHinkleyDetector = None
    ConceptDriftMonitor = None
# Import MLOps (now implemented)
    from .mlops import (
        ModelRegistry,
        ExperimentTracker,
        PerformanceMonitor,
        AutoRollback
    )
except ImportError:
    ModelRegistry = None
    ExperimentTracker = None
    PerformanceMonitor = None
    AutoRollback = None

__all__ = [
    # Agents
    'PlannerAgent',
    'VerifierAgent',
    'ExecutorAgent',
    'SafetyValidatorAgent',
    'AgentOrchestrator',
    
    # RL
    'CQLAgent',
    'BCQAgent',
    'BEARAgent',
    'MBOPAgent',
    'MAGICAgent',
    'HierarchicalRLAgent',
    'OfflinePolicyEvaluator',
    
    # Forecasting
    'TemporalFusionTransformer',
    'InformerModel',
    'NBEATSModel',
    'DeepARModel',
    'ForecastEnsemble',
    
    # Execution
    'AlmgrenChrissExecutor',
    'RLAdaptiveExecutor',
    'MarketImpactModel',
    'ExecutionOptimizer',
    
    # Explainability
    'SHAPExplainer',
    'LIMEExplainer',
    'CausalAnalyzer',
    'AttentionVisualizer',
    'TradeAttributor',
    
    # Meta-Learning
    'MAMLTrainer',
    'ContinualLearner',
    'RegimeDetector',
    'AdaptiveRetrainer',
    
    # Drift Detection
    'ADWINDetector',
    'PageHinkleyDetector',
    'ConceptDriftMonitor',
    
    # MLOps
    'ModelRegistry',
    'ExperimentTracker',
    'PerformanceMonitor',
    'AutoRollback',
]
