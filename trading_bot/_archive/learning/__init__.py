"""
learning package
"""

try:
    from .internet_learning import (
        AdaptiveLearningAgent,
        InternetLearningSystem,
        LearnedKnowledge,
        SourceType,
        TrustedSource,
        VerificationStatus,
        main
    )
    from .ppo_trainer import ActorCritic, PPOTrainer, TradingEnvironment
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in learning: {e}')

__all__ = [
    'ActorCritic',
    'AdaptiveLearningAgent',
    'InternetLearningSystem',
    'LearnedKnowledge',
    'PPOTrainer',
    'SourceType',
    'TradingEnvironment',
    'TrustedSource',
    'VerificationStatus',
    'main',
]