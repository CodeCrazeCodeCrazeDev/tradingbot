"""
training package
"""

try:
    from .adversarial_training import (
        AdversarialTrainingSystem,
        BlueTeamDefender,
        ManipulationScenario,
        ManipulationType,
        RedTeamAttacker,
        SelfPlayArena,
        ShadowModeObserver,
        TeamRole,
        TradingDuel,
        TrainingAgent
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in training: {e}')

__all__ = [
    'AdversarialTrainingSystem',
    'BlueTeamDefender',
    'ManipulationScenario',
    'ManipulationType',
    'RedTeamAttacker',
    'SelfPlayArena',
    'ShadowModeObserver',
    'TeamRole',
    'TradingDuel',
    'TrainingAgent',
]