"""
opportunity_scanner package
"""

try:
    from .arbitrage_detection import (
        ArbitrageOpportunity,
        ArbitrageType,
        CrossExchangeArbitrage,
        LatencyArbitrage,
        StatisticalArbitrage,
        TriangularArbitrage,
        retry
    )
    from .correlation_analysis import (
        CointegrationMonitor,
        CorrelationBreakdownDetector,
        CorrelationOpportunity,
        CorrelationType,
        PairsTradingEngine,
        SpreadAnalyzer,
        retry
    )
    from .flow_analysis import (
        DarkPoolMonitor,
        FlowOpportunity,
        FlowType,
        OrderFlowImbalanceDetector,
        VolumeProfileAnalyzer,
        WhaleTracker
    )
    from .market_inefficiency import (
        EfficiencyRatio,
        InefficiencyType,
        MarketInefficiencyScanner,
        MispricingDetector,
        PriceAnomaly
    )
    from .market_making import (
        LiquidityProvider,
        MakingOpportunity,
        MakingStrategy,
        MarketMakerStrategy,
        OrderBookImbalance,
        SpreadCapture
    )
    from .momentum_capture import (
        BreakoutScanner,
        MomentumBurstDetector,
        MomentumOpportunity,
        MomentumType,
        TrendAccelerationFinder,
        VelocityTracker
    )
    from .news_trading import (
        CatalystIdentifier,
        CatalystType,
        EventDrivenTrader,
        NewsImpact,
        NewsImpactAnalyzer,
        NewsOpportunity,
        SentimentSurgeDetector,
        retry
    )
    from .parallel_scanner import ParallelScanner
    from .scanner_interface import OpportunityData, UnifiedScanner
    from .volatility_trading import (
        GammaScalping,
        StrangleHarvester,
        VolatilityArbitrage,
        VolatilityOpportunity,
        VolatilitySkewTrader,
        VolatilityStrategy
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in opportunity_scanner: {e}')

__all__ = [
    'ArbitrageOpportunity',
    'ArbitrageType',
    'BreakoutScanner',
    'CatalystIdentifier',
    'CatalystType',
    'CointegrationMonitor',
    'CorrelationBreakdownDetector',
    'CorrelationOpportunity',
    'CorrelationType',
    'CrossExchangeArbitrage',
    'DarkPoolMonitor',
    'EfficiencyRatio',
    'EventDrivenTrader',
    'FlowOpportunity',
    'FlowType',
    'GammaScalping',
    'InefficiencyType',
    'LatencyArbitrage',
    'LiquidityProvider',
    'MakingOpportunity',
    'MakingStrategy',
    'MarketInefficiencyScanner',
    'MarketMakerStrategy',
    'MispricingDetector',
    'MomentumBurstDetector',
    'MomentumOpportunity',
    'MomentumType',
    'NewsImpact',
    'NewsImpactAnalyzer',
    'NewsOpportunity',
    'OpportunityData',
    'OrderBookImbalance',
    'OrderFlowImbalanceDetector',
    'PairsTradingEngine',
    'ParallelScanner',
    'PriceAnomaly',
    'SentimentSurgeDetector',
    'SpreadAnalyzer',
    'SpreadCapture',
    'StatisticalArbitrage',
    'StrangleHarvester',
    'TrendAccelerationFinder',
    'TriangularArbitrage',
    'UnifiedScanner',
    'VelocityTracker',
    'VolatilityArbitrage',
    'VolatilityOpportunity',
    'VolatilitySkewTrader',
    'VolatilityStrategy',
    'VolumeProfileAnalyzer',
    'WhaleTracker',
    'retry',
]