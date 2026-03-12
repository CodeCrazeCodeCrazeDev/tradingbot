"""
tests package
"""

try:
    from .run_tests import (
        TestEmotionalTracking,
        TestEndToEnd,
        TestEnhancedPerformanceAnalytics,
        TestExecutionAlgorithms,
        TestMLStrategyEngine,
        TestMainIntegration,
        create_test_suite,
        run_specific_test,
        run_tests
    )
    from .test_emotional_tracking import TestEmotionalTracking, TestEnhancedPerformanceAnalytics
    from .test_end_to_end import TestEndToEnd
    from .test_execution_algorithms import TestExecutionAlgorithms
    from .test_liquidity import test_equal_high_detection, test_liquidity_grab
    from .test_main_integration import TestMainIntegration
    from .test_market_structure import test_detect_swings, test_structure_events
    from .test_ml_components import TestPPOAgent, TestTransformerModel
    from .test_ml_ensemble import TestMLEnsemble
    from .test_ml_integration import TestMLIntegration
    from .test_ml_strategy import TestMLStrategyEngine
    from .test_risk import (
        test_market_regime_enum,
        test_position_size_dataclass,
        test_risk_assessment_dataclass,
        test_risk_limits_dataclass,
        test_risk_manager_initialization,
        test_risk_mode_enum,
        test_trade_direction_enum,
        test_trade_quality_enum,
        test_trading_stats_dataclass
    )
    from .test_survival_core import TestSurvivalCore, TestSurvivalCoreAsync
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in tests: {e}')

__all__ = [
    'TestEmotionalTracking',
    'TestEndToEnd',
    'TestEnhancedPerformanceAnalytics',
    'TestExecutionAlgorithms',
    'TestMLEnsemble',
    'TestMLIntegration',
    'TestMLStrategyEngine',
    'TestMainIntegration',
    'TestPPOAgent',
    'TestSurvivalCore',
    'TestSurvivalCoreAsync',
    'TestTransformerModel',
    'create_test_suite',
    'run_specific_test',
    'run_tests',
    'test_detect_swings',
    'test_equal_high_detection',
    'test_liquidity_grab',
    'test_market_regime_enum',
    'test_position_size_dataclass',
    'test_risk_assessment_dataclass',
    'test_risk_limits_dataclass',
    'test_risk_manager_initialization',
    'test_risk_mode_enum',
    'test_structure_events',
    'test_trade_direction_enum',
    'test_trade_quality_enum',
    'test_trading_stats_dataclass',
]