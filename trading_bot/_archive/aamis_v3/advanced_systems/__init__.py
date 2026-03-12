"""
advanced_systems package
"""

try:
    from .red_team_blue_team import (
        Attack,
        AttackType,
        BattleResult,
        BlueTeam,
        Defense,
        DefenseType,
        RedBlueTeamSystem,
        RedTeam,
        TeamType
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in advanced_systems: {e}')

__all__ = [
    'Attack',
    'AttackType',
    'BattleResult',
    'BlueTeam',
    'Defense',
    'DefenseType',
    'RedBlueTeamSystem',
    'RedTeam',
    'TeamType',
]