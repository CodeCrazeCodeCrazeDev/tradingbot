"""
reward_engine package
"""

try:
    from .constraints import ConstraintChecker, ConstraintSeverity, ConstraintViolation
    from .immutable_rewards import ImmutableRewardModel, RewardComponents, get_reward_model
    from .metrics import (
        PerformanceMetrics,
        calculate_max_drawdown,
        calculate_profit_factor,
        calculate_sharpe_ratio,
        calculate_sortino_ratio
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in reward_engine: {e}')

__all__ = [
    'ConstraintChecker',
    'ConstraintSeverity',
    'ConstraintViolation',
    'ImmutableRewardModel',
    'PerformanceMetrics',
    'RewardComponents',
    'calculate_max_drawdown',
    'calculate_profit_factor',
    'calculate_sharpe_ratio',
    'calculate_sortino_ratio',
    'get_reward_model',
]