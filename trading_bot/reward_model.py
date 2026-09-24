"""Reward Model - flat-path shim for ``trading_bot.evolution_layer.reward_model``."""

try:
    from trading_bot.evolution_layer.reward_model import *  # noqa: F401,F403
    from trading_bot.evolution_layer.reward_model import get_reward_model  # noqa: F401
except ImportError:
    pass
