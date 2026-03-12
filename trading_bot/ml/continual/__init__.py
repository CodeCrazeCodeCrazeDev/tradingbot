"""
continual package
"""

try:
    from .ewc_learning import ContinualLearningPipeline, EWC, create_regime_data
    from .ewc_trainer import EwcTrainer, create_ewc_trainer
    from .replay_buffer import ReplayBuffer, create_replay_buffer
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in continual: {e}')

__all__ = [
    'ContinualLearningPipeline',
    'EWC',
    'EwcTrainer',
    'ReplayBuffer',
    'create_ewc_trainer',
    'create_regime_data',
    'create_replay_buffer',
]