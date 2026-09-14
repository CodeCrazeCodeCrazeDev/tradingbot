"""Unified AI Brain module. Forwarding calls to canonical cognition orchestrator."""

from trading_bot.cognition import AlphaAlgoCognitiveBrain

# Maintain backward compatibility for existing callers
UnifiedAIBrain = AlphaAlgoCognitiveBrain
get_unified_brain = lambda: AlphaAlgoCognitiveBrain()

__all__ = ["UnifiedAIBrain", "AlphaAlgoCognitiveBrain", "get_unified_brain"]
