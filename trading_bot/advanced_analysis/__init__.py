"""
Advanced Analysis Module
============================================================

Auto-generated integration file.
"""

# advanced_analysis_orchestrator
try:
    from .advanced_analysis_orchestrator import (
        AdvancedAnalysisOrchestrator,
    )
except ImportError as e:
    # advanced_analysis_orchestrator not available
    pass

# multi_agent_rl
try:
    from .multi_agent_rl import (
        MultiAgentTradingSystem,
    )
except ImportError as e:
    # multi_agent_rl not available
    pass

# options_hedging
try:
    from .options_hedging import (
        OptionsHedgingEngine,
    )
except ImportError as e:
    # options_hedging not available
    pass

__all__ = [
    'AdvancedAnalysisOrchestrator',
    'MultiAgentTradingSystem',
    'OptionsHedgingEngine',
]
