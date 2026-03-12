"""
evolution_layer package
"""

try:
    from .evolver import (
        CodeEvolver,
        EvolutionProposal,
        EvolutionResult,
        EvolutionStatus,
        EvolutionType
    )
    from .learner import (
        ContinuousLearner,
        LearningExperience,
        LearningResult,
        LearningType,
        retry
    )
    from .optimizer import OptimizationResult, OptimizationTarget, SelfOptimizer
    from .orchestrator import (
        EvolutionCycle,
        EvolutionCycleStatus,
        EvolutionOrchestrator,
        EvolutionStatus,
        get_evolution_orchestrator,
        record_trade_experience,
        start_evolution,
        stop_evolution
    )
    from .reward_model import (
        ImmutableRewardModel,
        RewardComponents,
        RewardConstraints,
        calculate_reward,
        get_constraints,
        get_reward_model,
        is_valid_action,
        verify_reward_model_integrity
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in evolution_layer: {e}')

__all__ = [
    'CodeEvolver',
    'ContinuousLearner',
    'EvolutionCycle',
    'EvolutionCycleStatus',
    'EvolutionOrchestrator',
    'EvolutionProposal',
    'EvolutionResult',
    'EvolutionStatus',
    'EvolutionType',
    'ImmutableRewardModel',
    'LearningExperience',
    'LearningResult',
    'LearningType',
    'OptimizationResult',
    'OptimizationTarget',
    'RewardComponents',
    'RewardConstraints',
    'SelfOptimizer',
    'calculate_reward',
    'get_constraints',
    'get_evolution_orchestrator',
    'get_reward_model',
    'is_valid_action',
    'record_trade_experience',
    'retry',
    'start_evolution',
    'stop_evolution',
    'verify_reward_model_integrity',
]