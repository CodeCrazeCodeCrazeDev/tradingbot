"""Mega Integration module. Forwarding calls to canonical cognition orchestrator."""

from trading_bot.cognition import AlphaAlgoCognitiveBrain

MegaSystemIntegrator = AlphaAlgoCognitiveBrain
get_mega_system = lambda: AlphaAlgoCognitiveBrain()

__all__ = ["MegaSystemIntegrator", "AlphaAlgoCognitiveBrain", "get_mega_system"]
