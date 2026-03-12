"""
Production Trading Infrastructure

This package contains production-grade components:
- Tick-level backtesting engine with realistic fill simulation
- Simple profitable strategies with statistical edge
- Real Interactive Brokers integration
- Data validation system with timestamp sync and anomaly detection
"""

import logging
_logger = logging.getLogger(__name__)

# Live trading system
try:
    from .live_trading_system import (
        LiveDataFeed,
        LiveTradingSystem,
        Order,
        OrderSide,
        OrderStatus,
        OrderType,
        PaperTradingEngine,
        PerformanceMetrics,
        PerformanceMonitor,
        Position,
        RiskManager,
        RiskParameters,
        TradingMode,
        run_demo,
        simple_momentum_strategy
    )
except ImportError as e:
    _logger.debug(f'Optional import failed in production: {e}')
# Tick-level backtester
    from .tick_level_backtester import (
        TickLevelBacktester,
        BacktestConfig,
        BacktestMetrics,
        SlippageModel,
        CommissionModel,
        FillSimulator,
        FillModel,
        Tick,
        OrderBook,
        Trade,
        create_backtester,
        validate_strategy
    )
except ImportError as e:
    _logger.debug(f'Tick-level backtester import failed: {e}')
# Profitable strategies
    from .profitable_strategies import (
        BaseStrategy,
        Signal,
        StrategyConfig,
        MeanReversionStrategy,
        MomentumBreakoutStrategy,
        VolatilityMeanReversionStrategy,
        PairsTradingStrategy,
        TrendFollowingStrategy,
        create_strategy,
        get_all_strategies,
        validate_strategy_edge
    )
except ImportError as e:
    _logger.debug(f'Profitable strategies import failed: {e}')
# Interactive Brokers integration
    from .interactive_brokers_live import (
        InteractiveBrokersClient,
        IBCredentials,
        OrderRecord,
        Fill,
        FillReconciler,
        DataValidator,
        ConnectionState,
        OrderState,
        create_ib_client,
        quick_connect
    )
except ImportError as e:
    _logger.debug(f'IB integration import failed: {e}')
# Data validation system
    from .data_validation_system import (
        DataValidationSystem,
        DataQuality,
        AnomalyType,
        Anomaly,
        ValidationResult,
        TickData,
        DataQualityMetrics,
        TimestampSynchronizer,
        SequenceValidator,
        PriceValidator,
        CrossVenueValidator,
        StalenessDetector,
        create_validation_system,
        validate_ohlcv_bar
    )
except ImportError as e:
    _logger.debug(f'Data validation import failed: {e}')

__all__ = [
    # Live trading
    'LiveDataFeed',
    'LiveTradingSystem',
    'Order',
    'OrderSide',
    'OrderStatus',
    'OrderType',
    'PaperTradingEngine',
    'PerformanceMetrics',
    'PerformanceMonitor',
    'Position',
    'RiskManager',
    'RiskParameters',
    'TradingMode',
    'run_demo',
    'simple_momentum_strategy',
    
    # Backtesting
    'TickLevelBacktester',
    'BacktestConfig',
    'BacktestMetrics',
    'SlippageModel',
    'CommissionModel',
    'FillSimulator',
    'FillModel',
    'Tick',
    'OrderBook',
    'Trade',
    'create_backtester',
    'validate_strategy',
    
    # Strategies
    'BaseStrategy',
    'Signal',
    'StrategyConfig',
    'MeanReversionStrategy',
    'MomentumBreakoutStrategy',
    'VolatilityMeanReversionStrategy',
    'PairsTradingStrategy',
    'TrendFollowingStrategy',
    'create_strategy',
    'get_all_strategies',
    'validate_strategy_edge',
    
    # IB Integration
    'InteractiveBrokersClient',
    'IBCredentials',
    'OrderRecord',
    'Fill',
    'FillReconciler',
    'DataValidator',
    'ConnectionState',
    'OrderState',
    'create_ib_client',
    'quick_connect',
    
    # Data Validation
    'DataValidationSystem',
    'DataQuality',
    'AnomalyType',
    'Anomaly',
    'ValidationResult',
    'TickData',
    'DataQualityMetrics',
    'TimestampSynchronizer',
    'SequenceValidator',
    'PriceValidator',
    'CrossVenueValidator',
    'StalenessDetector',
    'create_validation_system',
    'validate_ohlcv_bar',
]