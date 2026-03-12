"""
Deepchart Module
============================================================

Auto-generated integration file.
"""

# confidence_overlay_engine
try:
    from .confidence_overlay_engine import (
        ConfidenceOverlayEngine,
        InformationFlowEngine,
        StrategyViewEngine,
    )
except ImportError as e:
    # confidence_overlay_engine not available
    pass

# execution_forecast_engine
try:
    from .execution_forecast_engine import (
        PriceResponseCurveEngine,
    )
except ImportError as e:
    # execution_forecast_engine not available
    pass

# feature_pipeline
try:
    from .feature_pipeline import (
        DeepChartFeatureEngine,
    )
except ImportError as e:
    # feature_pipeline not available
    pass

# friction_engine
try:
    from .friction_engine import (
        MicroFrictionEngine,
    )
except ImportError as e:
    # friction_engine not available
    pass

# inference_engine
try:
    from .inference_engine import (
        InferenceEngine,
    )
except ImportError as e:
    # inference_engine not available
    pass

# intent_inference_engine
try:
    from .intent_inference_engine import (
        IntentInferenceEngine,
    )
except ImportError as e:
    # intent_inference_engine not available
    pass

# intent_orchestrator
try:
    from .intent_orchestrator import (
        IntentOrchestrator,
    )
except ImportError as e:
    # intent_orchestrator not available
    pass

# latent_state_engine
try:
    from .latent_state_engine import (
        LatentStateEngine,
    )
except ImportError as e:
    # latent_state_engine not available
    pass

# liquidity_entropy_engine
try:
    from .liquidity_entropy_engine import (
        SyntheticLiquidityEngine,
    )
except ImportError as e:
    # liquidity_entropy_engine not available
    pass

# market_intelligence_orchestrator
try:
    from .market_intelligence_orchestrator import (
        MarketIntelligenceOrchestrator,
    )
except ImportError as e:
    # market_intelligence_orchestrator not available
    pass

# memory_sr_engine
try:
    from .memory_sr_engine import (
        LearnedSREngine,
        MarketMemoryEngine,
        MicroTrendVectorEngine,
    )
except ImportError as e:
    # memory_sr_engine not available
    pass

# orchestrator
try:
    from .orchestrator import (
        DeepChartOrchestrator,
        OrchestratorConfig,
    )
except ImportError as e:
    # orchestrator not available
    pass

__all__ = [
    'ConfidenceOverlayEngine',
    'DeepChartFeatureEngine',
    'DeepChartOrchestrator',
    'InferenceEngine',
    'InformationFlowEngine',
    'IntentInferenceEngine',
    'IntentOrchestrator',
    'LatentStateEngine',
    'LearnedSREngine',
    'MarketIntelligenceOrchestrator',
    'MarketMemoryEngine',
    'MicroFrictionEngine',
    'MicroTrendVectorEngine',
    'OrchestratorConfig',
    'PriceResponseCurveEngine',
    'StrategyViewEngine',
    'SyntheticLiquidityEngine',
]
