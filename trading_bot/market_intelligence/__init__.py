"""
Market Intelligence Module
============================================================

Auto-generated integration file.
"""

# data_monitoring
try:
    from .data_monitoring import (
        MarketDataMonitor,
        EconomicIndicatorMonitor,
        NewsAndSentimentMonitor,
    )
except ImportError as e:
    # data_monitoring not available
    MarketDataMonitor = None
    EconomicIndicatorMonitor = None
    NewsAndSentimentMonitor = None

# performance_optimization
try:
    from .performance_optimization import (
        CacheManager,
    )
except ImportError as e:
    # performance_optimization not available
    CacheManager = None

# wyckoff_analysis
try:
    from .wyckoff_analysis import (
        WyckoffAccumulationDetector,
        WyckoffDistributionAnalyzer,
        VolumeAnalysis,
    )
except ImportError as e:
    # wyckoff_analysis not available
    WyckoffAccumulationDetector = None
    WyckoffDistributionAnalyzer = None
    VolumeAnalysis = None

# liquidity_analysis
try:
    from .liquidity_analysis import (
        LiquidityPoolDetector,
    )
except ImportError as e:
    # liquidity_analysis not available
    LiquidityPoolDetector = None

# microstructure_analysis
try:
    from .microstructure_analysis import (
        OrderBlockAnalysis,
    )
except ImportError as e:
    # microstructure_analysis not available
    OrderBlockAnalysis = None

# event_detection
try:
    from .event_detection import (
        MarketEventDetector,
    )
except ImportError as e:
    # event_detection not available
    MarketEventDetector = None

# pattern_recognition
try:
    from .pattern_recognition import (
        PricePatternRecognition,
    )
except ImportError as e:
    # pattern_recognition not available
    PricePatternRecognition = None

__all__ = [
    'MarketDataMonitor',
    'EconomicIndicatorMonitor',
    'NewsAndSentimentMonitor',
    'CacheManager',
    'WyckoffAccumulationDetector',
    'WyckoffDistributionAnalyzer',
    'VolumeAnalysis',
    'LiquidityPoolDetector',
    'OrderBlockAnalysis',
    'MarketEventDetector',
    'PricePatternRecognition',
]
