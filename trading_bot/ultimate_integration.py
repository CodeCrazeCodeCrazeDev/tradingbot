"""Ultimate Integration module. Forwarding calls to canonical cognition orchestrator."""

from trading_bot.cognition import AlphaAlgoCognitiveBrain

UltimateSystemIntegrator = AlphaAlgoCognitiveBrain
get_ultimate_system = lambda: AlphaAlgoCognitiveBrain()

__all__ = ["UltimateSystemIntegrator", "AlphaAlgoCognitiveBrain", "get_ultimate_system"]
