"""AlphaAlgo AI Cognition System Module."""

# Canonical tactical brain: the 9-stage orchestrator (perception -> state ->
# reasoning -> simulation -> adversarial verification -> decision -> risk gate).
# trading_bot.cognition.alpha_algo_cognitive_brain is a merge-added paper
# artifact (async process_market_update stub); it is NOT the canonical brain.
from trading_bot.cognition.orchestrator import AlphaAlgoCognitiveBrain

__all__ = ["AlphaAlgoCognitiveBrain"]
