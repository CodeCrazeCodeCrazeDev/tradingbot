"""
indicators package
"""

try:
    from .advanced_liquidity import (
        AbsorptionExhaustionRatio,
        AdvancedLiquidityIndicators,
        CVDMultiTimeframe,
        IcebergDetector,
        IcebergOrder,
        OrderBookImbalance,
        TickImbalanceBar,
        VolumeDeltaHeatmap
    )
    from .advanced_ml import (
        AdaptiveEnsemble,
        AdvancedMLIndicators,
        CopulaModel,
        ExplainableAI,
        HiddenMarkovModel,
        MLSignal,
        MetaLearner,
        RegimeAwareRL,
        TransformerPredictor
    )
    from .advanced_statistical import (
        AdvancedStatisticalIndicators,
        CointegrationAnalyzer,
        HiddenMarkovRegime,
        KalmanFilterTrendline,
        ZScoreReversionModel
    )
    from .advanced_technical import (
        AdvancedTechnicalIndicators,
        FRAMA,
        HurstExponent,
        KAMA,
        KalmanFilter,
        SuperTrend,
        TTMSqueeze
    )
    from .fractal_momentum_divergence import (
        DivergenceType,
        FractalDivergence,
        FractalMomentumDivergence,
        MomentumCalculator,
        MomentumReading,
        SignalStrength,
        SingleTimeframeDivergenceDetector,
        SwingPointDetector,
        TimeframeDivergence,
        TimeframeRelation,
        create_fmd_indicator
    )
    from .sentiment import Sentiment, initialize_sentiment
    from .vectorized_indicators import (
        VectorizedIndicators,
        adx_fast,
        atr_fast,
        bollinger_bands_fast,
        calculate_all_indicators_parallel,
        ema_fast,
        macd_fast,
        rsi_fast,
        sma_fast,
        stochastic_fast
    )
    from .volatility_impulse_vector import (
        ATRCalculator,
        ExplosionSignal,
        ImpulseDirection,
        ImpulseStrength,
        MomentumCalculator,
        OrderBookImbalanceCalculator,
        VIIReading,
        VolatilityImpulseVector,
        VolumeSurgeDetector,
        create_vii_indicator
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in indicators: {e}')

__all__ = [
    'IndicatorOrchestrator',
    'IndicatorManager',
    'ATRCalculator',
    'AbsorptionExhaustionRatio',
    'AdaptiveEnsemble',
    'AdvancedLiquidityIndicators',
    'AdvancedMLIndicators',
    'AdvancedStatisticalIndicators',
    'AdvancedTechnicalIndicators',
    'CVDMultiTimeframe',
    'CointegrationAnalyzer',
    'CopulaModel',
    'DivergenceType',
    'ExplainableAI',
    'ExplosionSignal',
    'FRAMA',
    'FractalDivergence',
    'FractalMomentumDivergence',
    'HiddenMarkovModel',
    'HiddenMarkovRegime',
    'HurstExponent',
    'IcebergDetector',
    'IcebergOrder',
    'ImpulseDirection',
    'ImpulseStrength',
    'KAMA',
    'KalmanFilter',
    'KalmanFilterTrendline',
    'MLSignal',
    'MetaLearner',
    'MomentumCalculator',
    'MomentumReading',
    'OrderBookImbalance',
    'OrderBookImbalanceCalculator',
    'RegimeAwareRL',
    'Sentiment',
    'SignalStrength',
    'SingleTimeframeDivergenceDetector',
    'SuperTrend',
    'SwingPointDetector',
    'TTMSqueeze',
    'TickImbalanceBar',
    'TimeframeDivergence',
    'TimeframeRelation',
    'TransformerPredictor',
    'VIIReading',
    'VectorizedIndicators',
    'VolatilityImpulseVector',
    'VolumeDeltaHeatmap',
    'VolumeSurgeDetector',
    'ZScoreReversionModel',
    'adx_fast',
    'atr_fast',
    'bollinger_bands_fast',
    'calculate_all_indicators_parallel',
    'create_fmd_indicator',
    'create_vii_indicator',
    'ema_fast',
    'initialize_sentiment',
    'macd_fast',
    'rsi_fast',
    'sma_fast',
    'stochastic_fast',
]

class IndicatorsOrchestrator:
    """Auto-generated stub orchestrator for indicators."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.running = False
        self._initialized = True
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running, "initialized": self._initialized}

class IndicatorManager:
    """Stub implementation for IndicatorManager."""
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get('config', {})
        self.running = False
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running}


class IndicatorOrchestrator:
    """Stub for IndicatorOrchestrator."""
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get('config', {})
        self.running = False
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running}
